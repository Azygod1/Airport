import tkinter as tk
from tkinter import ttk, messagebox, HORIZONTAL
import sqlite3
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from tkinter import PhotoImage
import subprocess
import platform
import os

class AirportApp:
    def __init__(self, root, conn, user_type="admin"):
        self.root = root
        self.root.title("Аэропорт")
        self.root.state('zoomed')
        self.root.iconbitmap(default="icon.ico")

        self.conn = conn
        self.cursor = self.conn.cursor()

        self.tables = self.get_table_names()

        self.create_tabs(user_type)

        ttk.Style().configure("Green.TButton", foreground="black", background="red")
        ttk.Style().configure("Red.TButton", foreground="black", background="red")
        ttk.Style().configure("Blue.TButton", foreground="black", background="red")
        ttk.Style().configure("Blue.TFrame", background="black")
        ttk.Style().configure("TButton", width=3, foreground="black", background="red")
        ttk.Style().configure("TNotebook.Tab", padding=[20, 8], font=('Times New Roman', 13), background='#FF5733')
        ttk.Style().configure("Custom.Treeview.Heading", font=('Times New Roman', 11, 'bold'))

    def refresh_table_data(self, tree, table_name):
        for item in tree.get_children():
            tree.delete(item)

        self.cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = self.cursor.fetchall()

        for row in rows:
            tree.insert("", tk.END, values=row)

    def get_table_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()

        table_names = [table[0] for table in tables if table[0] != "sqlite_sequence"]

        return table_names

    def save_changes_to_database(self):
        self.conn.commit()
        messagebox.showinfo("Сохранение", "Изменения успешно сохранены в базе данных.")

    def create_tabs(self, user_type):
        tab_control = ttk.Notebook(self.root, style="TNotebook")

        if user_type == "seller":
            self.tables = ["Рейсы"]
        elif user_type == "admin":
            self.tables = self.get_table_names()

        for table in self.tables:
            tab = ttk.Frame(tab_control)
            tab_control.add(tab, text=table)
            self.display_table_data(tab, table, user_type)

        tab_control.pack(expand=1, fill="both")

    def display_table_data(self, tab, table_name, user_type):
        for widget in tab.winfo_children():
            widget.destroy()
            self.root.iconbitmap(default="icon.ico")

        image_path_top = "air2 для админа.png"
        img_top = tk.PhotoImage(file=image_path_top)

        img_label_top = tk.Label(tab, image=img_top)
        img_label_top.image = img_top

        img_label_top.pack()

        self.cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = self.cursor.fetchall()

        headers = [description[0] for description in self.cursor.description]

        frame_above_table = ttk.Frame(tab)
        frame_above_table.pack(side=tk.TOP, pady=0)

        buttons_frame = ttk.Frame(frame_above_table)
        buttons_frame.grid(row=0, column=1, sticky='ne')

        if user_type == "admin":
            edit_image = PhotoImage(file="Редактировать.png")
            edit_button = ttk.Button(buttons_frame, text="",
                                     command=lambda: self.edit_record(tree, table_name),
                                     style="Blue.TButton", image=edit_image, compound=tk.LEFT)
            edit_button.image = edit_image
            edit_button.grid(row=0, column=0, padx=3, sticky='ne')

            edit_label = ttk.Label(buttons_frame, text="Изменить", font=('Times New Roman', 11))
            edit_label.grid(row=1, column=0, padx=3, sticky='ne')

        if user_type == "admin":
            delete_image = PhotoImage(file="Удалить.png")
            delete_button = ttk.Button(buttons_frame, text="",
                                       command=lambda: self.delete_selected_row(tree, table_name),
                                       style="Red.TButton", image=delete_image, compound=tk.LEFT)
            delete_button.image = delete_image
            delete_button.grid(row=0, column=1, padx=3, sticky='ne')

            delete_label = tk.Label(buttons_frame, text="Удалить", font=('Times New Roman', 11))
            delete_label.grid(row=1, column=1, padx=3, sticky='ne')

        if user_type == "admin":
            add_image = PhotoImage(file="Добавить запись.png")
            add_button = ttk.Button(buttons_frame, text="",
                                    command=lambda: self.add_record(tree, table_name),
                                    style="Green.TButton", image=add_image, compound=tk.LEFT)
            add_button.image = add_image
            add_button.grid(row=0, column=2, padx=3, sticky='ne')

            add_label = ttk.Label(buttons_frame, text="Добавить", font=('Times New Roman', 11))
            add_label.grid(row=1, column=2, padx=3, sticky='ne')

        frame = ttk.Frame(tab, borderwidth=15, relief="solid", style="Blue.TFrame")
        frame.pack(expand=1, fill="both")

        image_path = "air2.png"
        img = tk.PhotoImage(file=image_path)

        img_label = tk.Label(tab, image=img)
        img_label.image = img

        img_label.pack()

        style = ttk.Style()
        style.configure("Treeview.Heading", anchor="center")
        style.configure("Treeview", rowheight=25, font=('Times New Roman', 11), cellwidth=50)

        tree = ttk.Treeview(frame, columns=headers, show="headings", style="Custom.Treeview")

        for header in headers:
            tree.heading(header, text=header)
            tree.column(header, anchor="center")

        for row in rows:
            tree.insert("", tk.END, values=row)

        tree.pack(expand=1, fill="both")

        horizontal_scrollbar_frame = ttk.Frame(tab)
        horizontal_scrollbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        horizontal_scrollbar = ttk.Scrollbar(horizontal_scrollbar_frame, orient=HORIZONTAL, command=tree.xview)
        horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        tree.configure(xscrollcommand=horizontal_scrollbar.set)

    def edit_record(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            return

        selected_data = tree.item(selected_item)['values']

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Редактирование записи")

        entry_vars = []
        for i, column_name in enumerate(tree['columns']):
            ttk.Label(edit_window, text=column_name).grid(row=i, column=0, padx=5, pady=5)
            entry_var = tk.StringVar(value=selected_data[i])
            entry = ttk.Entry(edit_window, textvariable=entry_var)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry_vars.append(entry_var)

        def save_changes():
            [var.get() for var in entry_vars]
            self.save_changes(tree, table_name, selected_item, edit_window)

        save_image = PhotoImage(file="Сохранить.png")
        save_button = ttk.Button(edit_window, text="",
                                     command=save_changes, style="Green.TButton", image=save_image, compound=tk.LEFT)
        save_button.image = save_image
        save_button.grid(row=len(tree['columns']), columnspan=2, pady=10)

    def add_record(self, tree, table_name):
        add_window = tk.Toplevel(self.root)
        add_window.title("Добавление записи")

        entry_vars = []
        for i, column_name in enumerate(tree['columns']):
            ttk.Label(add_window, text=column_name).grid(row=i, column=0, padx=5, pady=5)
            entry_var = tk.StringVar(value="")
            entry = ttk.Entry(add_window, textvariable=entry_var)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry_vars.append(entry_var)

        def save_record():
            new_data = [var.get() for var in entry_vars]
            self.insert_record(table_name, new_data, tree, add_window)

        save_image = PhotoImage(file="Сохранить.png")
        save_button = ttk.Button(add_window, text="",
                                 command=save_record, style="Green.TButton", image=save_image, compound=tk.LEFT)
        save_button.image = save_image
        save_button.grid(row=len(tree['columns']), columnspan=2, pady=10)

    def delete_selected_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            return

        values = tree.item(selected_item)['values']

        primary_key = self.get_primary_key(table_name)
        if primary_key:
            query = f'DELETE FROM [{table_name}] WHERE "{primary_key}" = ?'

            try:
                self.cursor.execute(query, (values[0],))
            except sqlite3.Error as e:
                print("Ошибка SQLite:", e)

            self.conn.commit()
            tree.delete(selected_item)

    def get_primary_key(self, table_name):
        self.cursor.execute(f"PRAGMA table_info([{table_name}])")
        columns_info = self.cursor.fetchall()

        for column in columns_info:
            if column[5]:
                return column[1]

    def insert_record(self, table_name, new_data, tree, add_window):
        insert_query = f"INSERT INTO {table_name} VALUES ({', '.join(['?' for _ in tree['columns']])})"

        self.cursor.execute(insert_query, new_data)

        self.conn.commit()

        tree.insert("", tk.END, values=new_data)

        add_window.destroy()

    def save_changes(self, tree, table_name, selected_item, edit_window):
        new_values = [entry.get() for entry in edit_window.winfo_children() if isinstance(entry, tk.Entry)]

        primary_key = self.get_primary_key(table_name)
        if primary_key:
            columns_quoted = [f'"{column}"' for column in tree["columns"]]
            query = f'UPDATE [{table_name}] SET {", ".join(f"{column} = ?" for column in columns_quoted)} WHERE "{primary_key}" = ? '

            try:
                self.cursor.execute(query, (*new_values, new_values[0]))
            except sqlite3.Error as e:
                print("Ошибка SQLite:", e)

            self.conn.commit()
            tree.item(selected_item, values=new_values)

        edit_window.destroy()

class SellerApp(AirportApp):
    def __init__(self, root, conn):
        super().__init__(root, conn, user_type="seller")
        self.root.iconbitmap(default="icon.ico")

    def clear_search_fields(self, departure_entry, destination_entry, departure_date_entry, tree, table_name, user_type,
                            tab):
        departure_entry.delete(0, tk.END)
        destination_entry.delete(0, tk.END)
        departure_date_entry.delete(0, tk.END)
        departure_date_entry.set_date(None)

        self.display_table_data(tab, table_name, user_type, tree)

    def display_table_data(self, tab, table_name, user_type, tree=None):
        for widget in tab.winfo_children():
            widget.destroy()

        image_path_top = "air2 поиск рейсов.png"
        img_top = tk.PhotoImage(file=image_path_top)

        img_label_top = tk.Label(tab, image=img_top)
        img_label_top.image = img_top

        img_label_top.pack()

        search_frame = ttk.Frame(tab)
        search_frame.pack(side=tk.TOP, pady=1)

        departure_label = ttk.Label(search_frame, text="Пункт вылета:", font=('Times New Roman', 13))
        departure_label.grid(row=0, column=0, padx=5, pady=1)

        departure_entry = ttk.Entry(search_frame)
        departure_entry.grid(row=0, column=1, padx=5, pady=1)

        destination_label = ttk.Label(search_frame, text="Пункт прибытия:", font=('Times New Roman', 13))
        destination_label.grid(row=0, column=2, padx=5, pady=1)

        destination_entry = ttk.Entry(search_frame)
        destination_entry.grid(row=0, column=3, padx=5, pady=1)

        departure_date_label = ttk.Label(search_frame, text="Дата вылета:", font=('Times New Roman', 13))
        departure_date_label.grid(row=0, column=4, padx=5, pady=1)

        departure_date_entry = DateEntry(search_frame, date_pattern="dd.MM.yyyy", locale="ru_RU")
        departure_date_entry.grid(row=0, column=5, padx=5, pady=1)

        buttons_frame_bottom = ttk.Frame(tab)
        buttons_frame_bottom.pack(side=tk.TOP, pady=1)

        search_image = PhotoImage(file="Найти.png")
        search_button = ttk.Button(search_frame,
                                   command=lambda: self.search_records(tree, table_name, departure_entry.get(),
                                                                       destination_entry.get(),
                                                                       departure_date_entry.get()),
                                   image=search_image, compound=tk.LEFT)
        search_button.image = search_image
        search_button.grid(row=0, column=6, padx=5, pady=1)

        additional_text_search = ttk.Label(search_frame, text="Найти", font=('Times New Roman', 10))
        additional_text_search.grid(row=1, column=6, padx=5, pady=1)

        clear_image = PhotoImage(file="Очистить.png")
        clear_button = ttk.Button(search_frame,
                                  command=lambda: self.clear_search_fields(
                                      departure_entry, destination_entry, departure_date_entry, tree, table_name,
                                      user_type, tab), image=clear_image, compound=tk.LEFT)
        clear_button.image = clear_image
        clear_button.grid(row=0, column=7, padx=5, pady=1)

        additional_text_clear = ttk.Label(search_frame, text="Очистить", font=('Times New Roman', 10))
        additional_text_clear.grid(row=1, column=7, padx=5, pady=1)

        tickets_image = PhotoImage(file="Билеты.png")
        tickets_button = ttk.Button(search_frame,
                                    command=lambda: self.open_tickets_folder(),
                                    image=tickets_image,
                                    compound=tk.LEFT)
        tickets_button.image = tickets_image
        tickets_button.grid(row=0, column=8, padx=5, pady=1)

        additional_text_tickets = ttk.Label(search_frame, text="Билеты", font=('Times New Roman', 10))
        additional_text_tickets.grid(row=1, column=8, padx=5, pady=1)

        self.cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = self.cursor.fetchall()

        headers = [description[0] for description in self.cursor.description]

        frame = ttk.Frame(tab, borderwidth=15, relief="solid", style="Blue.TFrame")
        frame.pack(expand=1, fill="both")

        image_path = "air2.png"
        img = tk.PhotoImage(file=image_path)

        img_label = tk.Label(tab, image=img)
        img_label.image = img

        img_label.pack()

        style = ttk.Style()
        style.configure("Treeview.Heading", anchor="center")
        style.configure("Treeview", rowheight=25, font=('Times New Roman', 11), cellwidth=50)

        tree = ttk.Treeview(frame, columns=headers, show="headings", style="Custom.Treeview")

        for header in headers:
            tree.heading(header, text=header)
            tree.column(header, anchor="center")

        for row in rows:
            tree.insert("", tk.END, values=row)

        tree.pack(expand=1, fill="both")

        purchase_frame = ttk.Frame(tab)
        purchase_frame.pack(side=tk.TOP, pady=1)

        purchase_image = PhotoImage(file="Приобретение билета.png")

        purchase_button = ttk.Button(purchase_frame,
                                     command=lambda: self.purchase_ticket(tree),
                                     image=purchase_image,
                                     compound=tk.LEFT)
        purchase_button.image = purchase_image
        purchase_button.pack()

        additional_text = ttk.Label(purchase_frame, text="Оформление билета", font=('Times New Roman', 10))
        additional_text.pack()

        horizontal_scrollbar_frame = ttk.Frame(tab)
        horizontal_scrollbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        horizontal_scrollbar = ttk.Scrollbar(horizontal_scrollbar_frame, orient=HORIZONTAL, command=tree.xview)
        horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        tree.configure(xscrollcommand=horizontal_scrollbar.set)

    def open_tickets_folder(self):
        folder_path = "Билеты"

        if platform.system() == "Windows":
            subprocess.Popen(["explorer", folder_path])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder_path])
        elif platform.system() == "Linux":
            subprocess.Popen(["xdg-open", folder_path])

    def get_selected_row_from_table_reysy(self, tree):
        try:
            selected_item = tree.selection()[0]
            selected_row = tree.item(selected_item, 'values')
            return selected_row
        except IndexError:
            return None

    def purchase_ticket(self, tree):
        selected_row_reysy = self.get_selected_row_from_table_reysy(tree)

        if selected_row_reysy:
            add_window = tk.Toplevel(self.root)
            add_window.title("Приобретение билета")
            add_window.resizable(False, False)
            add_window.geometry("300x300+615+290")

            entry_vars = []
            labels = ['Фамилия', 'Имя', 'Отчество', 'Номер телефона', 'Эл. почта', 'Серия и номер паспорта', 'Дата покупки билета']
            for i, label in enumerate(labels):
                ttk.Label(add_window, text=label).grid(row=i, column=0, padx=5, pady=5)

                entry_var = tk.StringVar(value="")
                validate_cmd = (add_window.register(self.validate_input), '%P', '%S', label)
                if label == 'Дата покупки билета':
                    entry = DateEntry(add_window, textvariable=entry_var, date_pattern="dd.mm.yyyy", locale='ru_RU')
                else:
                    entry = ttk.Entry(add_window, textvariable=entry_var, validate="key", validatecommand=validate_cmd)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entry_vars.append(entry_var)

            save_image = tk.PhotoImage(file="Печать билета.png")

            save_button = ttk.Button(add_window, text="",
                                     command=lambda: self.save_passenger_record(entry_vars, add_window, tree),
                                     style="Green.TButton", image=save_image, compound=tk.LEFT)
            save_button.image = save_image
            save_button.grid(row=len(labels), columnspan=2, pady=1)

            additional_text_save = ttk.Label(add_window, text="Печать билета")
            additional_text_save.grid(row=len(labels) + 1, columnspan=2, pady=5)
        else:
            messagebox.showwarning("Выберите рейс", "Нужно выбрать рейс из представленных")

    def validate_input(self, new_text, char, label):
        if label == 'Номер телефона':
            return char.isdigit() and len(new_text) <= 11
        elif label == 'Серия и номер паспорта':
            return (char.isdigit() or char.isspace() or char == '') and len(new_text.replace(' ', '')) <= 10
        elif label == 'Фамилия':
            return (char.isalpha() or char.isspace() or char == '') and len(new_text) <= 40
        elif label == 'Имя':
            return (char.isalpha() or char.isspace() or char == '') and len(new_text) <= 40
        elif label == 'Отчество':
            return (char.isalpha() or char.isspace() or char == '') and len(new_text) <= 40
        elif label == 'Эл. почта':
            return len(new_text) <= 40
        else:
            return True

    def create_pdf(self, passenger_data, ticket_number, reysy_data):
        pdf_folder = "Билеты"

        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)

        pdf_filename = os.path.join(pdf_folder, f"Билет_{ticket_number}.pdf")

        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        pdf = canvas.Canvas(pdf_filename, pagesize=letter)
        pdf.setFont("Arial", 12)

        image_path = "для билета.png"
        pdf.drawImage(image_path, -170, 745)

        image_path1 = "для билета2.png"
        pdf.drawImage(image_path1, -170, 515)

        pdf.drawString(75, 720, "ИНФОРМАЦИЯ О ПАССАЖИРЕ")
        pdf.drawString(75, 700, f"Фамилия: {passenger_data[0]}")
        pdf.drawString(75, 680, f"Имя: {passenger_data[1]}")
        pdf.drawString(75, 660, f"Отчество: {passenger_data[2]}")
        pdf.drawString(75, 640, f"Номер телефона: {passenger_data[3]}")
        pdf.drawString(75, 620, f"Эл. Почта: {passenger_data[4]}")
        pdf.drawString(75, 600, f"Серия и номер паспорта: {passenger_data[5]}")
        pdf.drawString(75, 580, f"Дата покупки билета: {passenger_data[6]}")
        pdf.drawString(75, 560, f"Номер билета: {ticket_number}")

        pdf.drawString(375, 720, "ИНФОРМАЦИЯ О РЕЙСЕ")
        pdf.drawString(375, 700, f"Номер рейса: {reysy_data[0]}")
        pdf.drawString(375, 680, f"Пункт вылета: {reysy_data[1]}")
        pdf.drawString(375, 660, f"Пункт прибытия: {reysy_data[2]}")
        pdf.drawString(375, 640, f"Дата вылета: {reysy_data[3]}")
        pdf.drawString(375, 620, f"Время вылета: {reysy_data[4]}")
        pdf.drawString(375, 600, f"Дата прибытия: {reysy_data[5]}")
        pdf.drawString(375, 580, f"Время прибытия: {reysy_data[6]}")
        pdf.drawString(375, 560, f"Регистрационный номер самолета: {reysy_data[7]}")

        pdf.save()

    def save_passenger_record(self, entry_vars, add_window, tree):
        try:
            passenger_data = [var.get() for var in entry_vars]

            if all(passenger_data):
                passenger_query = 'INSERT INTO "Пассажиры" ("Фамилия", "Имя", "Отчество", "Номер телефона", "Почта", "Серия и номер паспорта", "Дата покупки билета", "Номер билета") VALUES (?, ?, ?, ?, ?, ?, ?, ?)'

                ticket_query = 'INSERT INTO "Билеты" ("Табельный номер продавца") VALUES (?)'
                self.cursor.execute(ticket_query, (1,))
                self.conn.commit()

                ticket_number = self.cursor.lastrowid

                self.cursor.execute(passenger_query, tuple(passenger_data + [ticket_number]))
                self.conn.commit()

                selected_row_reysy = self.get_selected_row_from_table_reysy(tree)
                if selected_row_reysy:
                    reysy_data = selected_row_reysy

                    passengers_on_flights_query = 'INSERT INTO "Пассажиры_на_рейсах" ("Номер пассажира", "Номер рейса") VALUES (?, ?)'
                    self.cursor.execute(passengers_on_flights_query, (ticket_number, reysy_data[0]))
                    self.conn.commit()

                    self.create_pdf(passenger_data, ticket_number, reysy_data)

                    def close_window_and_show_message():
                        add_window.destroy()
                        messagebox.showinfo("Билет сохранен", "Билет сохранен в папке 'Билеты'")

                    add_window.after(50, close_window_and_show_message)
                else:
                    messagebox.showwarning("Выберите рейс", "Выберите рейс из таблицы 'Рейсы'")
                    add_window.destroy()

                for var in entry_vars:
                    var.set("")
            else:
                messagebox.showwarning("Пустые поля", "Заполните все поля ввода")
                add_window.destroy()
        except sqlite3.Error as e:
            print("Ошибка SQLite:", e)

    def search_records(self, tree, table_name, departure, destination, departure_date):
        for item in tree.get_children():
            tree.delete(item)

        query = f"SELECT * FROM [{table_name}] WHERE [Пункт вылета] LIKE ? AND [Пункт прибытия] LIKE ? " \
                f"AND [Дата вылета] LIKE ?"

        params = [f"%{departure}%", f"%{destination}%", f"%{departure_date}%"]

        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            for row in rows:
                tree.insert("", tk.END, values=row)
        except sqlite3.Error as e:
            print("Ошибка SQLite:", e)

def on_closing_app(app, conn, app_root):
    app.save_changes_to_database()
    conn.close()
    app_root.destroy()

def initialize_admin_app():
    conn = sqlite3.connect(r'C:\Users\Nikita\PycharmProjects\pythonProject2\airport_database.db')
    app_root = tk.Tk()
    app = AirportApp(app_root, conn)
    app_root.protocol("WM_DELETE_WINDOW", lambda: on_closing_app(app, conn, app_root))
    app_root.mainloop()

def initialize_seller_app():
    conn = sqlite3.connect(r'C:\Users\Nikita\PycharmProjects\pythonProject2\airport_database.db')
    app_root = tk.Tk()
    app = SellerApp(app_root, conn)
    app_root.protocol("WM_DELETE_WINDOW", lambda: on_closing_app(app, conn, app_root))
    app_root.mainloop()

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Вход")
        self.root.geometry('200x180+670+290')
        self.root.resizable(False, False)
        self.root.iconbitmap(default="icon.ico")

        self.canvas = tk.Canvas(root, width=200, height=180)
        self.canvas.pack()

        self.bg_image = tk.PhotoImage(file="air.png")

        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        self.label_authorization = tk.Label(self.canvas, text="Авторизация", font=("Helvetica", 10, "bold"), bg="white")
        self.label_frame = tk.LabelFrame(self.canvas, text="Введите учетные данные", font=("Helvetica", 10, "bold"),
                                         bg="white")

        self.label_username = tk.Label(self.label_frame, text="Логин:")
        self.label_password = tk.Label(self.label_frame, text="Пароль:")

        self.entry_username = tk.Entry(self.label_frame)
        self.entry_password = tk.Entry(self.label_frame, show="*")

        self.label_authorization.grid(row=0, column=1, pady=5, sticky=tk.NW)
        self.label_frame.grid(row=1, column=1, pady=10)

        self.label_username.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.entry_username.grid(row=0, column=1, padx=5, pady=5)
        self.label_password.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        self.login_button = tk.Button(self.canvas, text="Войти", command=self.login, font=("Helvetica", 10, "bold"))
        self.login_button.grid(row=2, column=1, pady=10)

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

    def login(self):
        username_admin = "1"
        password_admin = "1"

        username = self.entry_username.get()
        password = self.entry_password.get()

        if username == username_admin and password == password_admin:
            self.root.destroy()
            initialize_admin_app()
        else:
            conn = sqlite3.connect(r'C:\Users\Nikita\PycharmProjects\pythonProject2\airport_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT Логин, Пароль FROM Продавцы WHERE Логин=? AND Пароль=?", (username, password))
            seller_credentials = cursor.fetchone()
            conn.close()

            if seller_credentials:
                self.root.destroy()
                initialize_seller_app()
            else:
                messagebox.showerror("Ошибка входа", "Неверный логин или пароль")

if __name__ == "__main__":
    root = tk.Tk()
    login_window = LoginWindow(root)
    root.mainloop()
