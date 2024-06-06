import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import psycopg2
from config import host, user as db_user, password as db_password, db_name

current_user_role_id = None

def check_credentials(username, user_password):
    con = None
    try:
        con = psycopg2.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=db_name
        )
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
        if con:
            con.close()
            print("[INFO] PostgreSQL connection closed")

def save_testcase(name, description, steps):
    con = None
    try:
        con = psycopg2.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        with con.cursor() as cursor:
            cursor.execute(
                "INSERT INTO TestCases (name, description) VALUES (%s, %s) RETURNING id_case;",
                (name, description)
            )
            test_case_id = cursor.fetchone()[0]

            for step_num, (step, result) in enumerate(steps, start=1):
                cursor.execute(
                    "INSERT INTO TestCaseSteps (StepNumber, ActionDescription, ExpectedResult, TestCaseID) "
                    "VALUES (%s, %s, %s, %s);",
                    (step_num, step, result, test_case_id)
                )

        con.commit()
        print("[INFO] Test case saved successfully!")
        refresh_testcases()  # Обновление списка тест-кейсов после сохранения

    except Exception as ex:
        print("[ERROR] Error while saving test case:", ex)
    finally:
        if con:
            con.close()
            print("[INFO] PostgreSQL connection closed")

def update_testcase(test_case_id, name, description, steps):
    con = None
    try:
        con = psycopg2.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        with con.cursor() as cursor:
            cursor.execute(
                "UPDATE TestCases SET name = %s, description = %s WHERE id_case = %s;",
                (name, description, test_case_id)
            )
            cursor.execute(
                "DELETE FROM TestCaseSteps WHERE TestCaseID = %s;",
                (test_case_id,)
            )
            for step_num, (step, result) in enumerate(steps, start=1):
                cursor.execute(
                    "INSERT INTO TestCaseSteps (StepNumber, ActionDescription, ExpectedResult, TestCaseID) "
                    "VALUES (%s, %s, %s, %s);",
                    (step_num, step, result, test_case_id)
                )

        con.commit()
        print("[INFO] Test case updated successfully!")
        refresh_testcases()  # Обновление списка тест-кейсов после обновления

    except Exception as ex:
        print("[ERROR] Error while updating test case:", ex)
    finally:
        if con:
            con.close()
            print("[INFO] PostgreSQL connection closed")

def delete_testcase(test_case_id):
    con = None
    try:
        con = psycopg2.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        with con.cursor() as cursor:
            cursor.execute(
                "DELETE FROM TestCaseSteps WHERE TestCaseID = %s;",
                (test_case_id,)
            )
            cursor.execute(
                "DELETE FROM TestCases WHERE id_case = %s;",
                (test_case_id,)
            )

        con.commit()
        print("[INFO] Test case deleted successfully!")
        refresh_testcases()  # Обновление списка тест-кейсов после удаления

    except Exception as ex:
        print("[ERROR] Error while deleting test case:", ex)
    finally:
        if con:
            con.close()
            print("[INFO] PostgreSQL connection closed")


def create_testcase_window(test_case_id=None):
    def save_testcase_to_db():
        name = name_entry.get()
        description = description_entry.get()
        steps = [(step_entry.get(), result_entry.get()) for step_entry, result_entry in steps_widgets]

        if test_case_id:
            update_testcase(test_case_id, name, description, steps)
        else:
            save_testcase(name, description, steps)
        testcase_window.destroy()

    def add_step(step_num):
        step_label = tk.Label(steps_frame, text=f"Шаг {step_num}:")
        step_label.grid(row=step_num, column=0, sticky="w")
        step_entry = tk.Entry(steps_frame, width=50)
        step_entry.grid(row=step_num, column=1, padx=5, pady=5, sticky="we")
        result_label = tk.Label(steps_frame, text="Ожидаемый результат:")
        result_label.grid(row=step_num, column=2, sticky="w")
        result_entry = tk.Entry(steps_frame, width=50)
        result_entry.grid(row=step_num, column=3, padx=5, pady=5, sticky="we")

        steps_widgets.append((step_entry, result_entry))
        num_steps[0] += 1

    testcase_window = tk.Toplevel(root)
    testcase_window.title("Создание тесткейса")

    tk.Label(testcase_window, text="Название:").grid(row=0, column=0, sticky="w")
    name_entry = tk.Entry(testcase_window)
    name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")

    tk.Label(testcase_window, text="Описание:").grid(row=1, column=0, sticky="w")
    description_entry = tk.Entry(testcase_window)
    description_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")

    steps_frame = tk.Frame(testcase_window)
    steps_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

    add_step_button = tk.Button(testcase_window, text="Добавить шаг", command=lambda: add_step(num_steps[0] + 1))
    add_step_button.grid(row=3, column=0, columnspan=2, pady=10)

    steps_widgets = []
    num_steps = [0]

    save_button = tk.Button(testcase_window, text="Сохранить", command=save_testcase_to_db)
    save_button.grid(row=4, column=0, columnspan=2, pady=10)

    testcase_window.columnconfigure(1, weight=1)
    steps_frame.columnconfigure(1, weight=1)
    steps_frame.columnconfigure(3, weight=1)
    steps_frame.rowconfigure(num_steps[0] + 1, weight=1)

    description_entry.config(width=50)

    # Если редактируем существующий тест-кейс, заполняем поля текущими значениями
    if test_case_id:
        con = psycopg2.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT name, description FROM TestCases WHERE id_case = %s;", (test_case_id,)
            )
            name, description = cursor.fetchone()
            name_entry.insert(0, name)
            description_entry.insert(0, description)

            cursor.execute(
                "SELECT StepNumber, ActionDescription, ExpectedResult FROM TestCaseSteps WHERE TestCaseID = %s ORDER BY StepNumber;",
                (test_case_id,)
            )
            steps = cursor.fetchall()
            for step_num, (step, result) in enumerate(steps, start=1):
                add_step(step_num)
                steps_widgets[step_num - 1][0].insert(0, step)
                steps_widgets[step_num - 1][1].insert(0, result)

        con.close()

def load_testcases():
    try:
        con = psycopg2.connect(
            host=host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        with con.cursor() as cursor:
            cursor.execute("SELECT id_case, name, description FROM TestCases;")
            testcases = cursor.fetchall()
            return testcases
    except Exception as ex:
        print("[ERROR] Error while loading test cases:", ex)
        return []
    finally:
        if con:
            con.close()
            print("[INFO] PostgreSQL connection closed")

def refresh_testcases():
    for widget in tab2_frame.winfo_children():
        widget.destroy()

    testcases = load_testcases()
    for idx, (test_case_id, name, description) in enumerate(testcases):
        tk.Label(tab2_frame, text=f"{name}").grid(row=idx, column=0, sticky="w")
        tk.Button(tab2_frame, text="Редактировать", command=lambda tcid=test_case_id: create_testcase_window(tcid)).grid(row=idx, column=1, sticky="w")
        tk.Button(tab2_frame, text="Удалить", command=lambda tcid=test_case_id: delete_testcase(tcid)).grid(row=idx, column=2, sticky="w")

def create_error_message(message):
    error_window = tk.Toplevel()
    error_window.title("Ошибка")
    error_window.geometry("300x100")
    error_window.resizable(False, False)

    label = tk.Label(error_window, text=message, wraplength=250)
    label.pack(pady=10, padx=10)

def create_user_management_tab(tab_control):
    def load_users():
        try:
            con = psycopg2.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=db_name
            )
            with con.cursor() as cursor:
                cursor.execute("SELECT id_users, username, password, role_id FROM Users;")
                users = cursor.fetchall()
                return users
        except Exception as ex:
            print("[ERROR] Error while loading users:", ex)
            return []
        finally:
            if con:
                con.close()
                print("[INFO] PostgreSQL connection closed")

    def refresh_user_list():
        for row in user_tree.get_children():
            user_tree.delete(row)
        users = load_users()
        for user in users:
            user_tree.insert("", "end", values=user)

    def add_user():
        def save_new_user():
            username = username_entry.get()
            password = password_entry.get()
            role_id = int(role_id_entry.get())
            try:
                con = psycopg2.connect(
                    host=host,
                    user=db_user,
                    password=db_password,
                    database=db_name
                )
                with con.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO Users (username, password, role_id) VALUES (%s, %s, %s);",
                        (username, password, role_id)
                    )
                con.commit()
                refresh_user_list()
                add_user_window.destroy()
                print("[INFO] New user added successfully!")
            except Exception as ex:
                print("[ERROR] Error while adding new user:", ex)
            finally:
                if con:
                    con.close()
                    print("[INFO] PostgreSQL connection closed")

        add_user_window = tk.Toplevel(root)
        add_user_window.title("Добавить пользователя")
        add_user_window.geometry("300x200")

        tk.Label(add_user_window, text="Имя пользователя:").pack(pady=5)
        username_entry = tk.Entry(add_user_window)
        username_entry.pack(pady=5)

        tk.Label(add_user_window, text="Пароль:").pack(pady=5)
        password_entry = tk.Entry(add_user_window)
        password_entry.pack(pady=5)

        tk.Label(add_user_window, text="Роль (ID):").pack(pady=5)
        role_id_entry = tk.Entry(add_user_window)
        role_id_entry.pack(pady=5)

        save_button = tk.Button(add_user_window, text="Сохранить", command=save_new_user)
        save_button.pack(pady=10)

    def edit_user_password():
        selected_item = user_tree.selection()
        if not selected_item:
            return

        user_id = user_tree.item(selected_item)["values"][0]

        def save_new_password():
            new_password = new_password_entry.get()
            try:
                con = psycopg2.connect(
                    host=host,
                    user=db_user,
                    password=db_password,
                    database=db_name
                )
                with con.cursor() as cursor:
                    cursor.execute(
                        "UPDATE Users SET password = %s WHERE id_users = %s;",
                        (new_password, user_id)
                    )
                con.commit()
                refresh_user_list()
                edit_password_window.destroy()
                print("[INFO] Password updated successfully!")
            except Exception as ex:
                print("[ERROR] Error while updating password:", ex)
            finally:
                if con:
                    con.close()
                    print("[INFO] PostgreSQL connection closed")

        edit_password_window = tk.Toplevel(root)
        edit_password_window.title("Изменить пароль")
        edit_password_window.geometry("300x150")

        tk.Label(edit_password_window, text="Новый пароль:").pack(pady=5)
        new_password_entry = tk.Entry(edit_password_window)
        new_password_entry.pack(pady=5)

        save_button = tk.Button(edit_password_window, text="Сохранить", command=save_new_password)
        save_button.pack(pady=10)

    if current_user_role_id != 1:
        return

    user_management_tab = ttk.Frame(tab_control)
    tab_control.add(user_management_tab, text="Управление пользователями")

    user_tree = ttk.Treeview(user_management_tab, columns=("id", "username", "password", "role"), show="headings")
    user_tree.heading("id", text="ID")
    user_tree.heading("username", text="Имя пользователя")
    user_tree.heading("password", text="Пароль")
    user_tree.heading("role", text="Роль")
    user_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    refresh_button = tk.Button(user_management_tab, text="Обновить", command=refresh_user_list)
    refresh_button.pack(side=tk.LEFT, padx=10, pady=10)

    add_user_button = tk.Button(user_management_tab, text="Добавить пользователя", command=add_user)
    add_user_button.pack(side=tk.LEFT, padx=10, pady=10)

    edit_password_button = tk.Button(user_management_tab, text="Изменить пароль", command=edit_user_password)
    edit_password_button.pack(side=tk.LEFT, padx=10, pady=10)

    refresh_user_list()

def login():
    def try_login():
        username = username_entry.get()
        user_password = password_entry.get()
        if check_credentials(username, user_password):
            login_window.destroy()
            main()
        else:
            create_error_message("Неправильное имя пользователя или пароль")

    login_window = tk.Tk()
    login_window.title("Вход в систему")
    login_window.geometry("300x150")

    tk.Label(login_window, text="Имя пользователя:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Пароль:").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    login_button = tk.Button(login_window, text="Войти", command=try_login)
    login_button.pack(pady=5)

    login_window.mainloop()

def main():
    global root
    global tab2_frame
    root = tk.Tk()
    root.geometry("800x700")
    root.title("RED DWARF")

    tab_control = ttk.Notebook(root)

    tab1 = ttk.Frame(tab_control)
    tab_control.add(tab1, text="Главная")

    image = Image.open("img/dwarf.png")
    photo = ImageTk.PhotoImage(image)
    label1 = tk.Label(tab1, image=photo)
    label1.image = photo
    label1.pack(pady=10, padx=10)

    tab2 = ttk.Frame(tab_control)
    tab_control.add(tab2, text="База")

    frame_btn = tk.Frame(tab2)
    frame_btn.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=10)

    button_create = tk.Button(frame_btn, text="Создать тест-кейс", command=create_testcase_window)
    button_create.pack(pady=5, padx=5)

    tab2_frame = tk.Frame(tab2)
    tab2_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    refresh_testcases()

    create_user_management_tab(tab_control)

    tab_control.pack(expand=1, fill="both")
    root.mainloop()

if __name__ == "__main__":
    login()
