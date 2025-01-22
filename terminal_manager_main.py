import sqlite3
import hashlib
import time
import os
import subprocess
from progress.bar import IncrementalBar
from confs import config

txt = """Итак, вам как пользователю уровня 1 доступны следующие действия:
------------------------
1 - Добавить книгу в базу данных
2 - Вывести весь список книг
3 - Получить книгу по названию или id из базы данных
4 - Выйти из приложения"""

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

    @staticmethod # staticmethod тут используется потому, что технически метод register не относится к классу User, мы подчеркиваем логическую связ
    def register(db, nickname, password):
        user = User(nickname, password)
        try:
            db.insert_user(user.nickname, user.password) # insert_user по сути за регистрацию и отвечает
            print("Выполняю инициализацию...")
            time.sleep(1)
            config.prog_bar("Создание пользователя: ") # эта штука уже чисто косметическая
        except sqlite3.IntegrityError:
            print("Пользователь с таким именем уже существует.")

    @staticmethod
    def login(db, nickname, password):
        user = User(nickname, password)
        return db.get_user(user.nickname, user.password)


class LibraryApp:
    def __init__(self):
        self.db = Database("books.db")
        self.user_id = None
        self.nickname = None

    def start(self):
        start = input("Привет!\nСожалею, но моя система пока не может никого запомнить..\nПоэтому предлагаю тебе войти - 1, или зарегистрироваться - 0: ")
        while start not in ("0", "1"):
            start = input("Ты кажется не понял, нужно ввести 1 или 0:")
        if start == "0":
            self.register_user()
        elif start == "1":
            self.login_user()
        if self.nickname:
            print(txt)
            self.user_menu()

    def register_user(self):
        username = input("Введите имя пользователя: ")
        password = input("Введите пароль: ")
        one_more_time = input("Введите пароль еще раз: ")

        if password == one_more_time:
            User.register(self.db, username, password)


    def login_user(self):
        username = input("Введите имя пользователя: ")
        password = input("Введите пароль: ")

        result = User.login(self.db, username, password)
        while not result:
            print("Что-то пошло не так, введи 0 или введи данные еще раз")
            username = input("Введите имя пользователя: ")
            if username == "0":
                quit()
                break
            password = input("Введите пароль: ")
            result = User.login(self.db, username, password)
        
        self.user_id = result[0]
        self.nickname = result[1]
        print("Выполняю вход...")
        time.sleep(0.2)
        print("Привет,", self.nickname + "!")
            
    def user_menu(self):
        what_to_do = "."
        while what_to_do != "1" or what_to_do != "2" or what_to_do != "3" or what_to_do != "4" or what_to_do != "5":
            what_to_do = input("------------------------\n\n<Главное меню> Введите число от 1 до 5: ")
            if what_to_do == "1":
                self.add_book()
            elif what_to_do == "2":
                self.show_books()
                break
            elif what_to_do == "3":
                self.get_book()
            elif what_to_do == "4":
                exit()
            elif what_to_do == "5":
                print(txt)

        
    def add_book(self):
        print("Отлично, вводите нужную информацию ниже")
        book_title = input("Введите название книги: ")
        if book_title == "0":
            self.user_menu()
        book_path = input("Введите путь к файлу: ")
    
        while os.path.exists(book_path) == False:
            print("Прошу прощения, но такой книги нет, попробуй ввести еще раз, либо введи 0, чтобы вернуться в меню")
            book_title = input("Введите название книги: ")
            if book_title == "0":
                self.user_menu()
                break
            book_path = input("Введите путь к файлу: ")

        if os.path.exists(book_path):
            self.db.insert_book(book_title, book_path, self.user_id)
            print("Добавляю...")
            time.sleep(0.2)
            config.prog_bar("Обновление базы данных: ")
            time.sleep(0.2)
            print("Книга", book_title, "была успешно добавлена по пути:", book_path)
        
    def show_books(self):
        books = self.db.get_books(self.user_id) # получаем все книги
        print("\n-----------------------")
        for row in books:
            print(f"{row[0]}. {row[1]}")

        self.user_menu()

    def get_book(self):

        books = self.db.get_books(self.user_id)
        print("\n-------------------------")
        for row in books:
            print(f"{row[0]}. {row[1]}")
        print("--------------------------\n")

        request = input("Введите название или id: ")
        result = self.db.find_book_by_id(request, self.user_id)
        while not result:
            print("Такого файла нет:(")
            request = input("Попробуйте указать путь еще раз, либо введите 0, чтобы вернуться в меню: ")
            if request == "0":
                self.user_menu()
               

        subprocess.run(["okular", result[2]])
            

    def close(self):
        self.db.close()


if __name__ == "__main__":
    app = LibraryApp()
    app.start()
    app.close()
