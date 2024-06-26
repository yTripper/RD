import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from user_management import check_credentials, current_user_role_id, get_current_user_role_id
import psycopg2
from config import host, user as db_user, password as db_password, db_name
from database import get_db_connection, close_db_connection


# Functions to manage test cases
def save_testcase(name, description, steps, refresh_testcases_callback, suite_id=None):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "INSERT INTO TestCases (name, description) VALUES (%s, %s) RETURNING id_case;",
                (name, description)
            )
            test_case_id = cursor.fetchone()[0]

            for step_num, (step, result, status) in enumerate(steps, start=1):
                cursor.execute(
                    "INSERT INTO TestCaseSteps (StepNumber, ActionDescription, ExpectedResult, Status, TestCaseID) "
                    "VALUES (%s, %s, %s, %s, %s);",
                    (step_num, step, result, status, test_case_id)
                )
            
            if suite_id:
                cursor.execute(
                    "INSERT INTO TestSuiteCases (suite_id, case_id) VALUES (%s, %s);",
                    (suite_id, test_case_id)
                )

        con.commit()
        print("[INFO] Test case saved successfully!")
        refresh_testcases_callback()  # Refresh the list of test cases after saving

    except Exception as ex:
        print("[ERROR] Error while saving test case:", ex)
    finally:
        close_db_connection(con)

def update_testcase(test_case_id, name, description, steps, refresh_testcases_callback):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "UPDATE TestCases SET name = %s, description = %s WHERE id_case = %s;",
                (name, description, test_case_id)
            )
            cursor.execute(
                "DELETE FROM TestCaseSteps WHERE TestCaseID = %s;",
                (test_case_id,)
            )
            for step_num, (step, result, status) in enumerate(steps, start=1):
                cursor.execute(
                    "INSERT INTO TestCaseSteps (StepNumber, ActionDescription, ExpectedResult, Status, TestCaseID) "
                    "VALUES (%s, %s, %s, %s, %s);",
                    (step_num, step, result, status, test_case_id)
                )

        con.commit()
        print("[INFO] Test case updated successfully!")
        refresh_testcases_callback()  # Refresh the list of test cases after updating

    except Exception as ex:
        print("[ERROR] Error while updating test case:", ex)
    finally:
        close_db_connection(con)

def delete_testcase(test_case_id, refresh_testcases_callback):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute("DELETE FROM TestCaseSteps WHERE TestCaseID = %s;", (test_case_id,))
            cursor.execute("DELETE FROM TestSuiteCases WHERE case_id = %s;", (test_case_id,))
            cursor.execute("DELETE FROM TestCases WHERE id_case = %s;", (test_case_id,))

        con.commit()
        print("[INFO] Test case deleted successfully!")
        refresh_testcases_callback()  # Refresh the list of test cases after deletion

    except Exception as ex:
        print("[ERROR] Error while deleting test case:", ex)
    finally:
        close_db_connection(con)

def load_testcases(suite_id):
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT tc.id_case, tc.name, tc.description FROM TestCases tc "
                "JOIN TestSuiteCases tsc ON tc.id_case = tsc.case_id WHERE tsc.suite_id = %s;", 
                (suite_id,)
            )
            testcases = cursor.fetchall()
            return testcases
    except Exception as ex:
        print("[ERROR] Error while loading test cases:", ex)
        return []
    finally:
        close_db_connection(con)


def change_status(step_num, steps_frame, test_case_id, user_id, step_statuses):
    status_window = tk.Toplevel(steps_frame)
    status_window.title("Изменить статус")

    def set_status(new_status):
        button = steps_frame.grid_slaves(row=step_num, column=4)[0]
        color = status_colors.get(new_status, "white")  # Получаем цвет для нового статуса
        button.config(text=new_status, bg=color, activebackground=color)  # Устанавливаем текст и цвет кнопки
        step_statuses[step_num] = new_status
        status_window.destroy()

    statuses = [("Успешен", "green"), ("Пропущен", "yellow"), ("Провален", "red"), ("Заблокирован", "grey")]
    status_colors = {status: color for status, color in statuses}

    for idx, (status, color) in enumerate(statuses):
        button = tk.Button(status_window, text=status, bg=color, command=lambda s=status: set_status(s))
        button.grid(row=idx, column=0, padx=5, pady=5, sticky="we")



def edit_testcase(root, test_case_id, refresh_testcases_callback):
    def save_edited_testcase():
        name = name_entry.get()
        description = description_entry.get()
        steps = [(step_entry.get(), result_entry.get(), 'Не задан') for step_entry, result_entry in steps_widgets]

        con = None
        try:
            con = get_db_connection()
            with con.cursor() as cursor:
                cursor.execute(
                    "UPDATE TestCases SET name = %s, description = %s WHERE id_case = %s;",
                    (name, description, test_case_id)
                )

                cursor.execute("DELETE FROM TestCaseSteps WHERE TestCaseID = %s;", (test_case_id,))
                for step_num, (step, result, status) in enumerate(steps, start=1):
                    cursor.execute(
                        "INSERT INTO TestCaseSteps (StepNumber, ActionDescription, ExpectedResult, Status, TestCaseID) "
                        "VALUES (%s, %s, %s, %s, %s);",
                        (step_num, step, result, status, test_case_id)
                    )

            con.commit()
            print("[INFO] Test case updated successfully!")
            edit_window.destroy()
            refresh_testcases_callback()  # Обновление списка тест-кейсов после редактирования

        except Exception as ex:
            print("[ERROR] Error while updating test case:", ex)
        finally:
            close_db_connection(con)

    def add_step(step_num, step="", result=""):
        step_label = tk.Label(steps_frame, text=f"Шаг {step_num}:")
        step_label.grid(row=step_num, column=0, sticky="w")
        step_entry = tk.Entry(steps_frame, width=50)
        step_entry.insert(0, step)
        step_entry.grid(row=step_num, column=1, padx=5, pady=5, sticky="we")
        result_label = tk.Label(steps_frame, text="Ожидаемый результат:")
        result_label.grid(row=step_num, column=2, sticky="w")
        result_entry = tk.Entry(steps_frame, width=50)
        result_entry.insert(0, result)
        result_entry.grid(row=step_num, column=3, padx=5, pady=5, sticky="we")

        steps_widgets.append((step_entry, result_entry))
        num_steps[0] += 1

    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute("SELECT name, description FROM TestCases WHERE id_case = %s;", (test_case_id,))
            testcase = cursor.fetchone()

            cursor.execute("SELECT StepNumber, ActionDescription, ExpectedResult, Status FROM TestCaseSteps WHERE TestCaseID = %s ORDER BY StepNumber;", (test_case_id,))
            steps = cursor.fetchall()

        edit_window = tk.Toplevel(root)
        edit_window.title("Редактирование тест-кейса")

        tk.Label(edit_window, text="Название:").grid(row=0, column=0, sticky="w")
        name_entry = tk.Entry(edit_window)
        name_entry.insert(0, testcase[0])
        name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")

        tk.Label(edit_window, text="Описание:").grid(row=1, column=0, sticky="w")
        description_entry = tk.Entry(edit_window)
        description_entry.insert(0, testcase[1])
        description_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")

        steps_frame = tk.Frame(edit_window)
        steps_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        steps_widgets = []
        num_steps = [0]

        for step_num, (step_number, step, result, status) in enumerate(steps, start=1):
            add_step(step_num, step, result)

        add_step_button = tk.Button(edit_window, text="Добавить шаги", command=lambda: add_step(num_steps[0] + 1))
        add_step_button.grid(row=3, column=0, columnspan=2, pady=10)

        save_button = tk.Button(edit_window, text="Сохранить", command=save_edited_testcase)
        save_button.grid(row=4, column=0, columnspan=2, pady=10)

        steps_frame.columnconfigure(1, weight=1)
        steps_frame.columnconfigure(3, weight=1)
        steps_frame.rowconfigure(len(steps) + 1, weight=1)

    except Exception as ex:
        print("[ERROR] Error while editing test case:", ex)
    finally:
        close_db_connection(con)

# Functions to manage test suites
def save_testsuite(name, description, refresh_testsuites_callback):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "INSERT INTO TestSuites (suite_name, description) VALUES (%s, %s) RETURNING suite_id;",
                (name, description)
            )
            suite_id = cursor.fetchone()[0]

        con.commit()
        print("[INFO] Test suite saved successfully!")
        refresh_testsuites_callback()  # Refresh the list of test suites after saving

    except Exception as ex:
        print("[ERROR] Error while saving test suite:", ex)
    finally:
        close_db_connection(con)

def update_testsuite(suite_id, name, description, refresh_testsuites_callback):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "UPDATE TestSuites SET suite_name = %s, description = %s WHERE suite_id = %s;",
                (name, description, suite_id)
            )

        con.commit()
        print("[INFO] Test suite updated successfully!")
        refresh_testsuites_callback()  # Refresh the list of test suites after updating

    except Exception as ex:
        print("[ERROR] Error while updating test suite:", ex)
    finally:
        close_db_connection(con)

def delete_testsuite(suite_id, refresh_testsuites_callback):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "DELETE FROM TestSuiteCases WHERE suite_id = %s;",
                (suite_id,)
            )
            cursor.execute(
                "DELETE FROM TestSuites WHERE suite_id = %s;",
                (suite_id,)
            )

        con.commit()
        print("[INFO] Test suite deleted successfully!")
        refresh_testsuites_callback()  # Refresh the list of test suites after deletion

    except Exception as ex:
        print("[ERROR] Error while deleting test suite:", ex)
    finally:
        close_db_connection(con)

def load_testsuites():
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute("SELECT suite_id, suite_name, description FROM TestSuites;")
            testsuites = cursor.fetchall()
            return testsuites
    except Exception as ex:
        print("[ERROR] Error while loading test suites:", ex)
        return []
    finally:
        close_db_connection(con)

# GUI Functions
def create_testcase_window(root, refresh_testcases_callback, suite_id, test_case_id=None):
    def save_testcase_to_db():
        name = name_entry.get()
        description = description_entry.get()
        steps = [(step_entry.get(), result_entry.get(), 'Не задан') for step_entry, result_entry in steps_widgets]

        if test_case_id:
            update_testcase(test_case_id, name, description, steps, refresh_testcases_callback)
        else:
            save_testcase(name, description, steps, refresh_testcases_callback, suite_id)
        testcase_window.destroy()

    def add_step(step_num, step="", result=""):
        step_label = tk.Label(steps_frame, text=f"Шаг {step_num}:")
        step_label.grid(row=step_num, column=0, sticky="w")
        step_entry = tk.Entry(steps_frame, width=50)
        step_entry.insert(0, step)
        step_entry.grid(row=step_num, column=1, padx=5, pady=5, sticky="we")
        result_label = tk.Label(steps_frame, text="Ожидаемый результат:")
        result_label.grid(row=step_num, column=2, sticky="w")
        result_entry = tk.Entry(steps_frame, width=50)
        result_entry.insert(0, result)
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

    # If editing an existing test case, populate fields with current values
    if test_case_id:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT name, description FROM TestCases WHERE id_case = %s;", (test_case_id,)
            )
            name, description = cursor.fetchone()
            name_entry.insert(0, name)
            description_entry.insert(0, description)

            cursor.execute(
                "SELECT StepNumber, ActionDescription, ExpectedResult, Status FROM TestCaseSteps WHERE TestCaseID = %s ORDER BY StepNumber;",
                (test_case_id,)
            )
            steps = cursor.fetchall()
            for step_num, (step_number, step, result, status) in enumerate(steps, start=1):
                add_step(step_num, step, result)

        close_db_connection(con)

def create_testsuite_window(root, refresh_testsuites_callback, suite_id=None):
    def save_testsuite_to_db():
        name = name_entry.get()
        description = description_entry.get()

        if suite_id:
            update_testsuite(suite_id, name, description, refresh_testsuites_callback)
        else:
            save_testsuite(name, description, refresh_testsuites_callback)
        testsuite_window.destroy()

    testsuite_window = tk.Toplevel(root)
    testsuite_window.title("Создание набора тест-кейсов")

    tk.Label(testsuite_window, text="Название набора:").grid(row=0, column=0, sticky="w")
    name_entry = tk.Entry(testsuite_window)
    name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")

    tk.Label(testsuite_window, text="Описание набора:").grid(row=1, column=0, sticky="w")
    description_entry = tk.Entry(testsuite_window)
    description_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")

    save_button = tk.Button(testsuite_window, text="Сохранить", command=save_testsuite_to_db)
    save_button.grid(row=2, column=0, columnspan=2, pady=10)

    testsuite_window.columnconfigure(1, weight=1)

    # If editing an existing test suite, populate fields with current values
    if suite_id:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT suite_name, description FROM TestSuites WHERE suite_id = %s;", (suite_id,)
            )
            name, description = cursor.fetchone()
            name_entry.insert(0, name)
            description_entry.insert(0, description)

        close_db_connection(con)

def refresh_testsuites(root, tab2_frame, show_testcases_callback):
    for widget in tab2_frame.winfo_children():
        widget.destroy()

    testsuites = load_testsuites()
    for idx, (suite_id, name, description) in enumerate(testsuites):
        tk.Label(tab2_frame, text=f"{name}").grid(row=idx, column=0, sticky="w")
        tk.Button(tab2_frame, text="Просмотр", command=lambda sid=suite_id: show_testcases_callback(root, sid)).grid(row=idx, column=1, sticky="w")
        tk.Button(tab2_frame, text="Редактировать", command=lambda sid=suite_id: create_testsuite_window(root, lambda: refresh_testsuites(root, tab2_frame, show_testcases_callback), sid)).grid(row=idx, column=2, sticky="w")
        tk.Button(tab2_frame, text="Удалить", command=lambda sid=suite_id: delete_testsuite(sid, lambda: refresh_testsuites(root, tab2_frame, show_testcases_callback))).grid(row=idx, column=3, sticky="w")

def refresh_testcases(testcases_window, suite_id):
    for widget in testcases_window.grid_slaves():
        widget.destroy()

    frame_btn = tk.Frame(testcases_window)
    frame_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    button_create_case = tk.Button(frame_btn, text="Создать тест-кейс", command=lambda: create_testcase_window(testcases_window, lambda: refresh_testcases(testcases_window, suite_id), suite_id))
    button_create_case.grid(row=0, column=0, pady=5, padx=5)

    testcases = load_testcases(suite_id)
    for idx, (test_case_id, name, description) in enumerate(testcases):
        tk.Label(testcases_window, text=f"{name}").grid(row=idx + 1, column=0, sticky="w")
        tk.Button(testcases_window, text="Просмотр", command=lambda tcid=test_case_id: view_testcase(testcases_window, tcid)).grid(row=idx + 1, column=1, sticky="w")
        tk.Button(testcases_window, text="Редактировать", command=lambda tcid=test_case_id: create_testcase_window(testcases_window, lambda: refresh_testcases(testcases_window, suite_id), suite_id, tcid)).grid(row=idx + 1, column=2, sticky="w")
        tk.Button(testcases_window, text="Удалить", command=lambda tcid=test_case_id: delete_testcase(tcid, lambda: refresh_testcases(testcases_window, suite_id))).grid(row=idx + 1, column=3, sticky="w")

def save_test_run(test_case_id, user_id, status, step_statuses):
    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "INSERT INTO TestRuns (testcase_id, user_id, status) VALUES (%s, %s, %s) RETURNING id_run;",
                (test_case_id, user_id, status)
            )
            test_run_id = cursor.fetchone()[0]

            for step_num, step_status in step_statuses.items():
                cursor.execute(
                    "UPDATE TestCaseSteps SET Status = %s WHERE TestCaseID = %s AND StepNumber = %s;",
                    (step_status, test_case_id, step_num)
                )

        con.commit()
        print("[INFO] Test run saved successfully!")
    except Exception as ex:
        print("[ERROR] Error while saving test run:", ex)
    finally:
        close_db_connection(con)


# Глобальная переменная для хранения открытых окон просмотра тест-кейсов
view_testcase_windows = {}

def view_testcase(root, test_case_id):
    global view_testcase_windows

    # Если окно уже открыто, фокусируемся на нем и выходим
    if test_case_id in view_testcase_windows and view_testcase_windows[test_case_id].winfo_exists():
        view_testcase_windows[test_case_id].lift()
        view_testcase_windows[test_case_id].focus_force()
        return

    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute("SELECT name, description FROM TestCases WHERE id_case = %s;", (test_case_id,))
            testcase = cursor.fetchone()

            # Сбрасываем статусы шагов перед просмотром тест-кейса
            cursor.execute(
                "UPDATE TestCaseSteps SET Status = 'Не задан' WHERE TestCaseID = %s;",
                (test_case_id,)
            )

            cursor.execute("SELECT StepNumber, ActionDescription, ExpectedResult, Status FROM TestCaseSteps WHERE TestCaseID = %s ORDER BY StepNumber;", (test_case_id,))
            steps = cursor.fetchall()

        view_window = tk.Toplevel(root)
        view_window.title("Просмотр тест-кейса")
        view_testcase_windows[test_case_id] = view_window  # Сохраняем ссылку на новое окно

        tk.Label(view_window, text="Название:").grid(row=0, column=0, sticky="w")
        tk.Label(view_window, text=testcase[0]).grid(row=0, column=1, padx=10, pady=5, sticky="we")

        tk.Label(view_window, text="Описание:").grid(row=1, column=0, sticky="w")
        tk.Label(view_window, text=testcase[1]).grid(row=1, column=1, padx=10, pady=5, sticky="we")

        steps_frame = tk.Frame(view_window)
        steps_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        user_id = get_current_user_role_id()
        step_statuses = {}

        statuses = [("Успешен", "green"), ("Пропущен", "yellow"), ("Провален", "red"), ("Заблокирован", "grey")]
        status_colors = {status: color for status, color in statuses}

        for step_num, (step_number, step, result, status) in enumerate(steps, start=1):
            tk.Label(steps_frame, text=f"Шаг {step_num}:").grid(row=step_num, column=0, sticky="w")
            tk.Label(steps_frame, text=step).grid(row=step_num, column=1, padx=5, pady=5, sticky="we")
            tk.Label(steps_frame, text="Ожидаемый результат:").grid(row=step_num, column=2, sticky="w")
            tk.Label(steps_frame, text=result).grid(row=step_num, column=3, padx=5, pady=5, sticky="we")
            status_button = tk.Button(
                steps_frame,
                text='Не задан',
                bg=status_colors.get('Не задан', "white"),  # Устанавливаем цвет кнопки в зависимости от статуса
                activebackground=status_colors.get('Не задан', "white"),  # Устанавливаем цвет при активации
                command=lambda sn=step_num: change_status(sn, steps_frame, test_case_id, user_id, step_statuses)
            )
            status_button.grid(row=step_num, column=4, padx=5, pady=5, sticky="we")

        steps_frame.columnconfigure(1, weight=1)
        steps_frame.columnconfigure(3, weight=1)
        steps_frame.rowconfigure(len(steps) + 1, weight=1)

        finish_button = tk.Button(view_window, text="Завершить", command=lambda: finish_testcase(view_window, test_case_id, user_id, step_statuses))
        finish_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Закрытие окна и удаление из глобального списка
        def on_closing():
            del view_testcase_windows[test_case_id]
            view_window.destroy()

        view_window.protocol("WM_DELETE_WINDOW", on_closing)

    except Exception as ex:
        print("[ERROR] Error while viewing test case:", ex)
    finally:
        close_db_connection(con)




def finish_testcase(view_window, test_case_id, user_id, step_statuses):
    save_test_run(test_case_id, user_id, "Завершен", step_statuses)
    refresh_test_runs(view_window)



def load_test_runs():
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT tr.id_run, ts.suite_name, tc.name, tr.status, tr.execution_date "
                "FROM TestRuns tr "
                "JOIN TestCases tc ON tr.testcase_id = tc.id_case "
                "JOIN TestSuiteCases tsc ON tc.id_case = tsc.case_id "
                "JOIN TestSuites ts ON tsc.suite_id = ts.suite_id "
                "ORDER BY tr.execution_date DESC;"
            )
            test_runs = cursor.fetchall()
            return test_runs
    except Exception as ex:
        print("[ERROR] Error while loading test runs:", ex)
        return []
    finally:
        close_db_connection(con)



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





def load_test_runs():
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            cursor.execute(
                "SELECT tr.id_run, ts.suite_name, tc.name, tr.status, tr.execution_date FROM TestRuns tr "
                "JOIN TestCases tc ON tr.testcase_id = tc.id_case "
                "JOIN TestSuiteCases tsc ON tc.id_case = tsc.case_id "
                "JOIN TestSuites ts ON tsc.suite_id = ts.suite_id;"
            )
            test_runs = cursor.fetchall()
            return test_runs
    except Exception as ex:
        print("[ERROR] Error while loading test runs:", ex)
        return []
    finally:
        close_db_connection(con)

# Глобальная переменная для хранения открытых окон просмотра пройденных тест-кейсов
view_testcase_run_windows = {}

def view_testcase_run(tab2_frame, test_run_id):
    global view_testcase_run_windows

    # Если окно уже открыто, фокусируемся на нем и выходим
    if test_run_id in view_testcase_run_windows and view_testcase_run_windows[test_run_id].winfo_exists():
        view_testcase_run_windows[test_run_id].lift()
        view_testcase_run_windows[test_run_id].focus_force()
        return

    con = None
    try:
        con = get_db_connection()
        with con.cursor() as cursor:
            # Извлекаем данные о тест-кейсе
            cursor.execute(
                "SELECT tc.name, tc.description, tr.status, tr.execution_date FROM TestRuns tr "
                "JOIN TestCases tc ON tr.testcase_id = tc.id_case WHERE tr.id_run = %s;", (test_run_id,)
            )
            test_run = cursor.fetchone()

            # Извлекаем шаги тест-кейса
            cursor.execute(
                "SELECT StepNumber, ActionDescription, ExpectedResult, Status FROM TestCaseSteps WHERE TestCaseID = (SELECT testcase_id FROM TestRuns WHERE id_run = %s) ORDER BY StepNumber;",
                (test_run_id,)
            )
            steps = cursor.fetchall()

        view_window = tk.Toplevel(tab2_frame)
        view_window.title("Просмотр пройденного тест-кейса")
        view_testcase_run_windows[test_run_id] = view_window  # Сохраняем ссылку на новое окно

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

        statuses = [("Успешен", "green"), ("Пропущен", "yellow"), ("Провален", "red"), ("Заблокирован", "grey")]
        status_colors = {status: color for status, color in statuses}

        for step_num, (step_number, step, result, status) in enumerate(steps, start=1):
            tk.Label(steps_frame, text=f"Шаг {step_num}:").grid(row=step_num, column=0, sticky="w")
            tk.Label(steps_frame, text=step).grid(row=step_num, column=1, padx=5, pady=5, sticky="we")
            tk.Label(steps_frame, text="Ожидаемый результат:").grid(row=step_num, column=2, sticky="w")
            tk.Label(steps_frame, text=result).grid(row=step_num, column=3, padx=5, pady=5, sticky="we")
            status_label = tk.Label(
                steps_frame,
                text=status,
                bg=status_colors.get(status, "white"),
                width=12
            )
            status_label.grid(row=step_num, column=4, padx=5, pady=5, sticky="we")

        steps_frame.columnconfigure(1, weight=1)
        steps_frame.columnconfigure(3, weight=1)
        steps_frame.rowconfigure(len(steps) + 1, weight=1)

        # Закрытие окна и удаление из глобального списка
        def on_closing():
            del view_testcase_run_windows[test_run_id]
            view_window.destroy()

        view_window.protocol("WM_DELETE_WINDOW", on_closing)

    except Exception as ex:
        print("[ERROR] Error while viewing test case run:", ex)
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


