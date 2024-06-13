import psycopg2
from config import host, user as db_user, password as db_password, db_name

def get_db_connection():
    return psycopg2.connect(
        host=host,
        user=db_user,
        password=db_password,
        database=db_name
    )

def close_db_connection(con):
    if con:
        con.close()
        print("[INFO] PostgreSQL connection closed")
