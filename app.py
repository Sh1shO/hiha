from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QLineEdit, QFormLayout, QDialog, QMessageBox, QStackedWidget, QHBoxLayout, QGridLayout, QLabel, QGroupBox, QDateEdit, QSpinBox, QDialogButtonBox
from PySide6.QtCore import Qt, QDate
from fpdf import FPDF
from db import get_session, session, Rental, Car, Client, CarModel
from datetime import date, datetime, timedelta


class EditRentalDialog(QDialog):
    def __init__(self, rental, parent=None):
        super().__init__(parent)
        self.rental = rental
        self.setWindowTitle("Редактировать прокат")

        # Layout для формы
        layout = QFormLayout(self)

        # Выпадающий список для выбора клиента
        self.client_combo = QComboBox()
        self.client_combo.addItem("Выберите клиента")  # Начальный элемент
        # Заполняем выпадающий список клиентами из базы данных
        clients = session.query(Client).all()
        for client in clients:
            client_info = f"{client.lastname} {client.firstname} {client.patronymic}"
            self.client_combo.addItem(client_info, userData=client.id)  # Добавляем клиента в выпадающий список с id клиента
        layout.addRow("Клиент:", self.client_combo)

        # Выпадающий список для выбора автомобиля
        self.car_combo = QComboBox()
        self.car_combo.addItem("Выберите машину")  # Начальный элемент
        # Заполняем выпадающий список машинами из базы данных
        cars = session.query(Car).all()
        for car in cars:
            car_info = f"{car.fk_model_id.name} ({car.color}, {car.number})"
            self.car_combo.addItem(car_info, userData=car.id)  # Добавляем машину в выпадающий список с id машины
        layout.addRow("Автомобиль:", self.car_combo)

        # Поле для ввода количества дней
        self.days_input = QLineEdit(str(self.rental.days_quantity))
        layout.addRow("Количество дней:", self.days_input)

        # Кнопки для подтверждения или отмены изменений
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_rental)
        layout.addWidget(self.save_button)

    def save_rental(self):
        """Сохраняет изменения в базе данных."""
        new_client_id = self.client_combo.currentData()  # Получаем выбранный id клиента
        new_car_id = self.car_combo.currentData()  # Получаем выбранный id автомобиля
        new_days_quantity = self.days_input.text()

        if not new_client_id or not new_car_id or not new_days_quantity.isdigit():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите клиента и автомобиль и введите количество дней.")
            return

        # Обновляем данные о прокате
        self.rental.client_id = new_client_id
        self.rental.car_id = new_car_id
        self.rental.days_quantity = int(new_days_quantity)
        session.commit()  # Сохраняем изменения в базе
        self.accept()  # Закрыть диалог


class AddRentalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление нового проката")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Поля для данных клиента
        client_group = QGroupBox("Данные клиента")
        client_layout = QFormLayout()

        self.lastname_input = QLineEdit()
        self.firstname_input = QLineEdit()
        self.patronymic_input = QLineEdit()
        self.series_passport = QLineEdit()
        self.number_passport = QLineEdit()

        client_layout.addRow("Фамилия:", self.lastname_input)
        client_layout.addRow("Имя:", self.firstname_input)
        client_layout.addRow("Отчество:", self.patronymic_input)
        client_layout.addRow("Серия паспорта:", self.series_passport)
        client_layout.addRow("Номер паспорта:", self.number_passport)
        
        client_group.setLayout(client_layout)
        layout.addWidget(client_group)

        # Поля для данных проката
        rental_group = QGroupBox("Данные проката")
        rental_layout = QFormLayout()

        # Выбор автомобиля
        self.car_combo = QComboBox()
        cars = session.query(Car, CarModel).\
            join(CarModel, Car.model_id == CarModel.id).all()
        
        for car, model in cars:
            self.car_combo.addItem(f"{model.name} ({car.color}, {car.number})", car.id)

        # Стоимость в день
        self.day_cost = QSpinBox()
        self.day_cost.setRange(1, 100000)
        self.day_cost.setValue(1000)

        # Дата начала
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        # Количество дней
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(1)

        rental_layout.addRow("Автомобиль:", self.car_combo)
        rental_layout.addRow("Стоимость в день:", self.day_cost)
        rental_layout.addRow("Дата начала:", self.date_edit)
        rental_layout.addRow("Количество дней:", self.days_spin)

        rental_group.setLayout(rental_layout)
        layout.addWidget(rental_group)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        """Проверяет заполнение обязательных полей"""
        if not all([
            self.lastname_input.text(),
            self.firstname_input.text(),
            self.patronymic_input.text(),
            self.series_passport.text(),
            self.number_passport.text(),
            self.car_combo.currentData()
        ]):
            QMessageBox.warning(self, "Ошибка", 
                              "Пожалуйста, заполните все обязательные поля!")
            return
        
        # Проверка корректности паспортных данных
        try:
            series = int(self.series_passport.text())
            number = int(self.number_passport.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", 
                              "Серия и номер паспорта должны быть числами!")
            return
        
        self.accept()


class RentalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Прокат автомобилей")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Добавляем панель поиска и фильтрации
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.search_rentals)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все модели")  # Добавляем пункт "Все модели"
        
        # Получаем все уникальные модели из базы данных
        car_models = session.query(CarModel.name).distinct().all()
        for model in car_models:
            self.filter_combo.addItem(model[0])
        
        self.filter_combo.currentTextChanged.connect(self.filter_rentals)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        layout.addLayout(search_layout)

        # Переключатель вида (таблица/плитки)
        view_toggle = QPushButton("Переключить вид")
        view_toggle.clicked.connect(self.toggle_view)
        layout.addWidget(view_toggle)

        # Добавляем стек виджетов для переключения между таблицей и плитками
        self.stack = QStackedWidget()
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Клиент", "Автомобиль", "Дата начала", "Количество дней"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Запрет редактирования
        layout.addWidget(self.table)

        # Плитки
        self.tiles = QWidget()
        self.tiles_layout = QGridLayout(self.tiles)
        
        self.stack.addWidget(self.table)
        self.stack.addWidget(self.tiles)
        layout.addWidget(self.stack)

        # Кнопки управления
        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить")
        edit_button = QPushButton("Редактировать")
        delete_button = QPushButton("Удалить")
        generate_report_button = QPushButton("Создать отчет")

        add_button.clicked.connect(self.add_rental)
        edit_button.clicked.connect(self.edit_rental)
        delete_button.clicked.connect(self.delete_rental)
        generate_report_button.clicked.connect(self.generate_rental_report)

        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(generate_report_button)
        layout.addLayout(button_layout)

        # Загрузка данных
        self.load_rentals()

    def load_rentals(self):
        """Загружает данные из базы в таблицу и плитки."""
        # Получаем данные о прокатах
        rentals = session.query(Rental, Client, Car, CarModel).join(Client, Rental.client_id == Client.id) \
            .join(Car, Rental.car_id == Car.id) \
            .join(CarModel, Car.model_id == CarModel.id).all()

        # Очищаем таблицу и плитки
        self.table.setRowCount(len(rentals))
        
        # Очищаем плиточный layout
        while self.tiles_layout.count():
            item = self.tiles_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Заполняем таблицу и плитки
        for row, (rental, client, car, model) in enumerate(rentals):
            # Данные для таблицы
            self.table.setItem(row, 0, QTableWidgetItem(f"{client.lastname} {client.firstname} {client.patronymic}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{model.name} ({car.color}, {car.number})"))
            self.table.setItem(row, 2, QTableWidgetItem(str(rental.start_date)))
            self.table.setItem(row, 3, QTableWidgetItem(str(rental.days_quantity)))

            # Создаем плитку
            tile = QWidget()
            tile_layout = QVBoxLayout(tile)
            
            # Добавляем информацию в плитку
            client_label = QLabel(f"Клиент: {client.lastname} {client.firstname}")
            car_label = QLabel(f"Авто: {model.name} ({car.number})")
            date_label = QLabel(f"Дата: {rental.start_date}")
            
            tile_layout.addWidget(client_label)
            tile_layout.addWidget(car_label)
            tile_layout.addWidget(date_label)
            
            # Добавляем плитку в сетку
            row_pos = row // 3  # 3 плитки в ряд
            col_pos = row % 3
            self.tiles_layout.addWidget(tile, row_pos, col_pos)

    def edit_rental(self):
        """Редактирует данные о прокате авто."""
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите строку для редактирования.")
            return

        # Получаем объект проката для редактирования
        rental_id = self.table.item(row, 2).text()  # Для поиска проката можно использовать дату начала
        rental = session.query(Rental).filter(Rental.start_date == rental_id).first()  # Получаем прокат по дате начала

        if rental is None:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти прокат для редактирования.")
            return

        # Создаем диалоговое окно для редактирования
        dialog = EditRentalDialog(rental, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_rentals()  # Перезагружаем данные в таблице
            QMessageBox.information(self, "Успех", "Данные успешно обновлены!")

    def generate_rental_report(self):
        session = get_session()

        # Указываем начальную и конечную дату отчета
        start_date, end_date = date(2024, 1, 1), date(2024, 12, 31)

        # Извлечение данных о прокатах по каждому клиенту
        rentals = (
            session.query(
                Client.lastname,
                Client.firstname,
                Client.patronymic,
                Rental.client_id
            )
            .join(Client, Rental.client_id == Client.id)
            .filter(Rental.start_date.between(start_date, end_date))
            .all()
        )

        # Считаем количество прокатов по каждому клиенту
        client_rentals = {}
        for last_name, first_name, patronymic, client_id in rentals:
            full_name = f"{last_name} {first_name} {patronymic}"
            client_rentals[full_name] = client_rentals.get(full_name, 0) + 1

        # Создание PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.add_font('FreeSans', '', 'FreeSans.ttf', uni=True)
        pdf.set_font('FreeSans', '', 16)

        # Заголовок отчета
        pdf.cell(200, 10, "Отчет о количестве прокатов автомобилей по клиентам", ln=True, align='C')
        pdf.ln(10)

        # Заполнение данных отчета
        pdf.set_font('FreeSans', '', 12)
        for client, count in client_rentals.items():
            pdf.cell(200, 10, f"{client}:", ln=True)
            pdf.cell(200, 10, f"Прокатов: {count}", ln=True)
            pdf.ln(5)

        # Сохранение PDF
        pdf_output_path = f"./rental_report_by_client.pdf"
        pdf.output(pdf_output_path)

        print(f"Отчет был успешно экспортирован в {pdf_output_path}")
        session.close()

        QMessageBox.information(self, "Успех", f"Отчет был успешно экспортирован в:\n{pdf_output_path}")

    def add_rental(self):
        """Добавляет новый прокат"""
        dialog = AddRentalDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                # Создаем нового клиента
                new_client = Client(
                    firstname=dialog.firstname_input.text(),
                    lastname=dialog.lastname_input.text(),
                    patronymic=dialog.patronymic_input.text(),
                    series_passport=int(dialog.series_passport.text()),
                    number_passport=int(dialog.number_passport.text())
                )
                session.add(new_client)
                session.flush()  # Чтобы получить ID нового клиента

                # Создаем новый прокат
                new_rental = Rental(
                    client_id=new_client.id,
                    car_id=dialog.car_combo.currentData(),
                    start_date=dialog.date_edit.date().toPython(),
                    days_quantity=dialog.days_spin.value(),
                    day_cost=dialog.day_cost.value()
                )
                session.add(new_rental)
                session.commit()
                
                self.load_rentals()
                QMessageBox.information(self, "Успех", "Прокат успешно добавлен!")
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить прокат: {str(e)}")

    def delete_rental(self):
        """Удаляет выбранный прокат"""
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите прокат для удаления")
            return

        reply = QMessageBox.question(self, "Подтверждение", 
                                   "Вы уверены, что хотите удалить этот прокат?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            rental_date = self.table.item(row, 2).text()
            rental = session.query(Rental).filter(Rental.start_date == rental_date).first()
            if rental:
                session.delete(rental)
                session.commit()
                self.load_rentals()
                QMessageBox.information(self, "Успех", "Прокат успешно удален!")

    def toggle_view(self):
        """Переключает между табличным и плиточным видом"""
        current_index = self.stack.currentIndex()
        self.stack.setCurrentIndex(1 if current_index == 0 else 0)
        self.load_rentals()

    def search_rentals(self):
        """Поиск по прокатам"""
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            hidden = True
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    hidden = False
                    break
            self.table.setRowHidden(row, hidden)

    def filter_rentals(self):
        """Фильтрация прокатов по модели автомобиля"""
        filter_model = self.filter_combo.currentText()
        
        for row in range(self.table.rowCount()):
            if filter_model == "Все модели":
                self.table.setRowHidden(row, False)
                continue

            # Получаем информацию о машине из второй колонки
            car_info = self.table.item(row, 1).text()
            # Получаем название модели (оно идет до первой скобки)
            car_model = car_info.split('(')[0].strip()
            
            # Скрываем строку, если модель не соответствует фильтру
            self.table.setRowHidden(row, car_model != filter_model)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = RentalApp()
    window.show()
    sys.exit(app.exec())
