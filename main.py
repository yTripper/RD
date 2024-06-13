import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from gui import create_user_management_tab, create_error_message
from testcase_management import create_testsuite_window, refresh_testsuites, show_testcases
from user_management import check_credentials, current_user_role_id

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

    button_create_suite = tk.Button(frame_btn, text="Создать набор тест-кейсов", command=lambda: create_testsuite_window(root, lambda: refresh_testsuites(root, tab2_frame, show_testcases)))
    button_create_suite.pack(pady=5, padx=5)

    tab2_frame = tk.Frame(tab2)
    tab2_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    refresh_testsuites(root, tab2_frame, show_testcases)

    create_user_management_tab(root, tab_control)

    tab_control.pack(expand=1, fill="both")
    root.mainloop()

if __name__ == "__main__":
    login()
