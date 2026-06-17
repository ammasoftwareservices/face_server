import os
import psycopg2

def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

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

  from datetime import datetime

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
