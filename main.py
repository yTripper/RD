import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from gui import create_user_management_tab, create_error_message, create_base_tab, create_test_run_tab
from user_management import check_credentials, get_current_user_role_id

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

    # Установка иконки для окна входа
    icon_path = "img/RD.png"
    login_icon = ImageTk.PhotoImage(Image.open(icon_path))  # Сохраняем ссылку на иконку
    login_window.iconphoto(True, login_icon)

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

    # Установка иконки для главного окна
    icon_path = "img/RD.png"
    main_icon = ImageTk.PhotoImage(Image.open(icon_path))  # Сохраняем ссылку на иконку
    root.iconphoto(True, main_icon)

    tab_control = ttk.Notebook(root)

    tab1 = ttk.Frame(tab_control)
    tab_control.add(tab1, text="Главная")

    image = Image.open("img/dwarf.png")
    photo = ImageTk.PhotoImage(image)
    label1 = tk.Label(tab1, image=photo)
    label1.image = photo
    label1.pack(pady=10, padx=10)

    create_user_management_tab(root, tab_control)
    create_base_tab(root, tab_control)
    create_test_run_tab(root, tab_control)

    tab_control.pack(expand=1, fill="both")
    root.mainloop()

if __name__ == "__main__":
    login()
