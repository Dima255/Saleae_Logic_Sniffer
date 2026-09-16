import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import csv
import os
import json
from datetime import datetime
from collections import Counter
import threading
import subprocess
import sys

class CommandParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Saleae Logic 2 - Парсинг команд")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Путь к файлу настроек
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parser_settings.json")
        
        # Переменные
        self.input_file = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.end_char = tk.StringVar(value="\\r")
        self.filter_pattern = tk.StringVar()
        self.delimiter = tk.StringVar(value="Запятая (,)")
        self.custom_delimiter = tk.StringVar(value="|")
        self.encoding = tk.StringVar(value="UTF-8 с BOM (Excel)")
        self.save_mode = tk.StringVar(value="Рядом с исходным")  # "Рядом с исходным" или "Вручную"
        self.commands = []
        self.filtered_commands = []
        self.last_saved_files = []  # Список последних сохраненных файлов
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка настроек
        self.load_settings()
        
    def create_widgets(self):
        # Основной контейнер с отступами
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === Меню для работы с настройками ===
        menu_frame = ttk.Frame(main_frame)
        menu_frame.pack(fill=tk.X, pady=(0, 5))
        
        settings_menu_btn = ttk.Menubutton(menu_frame, text="⚙️ Настройки", direction='below')
        settings_menu_btn.pack(side=tk.LEFT, padx=2)
        
        settings_menu = tk.Menu(settings_menu_btn, tearoff=0)
        settings_menu_btn.config(menu=settings_menu)
        
        settings_menu.add_command(label="💾 Сохранить настройки в файл...", command=self.save_settings_to_file)
        settings_menu.add_command(label="📂 Загрузить настройки из файла...", command=self.load_settings_from_file)
        settings_menu.add_separator()
        settings_menu.add_command(label="🔄 Сбросить настройки по умолчанию", command=self.reset_settings)
        
        # Информация о последних файлах
        self.last_files_label = ttk.Label(menu_frame, text="", foreground="gray")
        self.last_files_label.pack(side=tk.RIGHT, padx=5)
        
        # === Блок выбора файла ===
        file_frame = ttk.LabelFrame(main_frame, text="📂 Исходный файл", padding="5")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(file_frame, textvariable=self.input_file, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Выбрать файл", command=self.select_input_file).pack(side=tk.RIGHT, padx=5)
        
        # === Блок выбора папки ===
        folder_frame = ttk.LabelFrame(main_frame, text="📁 Папка для сохранения", padding="5")
        folder_frame.pack(fill=tk.X, pady=5)
        
        # Режим сохранения
        save_mode_frame = ttk.Frame(folder_frame)
        save_mode_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(save_mode_frame, text="Режим сохранения:").pack(side=tk.LEFT, padx=5)
        
        save_modes = ["Рядом с исходным", "Вручную"]
        self.save_mode_combo = ttk.Combobox(save_mode_frame, values=save_modes, textvariable=self.save_mode, width=20)
        self.save_mode_combo.pack(side=tk.LEFT, padx=5)
        self.save_mode_combo.bind('<<ComboboxSelected>>', self.on_save_mode_change)
        
        ttk.Label(save_mode_frame, text="(создается папка Res рядом с исходным файлом)", foreground="blue").pack(side=tk.LEFT, padx=5)
        
        # Поле выбора папки
        folder_select_frame = ttk.Frame(folder_frame)
        folder_select_frame.pack(fill=tk.X, pady=2)
        
        self.folder_entry = ttk.Entry(folder_select_frame, textvariable=self.output_folder, width=60, state='readonly')
        self.folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.folder_button = ttk.Button(folder_select_frame, text="Выбрать папку", command=self.select_output_folder)
        self.folder_button.pack(side=tk.RIGHT, padx=5)
        
        # Обновляем состояние в зависимости от режима
        self.update_folder_state()
        
        # === Блок настроек ===
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Настройки парсинга", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Строка окончания
        end_frame = ttk.Frame(settings_frame)
        end_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(end_frame, text="Символ окончания команды:").pack(side=tk.LEFT, padx=5)
        
        end_chars = ["\\r", "\\n", "\\r\\n", "\\n\\r", "\\t", ";", ":", ",", "Пользовательский"]
        self.end_combo = ttk.Combobox(end_frame, values=end_chars, textvariable=self.end_char, width=15)
        self.end_combo.pack(side=tk.LEFT, padx=5)
        self.end_combo.bind('<<ComboboxSelected>>', self.on_end_char_change)
        
        self.custom_end_entry = ttk.Entry(end_frame, width=10, state='disabled')
        self.custom_end_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(end_frame, text="(для пользовательского)").pack(side=tk.LEFT, padx=2)
        
        # Разделитель для экспорта
        delim_frame = ttk.Frame(settings_frame)
        delim_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(delim_frame, text="Разделитель для экспорта:").pack(side=tk.LEFT, padx=5)
        
        delimiters = [
            "Запятая (,)",
            "Точка с запятой (;)(Excel)",
            "Табуляция (\\t)",
            "Вертикальная черта (|)",
            "Двоеточие (:)",
            "Пробел",
            "Пользовательский"
        ]
        self.delim_combo = ttk.Combobox(delim_frame, values=delimiters, textvariable=self.delimiter, width=20)
        self.delim_combo.pack(side=tk.LEFT, padx=5)
        self.delim_combo.bind('<<ComboboxSelected>>', self.on_delimiter_change)
        
        self.custom_delim_entry = ttk.Entry(delim_frame, width=5, state='disabled')
        self.custom_delim_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(delim_frame, text="(для пользовательского)").pack(side=tk.LEFT, padx=2)
        
        # Кодировка для экспорта
        encoding_frame = ttk.Frame(settings_frame)
        encoding_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(encoding_frame, text="Кодировка для Excel:").pack(side=tk.LEFT, padx=5)
        
        encodings = [
            "UTF-8 с BOM (Excel)",
            "UTF-8 без BOM",
            "ANSI (Windows-1251)",
            "UTF-16LE"
        ]
        self.encoding_combo = ttk.Combobox(encoding_frame, values=encodings, textvariable=self.encoding, width=20)
        self.encoding_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(encoding_frame, text="(UTF-8 с BOM рекомендуется для Excel)", foreground="blue").pack(side=tk.LEFT, padx=5)
        
        # Фильтр
        filter_frame = ttk.Frame(settings_frame)
        filter_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(filter_frame, text="Фильтр команд (оставить пустым для отключения):").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filter_frame, textvariable=self.filter_pattern, width=20).pack(side=tk.LEFT, padx=5)
        
        # Информация
        info_label = ttk.Label(settings_frame, text="ℹ️ Для \\r\\n разделение происходит по \\r, а \\n игнорируется", foreground="blue")
        info_label.pack(pady=2)
        
        # === Кнопки действий ===
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="▶️ Начать обработку", command=self.start_parsing, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📊 Показать статистику", command=self.show_statistics).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📂 Открыть результаты", command=self.open_results_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🗑️ Очистить лог", command=self.clear_log).pack(side=tk.RIGHT, padx=5)
        
        # === Лог вывода ===
        log_frame = ttk.LabelFrame(main_frame, text="📋 Результаты", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Courier New", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Настройка стилей
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
        # Статус бар
        self.status_label = ttk.Label(main_frame, text="Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)
    
    def on_save_mode_change(self, event):
        """Обработка изменения режима сохранения"""
        self.update_folder_state()
        self.save_settings()
    
    def update_folder_state(self):
        """Обновление состояния поля выбора папки"""
        if self.save_mode.get() == "Рядом с исходным":
            self.folder_entry.config(state='readonly')
            self.folder_button.config(state='disabled')
            # Автоматически обновляем путь
            self.update_default_folder()
        else:
            self.folder_entry.config(state='readonly')
            self.folder_button.config(state='normal')
    
    def update_default_folder(self):
        """Обновление пути к папке по умолчанию (рядом с исходным файлом)"""
        if self.save_mode.get() == "Рядом с исходным" and self.input_file.get():
            input_dir = os.path.dirname(self.input_file.get())
            if input_dir:
                default_folder = os.path.join(input_dir, "Res")
                self.output_folder.set(default_folder)
                self.log_message(f"📁 Папка сохранения: {default_folder}")
    
    def get_output_folder(self):
        """Получение папки для сохранения"""
        if self.save_mode.get() == "Рядом с исходным":
            self.update_default_folder()
        return self.output_folder.get()
    
    def on_end_char_change(self, event):
        """Обработка выбора символа окончания"""
        if self.end_char.get() == "Пользовательский":
            self.custom_end_entry.config(state='normal')
            self.custom_end_entry.focus()
        else:
            self.custom_end_entry.config(state='disabled')
            self.custom_end_entry.delete(0, tk.END)
        self.save_settings()
    
    def on_delimiter_change(self, event):
        """Обработка выбора разделителя"""
        if self.delimiter.get() == "Пользовательский":
            self.custom_delim_entry.config(state='normal')
            self.custom_delim_entry.focus()
        else:
            self.custom_delim_entry.config(state='disabled')
            self.custom_delim_entry.delete(0, tk.END)
        self.save_settings()
    
    def get_end_char(self):
        """Получение символа окончания"""
        end_char = self.end_char.get()
        if end_char == "Пользовательский":
            return self.custom_end_entry.get()
        return end_char
    
    def get_delimiter(self):
        """Получение разделителя для экспорта"""
        delim = self.delimiter.get()
        if delim == "Пользовательский":
            return self.custom_delim_entry.get()
        
        delim_map = {
            "Запятая (,)": ",",
            "Точка с запятой (;)(Excel)": ";",
            "Табуляция (\\t)": "\t",
            "Вертикальная черта (|)": "|",
            "Двоеточие (:)": ":",
            "Пробел": " "
        }
        return delim_map.get(delim, ",")
    
    def get_encoding(self):
        """Получение кодировки для экспорта"""
        enc = self.encoding.get()
        encoding_map = {
            "UTF-8 с BOM (Excel)": "utf-8-sig",
            "UTF-8 без BOM": "utf-8",
            "ANSI (Windows-1251)": "windows-1251",
            "UTF-16LE": "utf-16le"
        }
        return encoding_map.get(enc, "utf-8-sig")
    
    def get_settings(self):
        """Получение текущих настроек в виде словаря"""
        return {
            "input_file": self.input_file.get(),
            "output_folder": self.output_folder.get(),
            "save_mode": self.save_mode.get(),
            "end_char": self.end_char.get(),
            "custom_end_char": self.custom_end_entry.get(),
            "filter_pattern": self.filter_pattern.get(),
            "delimiter": self.delimiter.get(),
            "custom_delimiter": self.custom_delim_entry.get(),
            "encoding": self.encoding.get()
        }
    
    def load_settings(self):
        """Загрузка настроек из JSON файла"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Восстанавливаем настройки
                if "input_file" in settings and os.path.exists(settings["input_file"]):
                    self.input_file.set(settings["input_file"])
                
                if "output_folder" in settings:
                    self.output_folder.set(settings["output_folder"])
                
                if "save_mode" in settings:
                    self.save_mode.set(settings["save_mode"])
                    self.update_folder_state()
                
                if "end_char" in settings:
                    self.end_char.set(settings["end_char"])
                    if settings["end_char"] == "Пользовательский" and "custom_end_char" in settings:
                        self.custom_end_entry.config(state='normal')
                        self.custom_end_entry.delete(0, tk.END)
                        self.custom_end_entry.insert(0, settings["custom_end_char"])
                
                if "filter_pattern" in settings:
                    self.filter_pattern.set(settings["filter_pattern"])
                
                if "delimiter" in settings:
                    self.delimiter.set(settings["delimiter"])
                    if settings["delimiter"] == "Пользовательский" and "custom_delimiter" in settings:
                        self.custom_delim_entry.config(state='normal')
                        self.custom_delim_entry.delete(0, tk.END)
                        self.custom_delim_entry.insert(0, settings["custom_delimiter"])
                
                if "encoding" in settings:
                    self.encoding.set(settings["encoding"])
                
                # Обновляем путь к папке если режим "Рядом с исходным"
                if self.save_mode.get() == "Рядом с исходным":
                    self.update_default_folder()
                
                self.log_message("✅ Настройки загружены")
            else:
                self.log_message("ℹ️ Файл настроек не найден, используются стандартные")
        except Exception as e:
            self.log_message(f"⚠️ Ошибка загрузки настроек: {e}")
    
    def save_settings(self):
        """Сохранение настроек в JSON файл"""
        try:
            settings = self.get_settings()
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"⚠️ Ошибка сохранения настроек: {e}")
    
    def save_settings_to_file(self):
        """Сохранение настроек в выбранный файл"""
        file_path = filedialog.asksaveasfilename(
            title="Сохранить настройки в файл",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                settings = self.get_settings()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
                self.log_message(f"✅ Настройки сохранены в: {file_path}")
                messagebox.showinfo("Успех", f"Настройки сохранены в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить настройки:\n{e}")
                self.log_message(f"❌ Ошибка сохранения настроек: {e}")
    
    def load_settings_from_file(self):
        """Загрузка настроек из выбранного файла"""
        file_path = filedialog.askopenfilename(
            title="Загрузить настройки из файла",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Применяем настройки
                if "input_file" in settings:
                    self.input_file.set(settings["input_file"])
                
                if "output_folder" in settings:
                    self.output_folder.set(settings["output_folder"])
                
                if "save_mode" in settings:
                    self.save_mode.set(settings["save_mode"])
                    self.update_folder_state()
                
                if "end_char" in settings:
                    self.end_char.set(settings["end_char"])
                    if settings["end_char"] == "Пользовательский" and "custom_end_char" in settings:
                        self.custom_end_entry.config(state='normal')
                        self.custom_end_entry.delete(0, tk.END)
                        self.custom_end_entry.insert(0, settings["custom_end_char"])
                
                if "filter_pattern" in settings:
                    self.filter_pattern.set(settings["filter_pattern"])
                
                if "delimiter" in settings:
                    self.delimiter.set(settings["delimiter"])
                    if settings["delimiter"] == "Пользовательский" and "custom_delimiter" in settings:
                        self.custom_delim_entry.config(state='normal')
                        self.custom_delim_entry.delete(0, tk.END)
                        self.custom_delim_entry.insert(0, settings["custom_delimiter"])
                
                if "encoding" in settings:
                    self.encoding.set(settings["encoding"])
                
                # Обновляем путь к папке если режим "Рядом с исходным"
                if self.save_mode.get() == "Рядом с исходным":
                    self.update_default_folder()
                
                # Сохраняем как текущие настройки
                self.save_settings()
                
                self.log_message(f"✅ Настройки загружены из: {file_path}")
                messagebox.showinfo("Успех", f"Настройки загружены из:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить настройки:\n{e}")
                self.log_message(f"❌ Ошибка загрузки настроек: {e}")
    
    def reset_settings(self):
        """Сброс настроек по умолчанию"""
        if messagebox.askyesno("Подтверждение", "Сбросить все настройки на значения по умолчанию?"):
            self.input_file.set("")
            self.output_folder.set("")
            self.save_mode.set("Рядом с исходным")
            self.end_char.set("\\r")
            self.filter_pattern.set("")
            self.delimiter.set("Запятая (,)")
            self.encoding.set("UTF-8 с BOM (Excel)")
            self.custom_end_entry.config(state='disabled')
            self.custom_end_entry.delete(0, tk.END)
            self.custom_delim_entry.config(state='disabled')
            self.custom_delim_entry.delete(0, tk.END)
            self.update_folder_state()
            self.save_settings()
            self.log_message("🔄 Настройки сброшены на значения по умолчанию")
            messagebox.showinfo("Успех", "Настройки сброшены на значения по умолчанию")
    
    def select_input_file(self):
        """Выбор входного файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл с данными Saleae",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            self.log_message(f"✅ Выбран файл: {file_path}")
            # Обновляем путь сохранения если режим "Рядом с исходным"
            if self.save_mode.get() == "Рядом с исходным":
                self.update_default_folder()
            self.save_settings()
    
    def select_output_folder(self):
        """Выбор папки для сохранения"""
        if self.save_mode.get() == "Вручную":
            folder_path = filedialog.askdirectory(
                title="Выберите папку для сохранения результатов"
            )
            if folder_path:
                self.output_folder.set(folder_path)
                self.log_message(f"✅ Выбрана папка: {folder_path}")
                self.save_settings()
    
    def open_results_folder(self):
        """Открытие папки с результатами"""
        folder_path = self.get_output_folder()
        if not folder_path:
            messagebox.showwarning("Предупреждение", "Папка для сохранения не выбрана!")
            return
        
        # Создаем папку если её нет
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
                self.log_message(f"📁 Создана папка: {folder_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{e}")
                return
        
        try:
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', folder_path])
            else:  # Linux
                subprocess.run(['xdg-open', folder_path])
            self.log_message(f"📂 Открыта папка: {folder_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")
            self.log_message(f"❌ Ошибка открытия папки: {e}")
    
    def log_message(self, message):
        """Добавление сообщения в лог"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def set_status(self, message):
        """Установка статуса"""
        self.status_label.config(text=message)
        self.root.update()
    
    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, tk.END)
        self.commands = []
        self.filtered_commands = []
        self.log_message("🗑️ Лог очищен")
    
    def parse_commands(self, input_file, end_char):
        """Парсинг команд из CSV файла"""
        commands = []
        current_cmd = ""
        start_time = ""
        
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            data_column = None
            time_column = None
            
            for col in reader.fieldnames:
                col_lower = col.lower().strip()
                if 'time' in col_lower or 'timestamp' in col_lower:
                    time_column = col
                elif 'error' not in col_lower and 'parity' not in col_lower and 'framing' not in col_lower:
                    data_column = col
            
            if data_column is None and len(reader.fieldnames) >= 2:
                data_column = reader.fieldnames[1]
            
            if time_column is None and len(reader.fieldnames) >= 1:
                time_column = reader.fieldnames[0]
            
            if data_column is None:
                raise Exception(f"Не найдена колонка с данными! Доступны: {reader.fieldnames}")
            
            self.log_message(f"📋 Используем колонку с данными: '{data_column}'")
            self.log_message(f"📋 Используем колонку с временем: '{time_column}'")
            
            sample_values = []
            temp_reader = csv.DictReader(open(input_file, 'r', encoding='utf-8'))
            for i, row in enumerate(temp_reader):
                if i < 5:
                    sample_values.append(repr(row[data_column]))
            self.log_message(f"🔍 Примеры значений: {', '.join(sample_values)}")
            
            row_count = 0
            for row in reader:
                row_count += 1
                char = row[data_column]
                
                if not char:
                    continue
                
                time_val = row[time_column].strip() if time_column else ""
                
                is_end = False
                
                if end_char == "\\r\\n":
                    if char == '\\r':
                        is_end = True
                    elif char == '\\n':
                        continue
                elif end_char == "\\n\\r":
                    if char == '\\n':
                        is_end = True
                    elif char == '\\r':
                        continue
                else:
                    if char == end_char:
                        is_end = True
                
                if is_end:
                    if current_cmd:
                        commands.append({
                            'time': start_time,
                            'command': current_cmd
                        })
                        current_cmd = ""
                        start_time = ""
                else:
                    if not current_cmd:
                        start_time = time_val
                    current_cmd += char
                
                if row_count % 100 == 0:
                    self.set_status(f"⏳ Обработано {row_count} строк...")
            
            if current_cmd:
                commands.append({
                    'time': start_time,
                    'command': current_cmd
                })
        
        return commands
    
    def start_parsing(self):
        """Запуск парсинга в отдельном потоке"""
        if not self.input_file.get():
            messagebox.showerror("Ошибка", "Выберите входной файл!")
            return
        
        # Проверяем/создаем папку для сохранения
        output_folder = self.get_output_folder()
        if not output_folder:
            messagebox.showerror("Ошибка", "Не удалось определить папку для сохранения!")
            return
        
        # Создаем папку если её нет
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
                self.log_message(f"📁 Создана папка: {output_folder}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{e}")
                return
        
        # Сохраняем настройки перед началом работы
        self.save_settings()
        
        threading.Thread(target=self.process_data, daemon=True).start()
    
    def process_data(self):
        """Обработка данных"""
        try:
            self.log_message("=" * 60)
            self.log_message("▶️ Начинаем обработку...")
            self.set_status("⏳ Обработка данных...")
            
            end_char = self.get_end_char()
            if not end_char:
                messagebox.showerror("Ошибка", "Укажите символ окончания команды!")
                return
            
            self.log_message(f"📌 Символ окончания: '{end_char}'")
            
            self.commands = self.parse_commands(self.input_file.get(), end_char)
            self.log_message(f"✅ Найдено команд: {len(self.commands)}")
            
            filter_pattern = self.filter_pattern.get().strip()
            if filter_pattern:
                self.filtered_commands = [cmd for cmd in self.commands if filter_pattern in cmd['command']]
                self.log_message(f"🔍 Отфильтровано: {len(self.filtered_commands)} из {len(self.commands)} команд")
            else:
                self.filtered_commands = self.commands
            
            self.save_results()
            self.show_results()
            
            self.set_status("✅ Готово!")
            self.log_message("✅ Обработка завершена!")
            
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")
            self.set_status("❌ Ошибка!")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", str(e))
    
    def save_results(self):
        """Сохранение результатов с выбранной кодировкой и разделителем"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.input_file.get()))[0]
        delim = self.get_delimiter()
        encoding = self.get_encoding()
        output_folder = self.get_output_folder()
        
        delim_name = self.delimiter.get()
        encoding_name = self.encoding.get()
        
        self.log_message(f"📌 Разделитель для экспорта: '{delim_name}' -> '{repr(delim)}'")
        self.log_message(f"📌 Кодировка: '{encoding_name}' -> '{encoding}'")
        self.log_message(f"📁 Папка сохранения: {output_folder}")
        
        # === Текстовый файл (UTF-8) ===
        txt_file = os.path.join(output_folder, f"{base_name}_commands_{timestamp}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("РЕЗУЛЬТАТ ПАРСИНГА КОМАНД\n")
            f.write(f"Исходный файл: {self.input_file.get()}\n")
            f.write(f"Дата обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Символ окончания: '{self.get_end_char()}'\n")
            f.write(f"Разделитель экспорта: '{delim_name}'\n")
            f.write(f"Кодировка: '{encoding_name}'\n")
            if self.filter_pattern.get().strip():
                f.write(f"Фильтр: '{self.filter_pattern.get()}'\n")
            f.write("=" * 70 + "\n\n")
            
            for i, cmd in enumerate(self.filtered_commands, 1):
                f.write(f"Команда {i:3d}: {cmd['command']:40s}  |  Время: {cmd['time']} с\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"Всего команд: {len(self.filtered_commands)}\n")
        
        # === CSV файл с выбранной кодировкой ===
        csv_file = os.path.join(output_folder, f"{base_name}_commands_{timestamp}.csv")
        with open(csv_file, 'w', encoding=encoding, newline='') as f:
            # Пишем заголовки
            f.write(f"Номер команды{delim}Команда{delim}Время (с)\n")
            
            # Пишем данные
            for i, cmd in enumerate(self.filtered_commands, 1):
                f.write(f"{i}{delim}{cmd['command']}{delim}{cmd['time']}\n")
        
        # === Статистика ===
        stats_file = os.path.join(output_folder, f"{base_name}_statistics_{timestamp}.csv")
        cmd_counter = Counter([cmd['command'] for cmd in self.filtered_commands])
        with open(stats_file, 'w', encoding=encoding, newline='') as f:
            f.write(f"Команда{delim}Количество\n")
            for cmd, count in cmd_counter.most_common():
                f.write(f"{cmd}{delim}{count}\n")
        
        # Сохраняем список созданных файлов
        self.last_saved_files = [txt_file, csv_file, stats_file]
        self.last_files_label.config(text=f"Последние файлы: {len(self.last_saved_files)}")
        
        self.log_message(f"💾 Сохранено в {output_folder}:")
        self.log_message(f"   📄 {os.path.basename(txt_file)}")
        self.log_message(f"   📊 {os.path.basename(csv_file)} (разделитель: '{repr(delim)}', кодировка: {encoding})")
        self.log_message(f"   📈 {os.path.basename(stats_file)} (разделитель: '{repr(delim)}', кодировка: {encoding})")
    
    def show_results(self):
        """Показ результатов"""
        self.log_message("\n" + "=" * 60)
        self.log_message("  РЕЗУЛЬТАТЫ ПАРСИНГА")
        self.log_message("=" * 60)
        
        max_display = min(20, len(self.filtered_commands))
        for i in range(max_display):
            cmd = self.filtered_commands[i]
            self.log_message(f"Команда {i+1:3d}: {cmd['command']:40s}  |  Время: {cmd['time']} с")
        
        if len(self.filtered_commands) > 20:
            self.log_message(f"... и еще {len(self.filtered_commands) - 20} команд")
        
        self.log_message("\n" + "=" * 60)
        self.log_message(f"✅ Всего команд: {len(self.filtered_commands)}")
    
    def show_statistics(self):
        """Показ статистики"""
        if not self.filtered_commands:
            messagebox.showinfo("Информация", "Сначала выполните парсинг команд!")
            return
        
        cmd_counter = Counter([cmd['command'] for cmd in self.filtered_commands])
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Статистика команд")
        stats_window.geometry("400x500")
        
        ttk.Label(stats_window, text="Статистика команд", font=("Arial", 14, "bold")).pack(pady=10)
        
        frame = ttk.Frame(stats_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Courier New", 10))
        listbox.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        listbox.insert(tk.END, f"{'Команда':<30} {'Количество':>10}")
        listbox.insert(tk.END, "-" * 42)
        
        for cmd, count in cmd_counter.most_common():
            listbox.insert(tk.END, f"{cmd:<30} {count:>10}")
        
        ttk.Button(stats_window, text="Закрыть", command=stats_window.destroy).pack(pady=10)

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = CommandParserApp(root)
    root.mainloop()