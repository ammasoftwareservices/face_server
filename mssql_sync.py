import json
import os
import re
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import pyodbc
except ImportError:
    pyodbc = None


class SyncNotConfiguredError(RuntimeError):
    pass


ENTITY_CONFIG = {
    "super_admin": {
        "table": "super_admins",
        "keys": ["super_admin_id"],
        "columns": [
            "super_admin_id",
            "name",
            "email",
            "contact",
            "password",
            "role",
            "is_active",
            "created_at",
        ],
    },
    "school": {
        "table": "schools",
        "keys": ["school_id"],
        "columns": [
            "school_id",
            "name",
            "address",
            "contact",
            "latitude",
            "longitude",
            "logo_path",
        ],
    },
    "admin": {
        "table": "admins",
        "keys": ["admin_id"],
        "columns": [
            "admin_id",
            "school_id",
            "name",
            "email",
            "contact",
            "address",
            "role",
            "password",
        ],
    },
    "school_subscription": {
        "table": "school_subscriptions",
        "keys": ["school_id"],
        "columns": [
            "school_id",
            "start_date",
            "end_date",
            "status",
            "updated_at",
        ],
    },
    "school_feature_setting": {
        "table": "school_feature_settings",
        "keys": ["school_id", "audience", "feature_code"],
        "columns": [
            "school_id",
            "audience",
            "feature_code",
            "enabled",
            "updated_at",
        ],
    },
    "teacher": {
        "table": "teachers",
        "keys": ["teacher_id"],
        "columns": [
            "teacher_id",
            "school_id",
            "name",
            "email",
            "contact",
            "address",
            "role",
            "subject",
            "qualification",
            "face_embedding",
            "password",
        ],
    },
    "student": {
        "table": "students",
        "keys": ["student_id"],
        "columns": [
            "student_id",
            "school_id",
            "admission_no",
            "admission_date",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "father_name",
            "mother_name",
            "address",
            "gender",
            "dob",
            "class",
            "section",
            "session",
            "class_teacher",
            "photo_path",
            "face_embedding",
            "created_at",
        ],
    },
    "subject": {
        "table": "subjects",
        "keys": ["school_id", "name"],
        "columns": ["school_id", "name"],
    },
    "class_teacher_assignment": {
        "table": "class_teacher_assignments",
        "keys": ["school_id", "class_name", "section"],
        "columns": [
            "school_id",
            "class_name",
            "section",
            "teacher_id",
            "teacher_name",
        ],
    },
    "student_attendance": {
        "table": "student_attendance",
        "keys": ["student_id", "school_id", "date"],
        "columns": ["student_id", "school_id", "date", "status", "timestamp"],
    },
    "teacher_attendance": {
        "table": "teacher_attendance",
        "keys": ["teacher_id", "school_id", "date"],
        "columns": ["teacher_id", "school_id", "date", "status", "timestamp"],
    },
    "teacher_leave_allocation": {
        "table": "teacher_leave_allocations",
        "keys": ["school_id", "teacher_id", "leave_type_code", "year"],
        "columns": [
            "school_id",
            "teacher_id",
            "leave_type_code",
            "year",
            "total_days",
        ],
    },
    "teacher_leave_application": {
        "table": "teacher_leave_applications",
        "keys": ["leave_id"],
        "columns": [
            "leave_id",
            "school_id",
            "teacher_id",
            "leave_type_code",
            "from_date",
            "to_date",
            "days",
            "reason",
            "status",
            "admin_remarks",
            "cancel_reason",
            "decided_by",
            "decided_at",
            "updated_at",
            "created_at",
        ],
    },
    "notification": {
        "table": "notifications",
        "keys": ["notification_id"],
        "columns": [
            "notification_id",
            "school_id",
            "recipient_role",
            "recipient_id",
            "title",
            "message",
            "type",
            "reference_id",
            "is_read",
            "created_at",
        ],
    },
}


def sync_event_to_mssql(event: dict[str, Any]) -> dict[str, Any]:
    entity = str(event.get("entity") or "")
    action = str(event.get("action") or "upsert")
    payload = event.get("payload") or {}

    if entity not in ENTITY_CONFIG:
        raise ValueError(f"Unsupported sync entity: {entity}")
    if not isinstance(payload, dict):
        raise ValueError("Sync payload must be an object.")

    config = ENTITY_CONFIG[entity]
    conn = _connect()
    try:
        cursor = conn.cursor()
        _run_feature_subscription_migration(cursor)
        _run_leave_workflow_migration(cursor)
        _insert_sync_event(cursor, event)
        if action == "delete":
            _delete(cursor, config, payload)
        else:
            _upsert(cursor, config, payload)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    _sync_to_school_database(entity, action, config, payload)

    return {"entity": entity, "action": action}


def _sync_to_school_database(
    entity: str,
    action: str,
    config: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    if entity == "super_admin":
        return

    school_id = payload.get("school_id")
    if not school_id:
        return

    school_id = str(school_id)
    _ensure_school_database(school_id)

    conn = _connect(database_override=school_id)
    try:
        cursor = conn.cursor()
        if action == "delete":
            _delete(cursor, config, payload)
        else:
            _upsert(cursor, config, payload)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_school_database(school_id: str) -> None:
    _validate_database_name(school_id)

    master = _connect(database_override="master", autocommit=True)
    try:
        cursor = master.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sys.databases WHERE name = ?",
            school_id,
        )
        exists = int(cursor.fetchone()[0]) > 0
        if not exists:
            cursor.execute(f"CREATE DATABASE [{school_id}]")
    finally:
        master.close()

    school_conn = _connect(database_override=school_id)
    try:
        cursor = school_conn.cursor()
        cursor.execute("SELECT OBJECT_ID('schools', 'U')")
        has_schema = cursor.fetchone()[0] is not None
        if not has_schema:
            _run_schema(cursor)
        _run_feature_subscription_migration(cursor)
        _run_leave_workflow_migration(cursor)
        school_conn.commit()
    except Exception:
        school_conn.rollback()
        raise
    finally:
        school_conn.close()


def _run_schema(cursor) -> None:
    schema_path = Path(__file__).with_name("mssql_schema.sql")
    schema_sql = schema_path.read_text(encoding="utf-8")
    for statement in _split_sql_batches(schema_sql):
        cursor.execute(statement)


def _run_feature_subscription_migration(cursor) -> None:
    migration_path = Path(__file__).with_name("mssql_feature_subscription_update.sql")
    if not migration_path.exists():
        return
    migration_sql = migration_path.read_text(encoding="utf-8")
    for statement in _split_sql_batches(migration_sql):
        cursor.execute(statement)


def _run_leave_workflow_migration(cursor) -> None:
    migration_path = Path(__file__).with_name("mssql_leave_workflow_update.sql")
    if not migration_path.exists():
        return
    migration_sql = migration_path.read_text(encoding="utf-8")
    for statement in _split_sql_batches(migration_sql):
        cursor.execute(statement)


def _split_sql_batches(sql: str) -> list[str]:
    batches: list[str] = []
    current: list[str] = []
    for line in sql.splitlines():
        if line.strip().upper() == "GO":
            batch = "\n".join(current).strip()
            if batch:
                batches.append(batch)
            current = []
        else:
            current.append(line)
    batch = "\n".join(current).strip()
    if batch:
        batches.append(batch)
    return batches


def _validate_database_name(database_name: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise ValueError(
            "School ID can only contain letters, numbers and underscore for database creation."
        )


def _connect(database_override: str | None = None, autocommit: bool = False):
    if pyodbc is None:
        raise SyncNotConfiguredError(
            "pyodbc is not installed. Run: python -m pip install -r requirements.txt"
        )

    connection_string = os.getenv("MSSQL_CONNECTION_STRING")
    if not connection_string:
        server = os.getenv("MSSQL_SERVER")
        database = database_override or os.getenv("MSSQL_DATABASE")
        username = os.getenv("MSSQL_USER")
        password = os.getenv("MSSQL_PASSWORD")
        driver = os.getenv("MSSQL_DRIVER") or _best_sql_driver()
        if not all([server, database, username, password]):
            raise SyncNotConfiguredError(
                "MSSQL is not configured. Set MSSQL_CONNECTION_STRING or "
                "MSSQL_SERVER, MSSQL_DATABASE, MSSQL_USER and MSSQL_PASSWORD."
            )
        connection_string = (
            f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
            f"UID={username};PWD={password};Encrypt=no;TrustServerCertificate=yes;"
        )
    elif database_override:
        connection_string = f"{connection_string};DATABASE={database_override};"
    return pyodbc.connect(connection_string, timeout=10, autocommit=autocommit)


def test_connection() -> dict[str, Any]:
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DB_NAME() AS database_name, @@SERVERNAME AS server_name")
        row = cursor.fetchone()
        return {
            "database": row.database_name,
            "server": row.server_name,
            "driver": os.getenv("MSSQL_DRIVER") or _best_sql_driver(),
        }
    finally:
        conn.close()


def get_next_school_id() -> str:
    year = str(__import__("datetime").datetime.now().year)
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT school_id FROM schools
            WHERE school_id LIKE ?
            """,
            f"{year}%",
        )
        max_number = 0
        for row in cursor.fetchall():
            school_id = str(row.school_id or "")
            if not school_id.startswith(year) or len(school_id) <= 4:
                continue
            try:
                number = int(school_id[4:])
            except ValueError:
                number = 0
            max_number = max(max_number, number)
        return year + str(max_number + 1).zfill(4)
    finally:
        conn.close()


def login_and_get_bundle(role: str, user_id: str, password: str) -> dict[str, Any] | None:
    role = role.lower().strip()
    if role not in {"admin", "teacher"}:
        raise ValueError("Role must be admin or teacher.")

    table = "admins" if role == "admin" else "teachers"
    id_column = "admin_id" if role == "admin" else "teacher_id"

    conn = _connect()
    try:
        cursor = conn.cursor()
        _run_feature_subscription_migration(cursor)
        _run_leave_workflow_migration(cursor)
        conn.commit()

        cursor.execute(
            f"""
            SELECT * FROM {table}
            WHERE {id_column} = ? AND password = ?
            """,
            user_id,
            password,
        )
        rows = _rows_to_dicts(cursor)
        if not rows:
            return None

        user = rows[0]
        school_id = str(user.get("school_id") or "")
        if not school_id:
            raise ValueError("User has no school_id.")

        bundle = _get_school_bundle(cursor, school_id)
        return {
            "role": role,
            "user": user,
            "school_id": school_id,
            "bundle": bundle,
        }
    finally:
        conn.close()

def get_school_bundle(school_id: str) -> dict[str, Any]:
    conn = _connect()

    try:
        cursor = conn.cursor()

        return _get_school_bundle(
            cursor,
            school_id,
        )

    finally:
        conn.close()
        
def _get_school_bundle(cursor, school_id: str) -> dict[str, Any]:
    return {
        "school": _fetch_one(
            cursor,
            """
            SELECT school_id, name, address, contact, latitude, longitude, logo_path
            FROM schools
            WHERE school_id = ?
            """,
            school_id,
        ),
        "admins": _fetch_all(
            cursor,
            """
            SELECT admin_id, school_id, name, email, contact, address, role, password
            FROM admins
            WHERE school_id = ?
            """,
            school_id,
        ),
        "teachers": _fetch_all(
            cursor,
            """
            SELECT teacher_id, school_id, name, email, contact, address, role,
                   subject, qualification, face_embedding, password
            FROM teachers
            WHERE school_id = ?
            """,
            school_id,
        ),
        "students": _fetch_all(
            cursor,
            """
            SELECT student_id, school_id, admission_no, admission_date,
                   first_name, middle_name, last_name, full_name,
                   father_name, mother_name, address, gender, dob,
                   [class] AS [class], section, session, class_teacher,
                   photo_path, face_embedding, created_at
            FROM students
            WHERE school_id = ?
            """,
            school_id,
        ),
        "attendance": _fetch_all(
            cursor,
            """
            SELECT student_id, school_id, [date], status, [timestamp]
            FROM student_attendance
            WHERE school_id = ?
            """,
            school_id,
        ),
        "teacher_attendance": _fetch_all(
            cursor,
            """
            SELECT teacher_id, school_id, [date], status, [timestamp]
            FROM teacher_attendance
            WHERE school_id = ?
            """,
            school_id,
        ),
        "class_teacher_assignments": _fetch_all(
            cursor,
            """
            SELECT school_id, class_name, section, teacher_id, teacher_name
            FROM class_teacher_assignments
            WHERE school_id = ?
            """,
            school_id,
        ),
        "subjects": _fetch_all(
            cursor,
            """
            SELECT school_id, name
            FROM subjects
            WHERE school_id = ?
            """,
            school_id,
        ),
        "leave_types": _fetch_all(
            cursor,
            """
            SELECT school_id, name, code
            FROM leave_types
            WHERE school_id = ?
            """,
            school_id,
        ),
        "teacher_leave_allocations": _fetch_all(
            cursor,
            """
            SELECT school_id, teacher_id, leave_type_code, [year], total_days
            FROM teacher_leave_allocations
            WHERE school_id = ?
            """,
            school_id,
        ),
        "teacher_leave_applications": _fetch_all(
            cursor,
            """
            SELECT leave_id, school_id, teacher_id, leave_type_code,
                   from_date, to_date, days, reason, status,
                   admin_remarks, cancel_reason, decided_by, decided_at,
                   updated_at, created_at
            FROM teacher_leave_applications
            WHERE school_id = ?
            """,
            school_id,
        ),
        "school_subscriptions": _fetch_all(
            cursor,
            """
            SELECT school_id, start_date, end_date, status, updated_at
            FROM school_subscriptions
            WHERE school_id = ?
            """,
            school_id,
        ),
        "school_feature_settings": _fetch_all(
            cursor,
            """
            SELECT school_id, audience, feature_code, CAST(enabled AS INT) AS enabled, updated_at
            FROM school_feature_settings
            WHERE school_id = ?
            """,
            school_id,
        ),
        "notifications": _fetch_all(
            cursor,
            """
            SELECT notification_id, school_id, recipient_role, recipient_id,
                   title, message, [type], reference_id,
                   CAST(is_read AS INT) AS is_read, created_at
            FROM notifications
            WHERE school_id = ?
            """,
            school_id,
        ),
    }


def _fetch_one(cursor, sql: str, *params) -> dict[str, Any] | None:
    rows = _fetch_all(cursor, sql, *params)
    return rows[0] if rows else None


def _fetch_all(cursor, sql: str, *params) -> list[dict[str, Any]]:
    cursor.execute(sql, *params)
    return _rows_to_dicts(cursor)


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    rows = []
    for row in cursor.fetchall():
        rows.append(
            {
                column: _json_safe_value(value)
                for column, value in zip(columns, row)
            }
        )
    return rows


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _best_sql_driver() -> str:
    drivers = list(pyodbc.drivers())
    preferred = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server",
    ]
    for driver in preferred:
        if driver in drivers:
            return driver
    raise SyncNotConfiguredError(
        "No SQL Server ODBC driver found. Install ODBC Driver 17/18 for SQL Server."
    )


def _insert_sync_event(cursor, event: dict[str, Any]) -> None:
    cursor.execute(
        """
        INSERT INTO sync_events(entity, action, payload_json, created_at)
        VALUES (?, ?, ?, SYSUTCDATETIME())
        """,
        str(event.get("entity") or ""),
        str(event.get("action") or ""),
        json.dumps(event.get("payload") or {}, ensure_ascii=False),
    )


def _upsert(cursor, config: dict[str, Any], payload: dict[str, Any]) -> None:
    table = config["table"]
    keys = config["keys"]
    columns = [column for column in config["columns"] if column in payload]
    if not all(key in payload for key in keys):
        raise ValueError(f"Missing key column for {table}: {keys}")
    if not columns:
        raise ValueError(f"No sync columns supplied for {table}")

    source_select = ", ".join([f"? AS [{column}]" for column in columns])
    match_clause = " AND ".join([f"target.[{key}] = source.[{key}]" for key in keys])
    update_columns = [column for column in columns if column not in keys]
    update_clause = ", ".join(
        [f"target.[{column}] = source.[{column}]" for column in update_columns]
    )
    insert_columns = ", ".join([f"[{column}]" for column in columns])
    insert_values = ", ".join([f"source.[{column}]" for column in columns])

    sql = f"""
    MERGE {table} AS target
    USING (SELECT {source_select}) AS source
      ON {match_clause}
    """
    if update_clause:
        sql += f" WHEN MATCHED THEN UPDATE SET {update_clause}"
    sql += f"""
    WHEN NOT MATCHED THEN INSERT ({insert_columns}) VALUES ({insert_values});
    """

    cursor.execute(
        sql,
        *[_coerce(payload.get(column), column) for column in columns],
    )


def _delete(cursor, config: dict[str, Any], payload: dict[str, Any]) -> None:
    table = config["table"]
    if table == "schools" and payload.get("school_id"):
        _delete_school_tree(cursor, str(payload["school_id"]))
        return

    keys = [key for key in config["keys"] if key in payload]
    if not keys:
        raise ValueError(f"No delete key supplied for {table}")
    where_clause = " AND ".join([f"[{key}] = ?" for key in keys])
    cursor.execute(
        f"DELETE FROM {table} WHERE {where_clause}",
        *[_coerce(payload.get(key), key) for key in keys],
    )


def _delete_school_tree(cursor, school_id: str) -> None:
    child_tables = [
        "notifications",
        "teacher_leave_applications",
        "teacher_leave_allocations",
        "leave_types",
        "student_attendance",
        "teacher_attendance",
        "class_teacher_assignments",
        "subjects",
        "class_master",
        "section_master",
        "students",
        "teachers",
        "admins",
        "school_feature_settings",
        "school_subscriptions",
        "holidays",
    ]
    for table in child_tables:
        cursor.execute(
            f"IF OBJECT_ID('{table}', 'U') IS NOT NULL DELETE FROM {table} WHERE school_id = ?",
            school_id,
        )
    cursor.execute(
        "IF OBJECT_ID('schools', 'U') IS NOT NULL DELETE FROM schools WHERE school_id = ?",
        school_id,
    )


DATE_COLUMNS = {
    "date",
    "admission_date",
    "dob",
    "from_date",
    "to_date",
    "start_date",
    "end_date",
    "holiday_date",
}

DATETIME_COLUMNS = {
    "timestamp",
    "created_at",
    "updated_at",
    "assigned_at",
    "decided_at",
}


def _coerce(value: Any, column: str | None = None) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if column in DATE_COLUMNS:
        return _parse_sql_date(value)
    if column in DATETIME_COLUMNS:
        return _parse_sql_datetime(value)
    return value


def _parse_sql_date(value: Any) -> Any:
    parsed = _parse_datetime_like(value)
    if isinstance(parsed, datetime):
        return parsed.date()
    return parsed


def _parse_sql_datetime(value: Any) -> Any:
    parsed = _parse_datetime_like(value)
    if isinstance(parsed, date) and not isinstance(parsed, datetime):
        return datetime(parsed.year, parsed.month, parsed.day)
    return parsed


def _parse_datetime_like(value: Any) -> Any:
    if value is None or isinstance(value, (date, datetime)):
        return value
    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")

    if "T" in text or ":" in text:
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return value
