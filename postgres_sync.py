import os
import psycopg2

from typing import Any
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"]
    )
class SyncNotConfiguredError(RuntimeError):
    pass


def test_connection():
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("SELECT current_database(), NOW()")

        row = cur.fetchone()

        return {
            "database": row[0],
            "server_time": str(row[1]),
        }

    finally:
        conn.close()

def _rows_to_dicts(cursor):
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _fetch_all(cursor, query, *params):
    cursor.execute(query, params)
    return _rows_to_dicts(cursor)


def _fetch_one(cursor, query, *params):
    cursor.execute(query, params)
    rows = _rows_to_dicts(cursor)
    return rows[0] if rows else None
def get_next_school_id():

    year = str(datetime.now().year)

    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT school_id
            FROM schools
            WHERE school_id LIKE %s
            """,
            (f"{year}%",)
        )

        rows = cur.fetchall()

        max_number = 0

        for row in rows:

            school_id = str(row[0])

            if school_id.startswith(year):

                try:
                    number = int(school_id[4:])
                    max_number = max(
                        max_number,
                        number
                    )

                except:
                    pass

        return year + str(
            max_number + 1
        ).zfill(4)

    finally:
        conn.close()
def sync_event(event):
    return {
        "entity": event.get("entity"),
        "action": event.get("action"),
        "status": "ok"
    }
def login_and_get_bundle(role: str, user_id: str, password: str) -> dict[str, Any] | None:
    role = role.lower().strip()
    if role not in {"admin", "teacher"}:
        raise ValueError("Role must be admin or teacher.")

    table = "admins" if role == "admin" else "teachers"
    id_column = "admin_id" if role == "admin" else "teacher_id"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        # _run_feature_subscription_migration(cursor)
        # _run_leave_workflow_migration(cursor)
        # conn.commit()

        # cursor.execute(
        #     f"""
        #     SELECT * FROM {table}
        #     WHERE {id_column} = %s AND password = %s AND is_active = %s
        #     """,
        #     (user_id, password, True)
        # )
        if role == "teacher":
         cursor.execute(
            """
            SELECT *
            FROM teachers
            WHERE teacher_id=%s
            AND password=%s
            AND is_active=true
            """,
            (user_id, password)
        )
        else:
         cursor.execute(
        """
        SELECT *
        FROM admins
        WHERE admin_id=%s
        AND password=%s
        """,
        (user_id, password)
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
             "school": ...,
             "admins": ...,
             "teachers": ...,
             "students": ...,
             "student_attendance": ...,
             "teacher_attendance": ...,
             "class_teacher_assignments": ...
        }
    finally:
        conn.close()
def get_school_bundle(school_id: str) -> dict[str, Any]:
    conn = get_connection()

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
            WHERE school_id = %s    
            """,
            school_id,
        ),
        "admins": _fetch_all(
            cursor,
            """
            SELECT admin_id, school_id, name, email, contact, address, role, password
            FROM admins
            WHERE school_id = %s   
            """,
            school_id,
        ),
        "teachers": _fetch_all(
            cursor,
            """
            SELECT teacher_id, school_id, name, email, contact, address, role,
                   subject, qualification, face_embedding, password
            FROM teachers
            WHERE school_id = %s
            """,
            school_id,
        ),
        "students": _fetch_all(
            cursor,
            """
            SELECT student_id, school_id, admission_no, admission_date,
                   first_name, middle_name, last_name, full_name,
                   father_name, mother_name, address, gender, dob,
                   "class", section, session, class_teacher,
                   photo_path, face_embedding, created_at
            FROM students
            WHERE school_id = %s    
            """,
            school_id,
        ),
        "attendance": _fetch_all(
            cursor,
            """
           SELECT *
                FROM student_attendance
                WHERE school_id=%s
                 """,
            school_id,
        ),
        "teacher_attendance": _fetch_all(
            cursor,
            """
            SELECT *
            FROM teacher_attendance
            WHERE school_id = %s
            """,
            school_id,
        ),
        "class_teacher_assignments": _fetch_all(
            cursor,
            """
            SELECT school_id, class_name, section, teacher_id, teacher_name
            FROM class_teacher_assignments
            WHERE school_id = %s
            """,
            school_id,
        ),
        "subjects": _fetch_all(
            cursor,
            """
            SELECT school_id, name
            FROM subjects
            WHERE school_id = %s
            """,
            school_id,
        ),
        "leave_types": _fetch_all(
            cursor,
            """
            SELECT school_id, name, code
            FROM leave_types
            WHERE school_id = %s
            """,
            school_id,
        ),
        "teacher_leave_allocations": _fetch_all(
            cursor,
            """
            SELECT school_id, teacher_id, leave_type_code, [year], total_days
            FROM teacher_leave_allocations
            WHERE school_id = %s
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
            WHERE school_id = %s    
            """,
            school_id,
        ),
        "school_subscriptions": _fetch_all(
            cursor,
            """
            SELECT school_id, start_date, end_date, status, updated_at
            FROM school_subscriptions
            WHERE school_id = %s    
            """,
            school_id,
        ),
        "school_feature_settings": _fetch_all(
            cursor,
            """
            SELECT school_id, audience, feature_code, CAST(enabled AS INT) AS enabled, updated_at
            FROM school_feature_settings
            WHERE school_id = %s
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
            WHERE school_id = %s
            """,
            school_id,
        ),
    }

