import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import sqlite3
import hashlib
import os
import subprocess
import time


class Database:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                                id INTEGER PRIMARY KEY,
                                nickname TEXT UNIQUE,
                                password TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Books (
                                id INTEGER PRIMARY KEY,
                                title TEXT,
                                path TEXT,
                                user_id INTEGER,
                                FOREIGN KEY(user_id) REFERENCES Users(id))''')
        self.connection.commit()

    def insert_user(self, nickname, password):
        self.cursor.execute("INSERT INTO Users(nickname, password) VALUES(?, ?)", (nickname, password))
        self.connection.commit()

    def get_user(self, nickname, password):
        return self.cursor.execute("SELECT * FROM Users WHERE nickname = ? AND password = ?", (nickname, password)).fetchone()

    def insert_book(self, title, path, user_id):
        self.cursor.execute("INSERT INTO Books(title, path, user_id) VALUES (?, ?, ?)", (title, path, user_id))
        self.connection.commit()

    def get_books(self, user_id):
        return self.cursor.execute("SELECT * FROM Books WHERE user_id = ?", (user_id,)).fetchall()

    def find_book_by_id(self, book_id, user_id):
        return self.cursor.execute("SELECT * FROM Books WHERE id = ? AND user_id = ?", (book_id, user_id)).fetchone()

    def close(self):
        self.connection.close()


class User:
    def __init__(self, nickname, password):
        self.nickname = nickname
        self.password = hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def register(db, nickname, password):
        user = User(nickname, password)
        try:
            db.insert_user(user.nickname, user.password)
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def login(db, nickname, password):
        user = User(nickname, password)
        return db.get_user(user.nickname, user.password)


class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = Database("books.db")
        self.user_id = None
        self.nickname = None

        self.title("Library App")
        self.geometry("400x400")

        self.start_menu()

    def start_menu(self):
        self.clear_frame()
        tk.Label(self, text="Привет! Войдите или зарегистрируйтесь").pack(pady=10)

        tk.Button(self, text="Зарегистрироваться", command=self.register_user).pack(pady=5)
        tk.Button(self, text="Войти", command=self.login_user).pack(pady=5)

    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()

    def register_user(self):
        self.clear_frame()
        nickname = simpledialog.askstring("Регистрация", "Введите имя пользователя:")
        password = simpledialog.askstring("Регистрация", "Введите пароль:", show='*')
        confirm_password = simpledialog.askstring("Регистрация", "Введите пароль еще раз:", show='*')

        if password == confirm_password:
            if User.register(self.db, nickname, password):
                messagebox.showinfo("Регистрация", "Пользователь успешно зарегистрирован")
                self.start_menu()
            else:
                messagebox.showwarning("Ошибка", "Пользователь с таким именем уже существует.")
                self.register_user()
            
    def login_user(self):
        self.clear_frame()
        nickname = simpledialog.askstring("Вход", "Введите имя пользователя:")
        password = simpledialog.askstring("Вход", "Введите пароль:", show='*')

        user = User.login(self.db, nickname, password)
        if user:
            self.nickname = nickname
            self.user_id = user[0]
            messagebox.showinfo("Вход", f"Вы успешно вошли\nПривет, {self.nickname}!")
            self.user_menu()
        else:
            messagebox.showwarning("Ошибка", "Неверное имя пользователя или пароль.")
            self.start_menu()

    def user_menu(self):
        self.clear_frame()
        tk.Label(self, text=f"Добро пожаловать, {self.nickname}!").pack(pady=10)

        tk.Button(self, text="Добавить книгу", command=self.add_book).pack(pady=5)
        tk.Button(self, text="Вывести все книги", command=self.show_books).pack(pady=5)
        tk.Button(self, text="Получить книгу по ID", command=self.get_book).pack(pady=5)
        tk.Button(self, text="Выйти", command=self.start_menu).pack(pady=5)

    def add_book(self):
        title = simpledialog.askstring("Добавить книгу", "Введите название книги:")
        path = filedialog.askopenfilename(title="Выберите файл книги")
        
        if title and path:
            if os.path.exists(path):
                self.db.insert_book(title, path, self.user_id)
                messagebox.showinfo("Добавить книгу", f"Книга '{title}' успешно добавлена.")
            else:
                messagebox.showwarning("Ошибка", "Выбранный файл не существует.")
        else:
            messagebox.showwarning("Ошибка", "Пожалуйста, введите название книги и выберите файл.")

    def show_books(self):
        books = self.db.get_books(self.user_id)
        if books:
            books_list = "\n".join([f"{book[0]}. {book[1]}" for book in books])
            messagebox.showinfo("Список книг", books_list)
        else:
            messagebox.showinfo("Список книг", "Ваша библиотека пуста.")

    def get_book(self):
        request = simpledialog.askstring("Получить книгу", "Введите название или ID книги:")
        if request:
            result = self.db.find_book_by_id(request, self.user_id)
            if result:
                subprocess.run(["okular", result[2]])
            else:
                messagebox.showwarning("Ошибка", "Книга не найдена.")
        else:
            messagebox.showwarning("Ошибка", "Пожалуйста, введите что-то.")

    def close(self):
        self.db.close()


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()
    app.close() 