from database import get_db_connection, close_db_connection

current_user_role_id = None

def check_credentials(username, user_password):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute("SELECT * FROM Users WHERE username = %s AND password = %s;", (username, user_password))
            user = cursor.fetchone()
            global current_user_role_id
            if user:
                current_user_role_id = user[3]  # предположим, что role_id - это четвертый элемент
            return user is not None
    except Exception as ex:
        print("[ERROR] Error while checking credentials:", ex)
        return False
    finally:
        close_db_connection(con)

def get_current_user_role_id():
    return current_user_role_id
