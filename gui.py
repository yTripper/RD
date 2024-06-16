import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from testcase_management import save_testcase, update_testcase, delete_testcase, view_testcase, edit_testcase, load_testcases, create_testcase_window, create_testsuite_window, refresh_testsuites, load_testsuites, delete_testsuite
from user_management import check_credentials, current_user_role_id, get_current_user_role_id
import psycopg2
from config import host, user as db_user, password as db_password, db_name
from database import get_db_connection, close_db_connection

def create_error_message(message):
    error_window = tk.Toplevel()
    error_window.title("Ошибка")
    error_window.geometry("300x100")
    error_window.resizable(False, False)

    label = tk.Label(error_window, text=message, wraplength=250)
    label.pack(pady=10, padx=10)

def create_user_management_tab(root, tab_control):
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
        add_user_window.geometry("500x300")

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

    def delete_user():
        selected_item = user_tree.selection()
        if not selected_item:
            return

        user_id = user_tree.item(selected_item)["values"][0]

        try:
            con = psycopg2.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=db_name
            )
            with con.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM Users WHERE id_users = %s;",
                    (user_id,)
                )
            con.commit()
            refresh_user_list()
            print("[INFO] User deleted successfully!")
        except Exception as ex:
            print("[ERROR] Error while deleting user:", ex)
        finally:
            if con:
                con.close()
                print("[INFO] PostgreSQL connection closed")

    if get_current_user_role_id() != 1:
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

    delete_user_button = tk.Button(user_management_tab, text="Удалить пользователя", command=delete_user)
    delete_user_button.pack(side=tk.LEFT, padx=10, pady=10)

    refresh_user_list()

def create_base_tab(root, tab_control):
    def load_testsuites():
        try:
            con = psycopg2.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=db_name
            )
            with con.cursor() as cursor:
                cursor.execute("SELECT suite_id, suite_name, description FROM TestSuites;")
                testsuites = cursor.fetchall()
                return testsuites
        except Exception as ex:
            print("[ERROR] Error while loading test suites:", ex)
            return []
        finally:
            if con:
                con.close()
                print("[INFO] PostgreSQL connection closed")

    def refresh_testsuite_list():
        for row in testsuite_tree.get_children():
            testsuite_tree.delete(row)
        testsuites = load_testsuites()
        for testsuite in testsuites:
            testsuite_tree.insert("", "end", values=testsuite)

    def add_testsuite():
        create_testsuite_window(root, refresh_testsuite_list)

    def edit_selected_testsuite():
        selected_item = testsuite_tree.selection()
        if not selected_item:
            return
        suite_id = testsuite_tree.item(selected_item)["values"][0]
        create_testsuite_window(root, refresh_testsuite_list, suite_id)

    def view_selected_testsuite():
        selected_item = testsuite_tree.selection()
        if not selected_item:
            return
        suite_id = testsuite_tree.item(selected_item)["values"][0]
        show_testcases(root, suite_id)

    def delete_selected_testsuite():
        selected_item = testsuite_tree.selection()
        if not selected_item:
            return
        suite_id = testsuite_tree.item(selected_item)["values"][0]
        delete_testsuite(suite_id, refresh_testsuite_list)

    if get_current_user_role_id() != 1:
        return

    base_tab = ttk.Frame(tab_control)
    tab_control.add(base_tab, text="База")

    testsuite_tree = ttk.Treeview(base_tab, columns=("id", "name", "description"), show="headings")
    testsuite_tree.heading("id", text="ID")
    testsuite_tree.heading("name", text="Название набора")
    testsuite_tree.heading("description", text="Описание")
    testsuite_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    button_frame = tk.Frame(base_tab)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

   ### Обновленный `gui.py` (продолжение):
    view_button = tk.Button(button_frame, text="Просмотр", command=view_selected_testsuite)
    view_button.pack(side=tk.LEFT, padx=5, pady=5)

    edit_button = tk.Button(button_frame, text="Редактировать", command=edit_selected_testsuite)
    edit_button.pack(side=tk.LEFT, padx=5, pady=5)

    delete_button = tk.Button(button_frame, text="Удалить", command=delete_selected_testsuite)
    delete_button.pack(side=tk.LEFT, padx=5, pady=5)

    add_button = tk.Button(button_frame, text="Добавить", command=add_testsuite)
    add_button.pack(side=tk.LEFT, padx=5, pady=5)

    refresh_testsuite_list()

def show_testcases(root, suite_id):
    testcase_window = tk.Toplevel(root)
    testcase_window.title("Тест-кейсы набора")

    def load_testcases():
        try:
            con = psycopg2.connect(
                host=host,
                user=db_user,
                password=db_password,
                database=db_name
            )
            with con.cursor() as cursor:
                cursor.execute(
                    "SELECT id_case, name, description FROM TestCases WHERE id_case IN "
                    "(SELECT case_id FROM TestSuiteCases WHERE suite_id = %s);",
                    (suite_id,)
                )
                testcases = cursor.fetchall()
                return testcases
        except Exception as ex:
            print("[ERROR] Error while loading test cases:", ex)
            return []
        finally:
            if con:
                con.close()
                print("[INFO] PostgreSQL connection closed")

    def refresh_testcase_list():
        for row in testcase_tree.get_children():
            testcase_tree.delete(row)
        testcases = load_testcases()
        for testcase in testcases:
            testcase_tree.insert("", "end", values=testcase)

    def add_testcase():
        create_testcase_window(testcase_window, refresh_testcase_list, suite_id)

    def edit_selected_testcase():
        selected_item = testcase_tree.selection()
        if not selected_item:
            return
        test_case_id = testcase_tree.item(selected_item)["values"][0]
        edit_testcase(testcase_window, test_case_id, refresh_testcase_list)

    def view_selected_testcase():
        selected_item = testcase_tree.selection()
        if not selected_item:
            return
        test_case_id = testcase_tree.item(selected_item)["values"][0]
        view_testcase(testcase_window, test_case_id)

    def delete_selected_testcase():
        selected_item = testcase_tree.selection()
        if not selected_item:
            return
        test_case_id = testcase_tree.item(selected_item)["values"][0]
        delete_testcase(test_case_id, refresh_testcase_list)

    testcase_tree = ttk.Treeview(testcase_window, columns=("id", "name", "description"), show="headings")
    testcase_tree.heading("id", text="ID")
    testcase_tree.heading("name", text="Название")
    testcase_tree.heading("description", text="Описание")
    testcase_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    button_frame = tk.Frame(testcase_window)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    view_button = tk.Button(button_frame, text="Просмотр", command=view_selected_testcase)
    view_button.pack(side=tk.LEFT, padx=5, pady=5)

    edit_button = tk.Button(button_frame, text="Редактировать", command=edit_selected_testcase)
    edit_button.pack(side=tk.LEFT, padx=5, pady=5)

    delete_button = tk.Button(button_frame, text="Удалить", command=delete_selected_testcase)
    delete_button.pack(side=tk.LEFT, padx=5, pady=5)

    add_button = tk.Button(button_frame, text="Добавить", command=add_testcase)
    add_button.pack(side=tk.LEFT, padx=5, pady=5)

    refresh_testcase_list()

from testcase_management import save_testcase, update_testcase, delete_testcase, view_testcase, edit_testcase, load_testcases, create_testcase_window, create_testsuite_window, refresh_testsuites, load_testsuites, delete_testsuite, load_test_runs

def create_test_run_tab(root, tab_control):
    test_run_tab = ttk.Frame(tab_control)
    tab_control.add(test_run_tab, text="Пройденные тесты")

    frame_btn = tk.Frame(test_run_tab)
    frame_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    button_refresh = tk.Button(frame_btn, text="Обновить", command=lambda: refresh_test_runs(tab2_frame))
    button_refresh.grid(row=0, column=0, pady=5, padx=5)

    tab2_frame = tk.Frame(test_run_tab)
    tab2_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    refresh_test_runs(tab2_frame)

def refresh_test_runs(tab2_frame):
    for widget in tab2_frame.winfo_children():
        widget.destroy()

    testcases_tree = ttk.Treeview(tab2_frame, columns=("id_run", "suite_name", "case_name", "status", "execution_date"), show="headings")
    testcases_tree.heading("id_run", text="ID")
    testcases_tree.heading("suite_name", text="Название набора")
    testcases_tree.heading("case_name", text="Название тест-кейса")
    testcases_tree.heading("status", text="Статус")
    testcases_tree.heading("execution_date", text="Дата выполнения")
    testcases_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    test_runs = load_test_runs()
    for test_run in test_runs:
        testcases_tree.insert("", "end", values=test_run)

    button_frame = tk.Frame(tab2_frame)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def view_selected_testcase():
        selected_item = testcases_tree.selection()
        if not selected_item:
            return
        test_run_id = testcases_tree.item(selected_item)["values"][0]
        view_testcase_run(tab2_frame, test_run_id)

    def delete_selected_testcase():
        selected_item = testcases_tree.selection()
        if not selected_item:
            return
        test_run_id = testcases_tree.item(selected_item)["values"][0]
        delete_test_run(test_run_id, tab2_frame)

    view_button = tk.Button(button_frame, text="Просмотр", command=view_selected_testcase)
    view_button.pack(side=tk.LEFT, padx=5, pady=5)

    delete_button = tk.Button(button_frame, text="Удалить", command=delete_selected_testcase)
    delete_button.pack(side=tk.LEFT, padx=5, pady=5)

    refresh_button = tk.Button(button_frame, text="Обновить", command=lambda: refresh_test_runs(tab2_frame))
    refresh_button.pack(side=tk.LEFT, padx=5, pady=5)


def load_test_runs_suites():
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT ts.suite_id, ts.suite_name FROM TestRuns tr "
                "JOIN TestCases tc ON tr.testcase_id = tc.id_case "
                "JOIN TestSuiteCases tsc ON tc.id_case = tsc.case_id "
                "JOIN TestSuites ts ON tsc.suite_id = ts.suite_id;"
            )
            test_suites = cursor.fetchall()
            return test_suites
    except Exception as ex:
        print("[ERROR] Error while loading test run suites:", ex)
        return []
    finally:
        close_db_connection(con)

def show_test_runs(tab2_frame, suite_id):
    testcases_window = tk.Toplevel(tab2_frame)
    testcases_window.title("Пройденные тест-кейсы набора")

    testcase_tree = ttk.Treeview(testcases_window, columns=("id", "name", "status", "execution_date"), show="headings")
    testcase_tree.heading("id", text="ID")
    testcase_tree.heading("name", text="Название")
    testcase_tree.heading("status", text="Статус")
    testcase_tree.heading("execution_date", text="Дата выполнения")
    testcase_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    test_runs = load_test_runs_by_suite(suite_id)
    for test_run in test_runs:
        testcase_tree.insert("", "end", values=test_run)

    button_frame = tk.Frame(testcases_window)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def view_selected_testcase():
        selected_item = testcase_tree.selection()
        if not selected_item:
            return
        test_run_id = testcase_tree.item(selected_item)["values"][0]
        view_testcase_run(testcases_window, test_run_id)

    def delete_selected_testcase():
        selected_item = testcase_tree.selection()
        if not selected_item:
            return
        test_run_id = testcase_tree.item(selected_item)["values"][0]
        delete_test_run(test_run_id, suite_id, tab2_frame, testcases_window)

    view_button = tk.Button(button_frame, text="Просмотр", command=view_selected_testcase)
    view_button.pack(side=tk.LEFT, padx=5, pady=5)

    delete_button = tk.Button(button_frame, text="Удалить", command=delete_selected_testcase)
    delete_button.pack(side=tk.LEFT, padx=5, pady=5)

def load_test_runs_by_suite(suite_id):
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT tr.id_run, tc.name, tr.status, tr.execution_date FROM TestRuns tr "
                "JOIN TestCases tc ON tr.testcase_id = tc.id_case "
                "JOIN TestSuiteCases tsc ON tc.id_case = tsc.case_id "
                "WHERE tsc.suite_id = %s;", (suite_id,)
            )
            test_runs = cursor.fetchall()
            return test_runs
    except Exception as ex:
        print("[ERROR] Error while loading test runs by suite:", ex)
        return []
    finally:
        close_db_connection(con)

def delete_test_run(test_run_id, tab2_frame):
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute("DELETE FROM TestRuns WHERE id_run = %s;", (test_run_id,))
        con.commit()
        print("[INFO] Test run deleted successfully!")
        refresh_test_runs(tab2_frame)
    except Exception as ex:
        print("[ERROR] Error while deleting test run:", ex)
    finally:
        close_db_connection(con)

def view_testcase_run(tab2_frame, test_run_id):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT tc.name, tc.description, tr.status, tr.execution_date FROM TestRuns tr "
                "JOIN TestCases tc ON tr.testcase_id = tc.id_case WHERE tr.id_run = %s;", (test_run_id,)
            )
            test_run = cursor.fetchone()

            cursor.execute(
                "SELECT StepNumber, ActionDescription, ExpectedResult, Status FROM TestCaseSteps WHERE TestCaseID = %s ORDER BY StepNumber;",
                (test_run_id,)
            )
            steps = cursor.fetchall()

        view_window = tk.Toplevel(tab2_frame)
        view_window.title("Просмотр пройденного тест-кейса")

        tk.Label(view_window, text="Название:").grid(row=0, column=0, sticky="w")
        tk.Label(view_window, text=test_run[0]).grid(row=0, column=1, padx=10, pady=5, sticky="we")

        tk.Label(view_window, text="Описание:").grid(row=1, column=0, sticky="w")
        tk.Label(view_window, text=test_run[1]).grid(row=1, column=1, padx=10, pady=5, sticky="we")

        tk.Label(view_window, text="Статус:").grid(row=2, column=0, sticky="w")
        tk.Label(view_window, text=test_run[2]).grid(row=2, column=1, padx=10, pady=5, sticky="we")

        tk.Label(view_window, text="Дата выполнения:").grid(row=3, column=0, sticky="w")
        tk.Label(view_window, text=test_run[3]).grid(row=3, column=1, padx=10, pady=5, sticky="we")

        steps_frame = tk.Frame(view_window)
        steps_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        for step_num, (step_number, step, result, status) in enumerate(steps, start=1):
            tk.Label(steps_frame, text=f"Шаг {step_num}:").grid(row=step_num, column=0, sticky="w")
            tk.Label(steps_frame, text=step).grid(row=step_num, column=1, padx=5, pady=5, sticky="we")
            tk.Label(steps_frame, text="Ожидаемый результат:").grid(row=step_num, column=2, sticky="w")
            tk.Label(steps_frame, text=result).grid(row=step_num, column=3, padx=5, pady=5, sticky="we")
            tk.Label(steps_frame, text="Статус:").grid(row=step_num, column=4, sticky="w")
            tk.Label(steps_frame, text=status).grid(row=step_num, column=5, padx=5, pady=5, sticky="we")

        steps_frame.columnconfigure(1, weight=1)
        steps_frame.columnconfigure(3, weight=1)
        steps_frame.rowconfigure(len(steps) + 1, weight=1)

    except Exception as ex:
        print("[ERROR] Error while viewing test case run:", ex)
    finally:
        close_db_connection(con)

