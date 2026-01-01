import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
import json
import os
def to_normal_readly_type(number):
    integer_part = int(abs(number))
    decimal_part = abs(number) - integer_part
    
    formatted_integer = f"{integer_part:,}".replace(",", " ")
    
    sign = "-" if number < 0 else ""
    
    if decimal_part > 0:
        decimal_str = f"{decimal_part:.2f}".lstrip("0")
        return f"{sign}{formatted_integer}{decimal_str}"
    else:
        return f"{sign}{formatted_integer}"

class FinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.operations = []
        self.currencies = {}  
        self.pending_currencies = {} 
        self.is_amount_hidden = False
        self.base_currency = 'RUB'  
        self.exchange_rates = { 
            'USD': 90.0,
            'EUR': 100.0,
            'RUB': 1.0,
            'KZT': 0.2,
            'UAH': 2.3,
            'BYN': 28.0
        }
        self.predefined_expense_names = ['Ашан', 'Аптека', 'Вайлдберриз', 'Магнит', 'Пятерочка', 'Такси', 'Кафе', 'Другое']
        self.predefined_income_names = ['Зарплата', 'Фриланс', 'Инвестиции', 'Подарок', 'Возврат долга', 'Другое']
        
        self.load_data()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Finance Manager')
        self.setGeometry(100, 100, 900, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        
        self.total_label = QLabel('Общая сумма (с ожидаемыми): 0.00 RUB')
        self.total_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #FF9800;')
        self.total_label.setAlignment(Qt.AlignCenter)
        
        self.actual_label = QLabel('Фактическая сумма: 0.00 RUB')
        self.actual_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #4CAF50;')
        self.actual_label.setAlignment(Qt.AlignCenter)
        
        top_layout.addWidget(self.total_label)
        top_layout.addWidget(self.actual_label)
        
        hide_layout = QHBoxLayout()
        self.hide_button = QPushButton('Скрыть суммы')
        self.hide_button.clicked.connect(self.toggle_amount_visibility)
        hide_layout.addStretch()
        hide_layout.addWidget(self.hide_button)
        hide_layout.addStretch()
        top_layout.addLayout(hide_layout)
        
        layout.addWidget(top_panel)
        
        self.tab_widget = QTabWidget()
        
        self.main_tab = QWidget()
        self.setup_main_tab()
        self.tab_widget.addTab(self.main_tab, "Главная")
        
        self.operations_tab = QWidget()
        self.setup_operations_tab()
        self.tab_widget.addTab(self.operations_tab, "Операции")
        
        self.pending_tab = QWidget()
        self.setup_pending_tab()
        self.tab_widget.addTab(self.pending_tab, "Ожидаемые доходы")
        
        self.analytics_tab = QWidget()
        self.setup_analytics_tab()
        self.tab_widget.addTab(self.analytics_tab, "Аналитика")
        
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "Настройки")
        
        layout.addWidget(self.tab_widget)
        
        self.update_amounts_display()
        self.update_operations_table()
        
    def setup_main_tab(self):
        layout = QVBoxLayout(self.main_tab)
        
        income_btn = QPushButton('Добавить доход')
        income_btn.setStyleSheet('background-color: #4CAF50; color: white; font-size: 14px; padding: 10px;')
        income_btn.clicked.connect(lambda: self.add_operation('income'))
        layout.addWidget(income_btn)
        
        pending_income_btn = QPushButton('Добавить ожидаемый доход')
        pending_income_btn.setStyleSheet('background-color: #FF9800; color: white; font-size: 14px; padding: 10px;')
        pending_income_btn.clicked.connect(lambda: self.add_operation('pending_income'))
        layout.addWidget(pending_income_btn)
        
        expense_btn = QPushButton('Добавить расход')
        expense_btn.setStyleSheet('background-color: #f44336; color: white; font-size: 14px; padding: 10px;')
        expense_btn.clicked.connect(lambda: self.add_operation('expense'))
        layout.addWidget(expense_btn)
        
        show_ops_btn = QPushButton('Показать таблицу операций')
        show_ops_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        layout.addWidget(show_ops_btn)
        
        show_pending_btn = QPushButton('Показать ожидаемые доходы')
        show_pending_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        layout.addWidget(show_pending_btn)
        
        currencies_label = QLabel('Фактический баланс по валютам:')
        currencies_label.setStyleSheet('font-weight: bold; margin-top: 20px;')
        layout.addWidget(currencies_label)
        
        self.currencies_list = QListWidget()
        layout.addWidget(self.currencies_list)
        
        pending_label = QLabel('Ожидаемые доходы по валютам:')
        pending_label.setStyleSheet('font-weight: bold; margin-top: 20px;')
        layout.addWidget(pending_label)
        
        self.pending_list = QListWidget()
        layout.addWidget(self.pending_list)
        
        layout.addStretch()
        
    def setup_operations_tab(self):
        layout = QVBoxLayout(self.operations_tab)
        
        self.operations_table = QTableWidget()
        self.operations_table.setColumnCount(6)
        self.operations_table.setHorizontalHeaderLabels([
            'Тип', 'Название', 'Сумма', 'Валюта', 'Дата и время', 'Комментарий'
        ])
        self.operations_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.operations_table)
        
        btn_layout = QHBoxLayout()
        
        delete_btn = QPushButton('Удалить выбранное')
        delete_btn.clicked.connect(self.delete_selected_operation)
        btn_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton('Очистить все')
        clear_btn.clicked.connect(self.clear_all_operations)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        
    def setup_pending_tab(self):
        layout = QVBoxLayout(self.pending_tab)
        
        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(7)
        self.pending_table.setHorizontalHeaderLabels([
            'Статус', 'Название', 'Сумма', 'Валюта', 'Дата и время', 'Комментарий', 'Действия'
        ])
        self.pending_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pending_table)
        
        confirm_layout = QHBoxLayout()
        confirm_btn = QPushButton('Подтвердить выбранный доход')
        confirm_btn.clicked.connect(self.confirm_selected_pending)
        confirm_btn.setStyleSheet('background-color: #4CAF50; color: white;')
        confirm_layout.addWidget(confirm_btn)
        
        delete_pending_btn = QPushButton('Удалить выбранный')
        delete_pending_btn.clicked.connect(self.delete_selected_pending)
        delete_pending_btn.setStyleSheet('background-color: #f44336; color: white;')
        confirm_layout.addWidget(delete_pending_btn)
        
        layout.addLayout(confirm_layout)
        
    def setup_analytics_tab(self):
        layout = QVBoxLayout(self.analytics_tab)
        
        label = QLabel('Аналитика\n\nЭта вкладка находится в разработке.\nЗдесь будет отображаться графическая аналитика ваших финансов.')
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet('font-size: 16px; color: #666;')
        layout.addWidget(label)
        
    def setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        
        currency_label = QLabel('Основная валюта для отображения:')
        layout.addWidget(currency_label)
        
        self.base_currency_combo = QComboBox()
        self.base_currency_combo.addItems(['USD', 'EUR', 'RUB', 'KZT', 'UAH', 'BYN'])
        self.base_currency_combo.setCurrentText(self.base_currency)
        self.base_currency_combo.currentTextChanged.connect(self.change_base_currency)
        layout.addWidget(self.base_currency_combo)
        
        rates_label = QLabel('Курсы валют (относительно RUB):')
        rates_label.setStyleSheet('font-weight: bold; margin-top: 20px;')
        layout.addWidget(rates_label)
        
        self.rates_widget = QWidget()
        rates_layout = QVBoxLayout(self.rates_widget)
        
        self.rate_inputs = {}
        for currency in ['USD', 'EUR', 'KZT', 'UAH', 'BYN']:
            hbox = QHBoxLayout()
            label = QLabel(f'1 {currency} = ')
            spinbox = QDoubleSpinBox()
            spinbox.setMinimum(0.01)
            spinbox.setMaximum(10000)
            spinbox.setValue(self.exchange_rates.get(currency, 1.0))
            spinbox.valueChanged.connect(lambda val, c=currency: self.update_exchange_rate(c, val))
            hbox.addWidget(label)
            hbox.addWidget(spinbox)
            hbox.addWidget(QLabel('RUB'))
            hbox.addStretch()
            rates_layout.addLayout(hbox)
            self.rate_inputs[currency] = spinbox
            
        layout.addWidget(self.rates_widget)
        layout.addStretch()
    
    def add_operation(self, op_type):
        if op_type == 'pending_income':
            dialog = OperationDialog('income', self, is_pending=True)
        else:
            dialog = OperationDialog(op_type, self)
            
        if dialog.exec_():
            name, amount, currency, comment, is_pending = dialog.get_data()
            
            operation = {
                'type': op_type if op_type != 'pending_income' else 'income',
                'name': name,
                'amount': amount,
                'currency': currency,
                'comment': comment,
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_pending': is_pending
            }
            
            self.operations.append(operation)
            
            if op_type == 'pending_income' or is_pending:
                if currency in self.pending_currencies:
                    self.pending_currencies[currency] += amount
                else:
                    self.pending_currencies[currency] = amount
            else:
                if op_type == 'income':
                    if currency in self.currencies:
                        self.currencies[currency] += amount
                    else:
                        self.currencies[currency] = amount
                else:  
                    if currency in self.currencies:
                        self.currencies[currency] -= amount
                    else:
                        self.currencies[currency] = -amount
            
            self.update_amounts_display()
            self.update_operations_table()
            self.update_pending_table()
            self.update_currency_lists()
            self.save_data()
    
    def calculate_total_in_base_currency(self, currency_dict):
        """Рассчитывает сумму в основной валюте"""
        total = 0.0
        
        for currency, amount in currency_dict.items():
            if currency == self.base_currency:
                total += amount
            else:
                if currency in self.exchange_rates and self.base_currency == 'RUB':
                    total += amount * self.exchange_rates[currency]
                elif self.base_currency in self.exchange_rates and currency == 'RUB':
                    total += amount / self.exchange_rates[self.base_currency]
                else:
                    if currency in self.exchange_rates and self.base_currency in self.exchange_rates:
                        amount_in_rub = amount * self.exchange_rates[currency]
                        total += amount_in_rub / self.exchange_rates[self.base_currency]
        
        return total
    


    def update_amounts_display(self):
        actual_total = self.calculate_total_in_base_currency(self.currencies)
        pending_total = self.calculate_total_in_base_currency(self.pending_currencies)
        total_with_pending = actual_total + pending_total
        
        if self.is_amount_hidden:
            self.total_label.setText(f'Общая сумма (с ожидаемыми): ****** {self.base_currency}')
            self.actual_label.setText(f'Фактическая сумма: ****** {self.base_currency}')
        else:
            self.total_label.setText(f'Общая сумма (с ожидаемыми): {to_normal_readly_type(total_with_pending)} {self.base_currency}')
            self.actual_label.setText(f'Фактическая сумма: {to_normal_readly_type(actual_total)} {self.base_currency}')
            
    def toggle_amount_visibility(self):
        self.is_amount_hidden = not self.is_amount_hidden
        if self.is_amount_hidden:
            self.hide_button.setText('Показать суммы')
        else:
            self.hide_button.setText('Скрыть суммы')
        self.update_amounts_display()
        
    def update_operations_table(self):
        actual_operations = [op for op in self.operations if not op.get('is_pending', False)]
        self.operations_table.setRowCount(len(actual_operations))
        
        for row, op in enumerate(actual_operations):
            type_text = 'Доход' if op['type'] == 'income' else 'Расход'
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor('#4CAF50') if op['type'] == 'income' else QColor('#f44336'))
            
            name_item = QTableWidgetItem(op['name'])
            amount_item = QTableWidgetItem(f"{op['amount']:.2f}")
            currency_item = QTableWidgetItem(op['currency'])
            datetime_item = QTableWidgetItem(op['datetime'])
            comment_item = QTableWidgetItem(op['comment'])
            
            self.operations_table.setItem(row, 0, type_item)
            self.operations_table.setItem(row, 1, name_item)
            self.operations_table.setItem(row, 2, amount_item)
            self.operations_table.setItem(row, 3, currency_item)
            self.operations_table.setItem(row, 4, datetime_item)
            self.operations_table.setItem(row, 5, comment_item)
            
        self.operations_table.resizeColumnsToContents()
    
    def update_pending_table(self):
        pending_operations = [op for op in self.operations if op.get('is_pending', False)]
        self.pending_table.setRowCount(len(pending_operations))
        
        for row, op in enumerate(pending_operations):
            status_item = QTableWidgetItem('Ожидает')
            status_item.setForeground(QColor('#FF9800'))
            
            name_item = QTableWidgetItem(op['name'])
            amount_item = QTableWidgetItem(f"{op['amount']:.2f}")
            currency_item = QTableWidgetItem(op['currency'])
            datetime_item = QTableWidgetItem(op['datetime'])
            comment_item = QTableWidgetItem(op['comment'])
            
            confirm_btn = QPushButton('Подтвердить')
            confirm_btn.clicked.connect(lambda checked, r=row: self.confirm_pending_income(r))
            confirm_btn.setStyleSheet('background-color: #4CAF50; color: white; padding: 5px;')
            
            self.pending_table.setItem(row, 0, status_item)
            self.pending_table.setItem(row, 1, name_item)
            self.pending_table.setItem(row, 2, amount_item)
            self.pending_table.setItem(row, 3, currency_item)
            self.pending_table.setItem(row, 4, datetime_item)
            self.pending_table.setItem(row, 5, comment_item)
            self.pending_table.setCellWidget(row, 6, confirm_btn)
            
        self.pending_table.resizeColumnsToContents()
        
    def update_currency_lists(self):
        # Обновляем список фактических балансов
        self.currencies_list.clear()
        
        for currency, amount in sorted(self.currencies.items()):
            if amount != 0:
                item_text = f"{currency}: {amount:.2f}"
                item = QListWidgetItem(item_text)
                if amount > 0:
                    item.setForeground(QColor('#4CAF50'))
                else:
                    item.setForeground(QColor('#f44336'))
                self.currencies_list.addItem(item)
        
        self.pending_list.clear()
        
        for currency, amount in sorted(self.pending_currencies.items()):
            if amount != 0:
                item_text = f"{currency}: {amount:.2f}"
                item = QListWidgetItem(item_text)
                item.setForeground(QColor('#FF9800'))
                self.pending_list.addItem(item)
    
    def confirm_pending_income(self, row_index):
        pending_ops = [op for op in self.operations if op.get('is_pending', False)]
        if row_index < len(pending_ops):
            pending_op = pending_ops[row_index]
            for i, op in enumerate(self.operations):
                if op == pending_op:
                    currency = op['currency']
                    amount = op['amount']
                    
                    if currency in self.pending_currencies:
                        self.pending_currencies[currency] -= amount
                        if self.pending_currencies[currency] == 0:
                            del self.pending_currencies[currency]
                    
                    if currency in self.currencies:
                        self.currencies[currency] += amount
                    else:
                        self.currencies[currency] = amount
                    
                    op['is_pending'] = False
                    
                    self.update_amounts_display()
                    self.update_operations_table()
                    self.update_pending_table()
                    self.update_currency_lists()
                    self.save_data()
                    break
    
    def confirm_selected_pending(self):
        selected = self.pending_table.currentRow()
        if selected >= 0:
            self.confirm_pending_income(selected)
    
    def delete_selected_pending(self):
        selected = self.pending_table.currentRow()
        if selected >= 0:
            pending_ops = [op for op in self.operations if op.get('is_pending', False)]
            if selected < len(pending_ops):
                pending_op = pending_ops[selected]
                
                currency = pending_op['currency']
                amount = pending_op['amount']
                
                if currency in self.pending_currencies:
                    self.pending_currencies[currency] -= amount
                    if self.pending_currencies[currency] == 0:
                        del self.pending_currencies[currency]
                
                self.operations.remove(pending_op)
                
                self.update_amounts_display()
                self.update_pending_table()
                self.update_currency_lists()
                self.save_data()
                
    def delete_selected_operation(self):
        selected = self.operations_table.currentRow()
        if selected >= 0:
            actual_ops = [op for op in self.operations if not op.get('is_pending', False)]
            if selected < len(actual_ops):
                op = actual_ops[selected]
                
                if op['type'] == 'income':
                    self.currencies[op['currency']] -= op['amount']
                else:
                    self.currencies[op['currency']] += op['amount']
                
                self.operations.remove(op)
                
                self.update_amounts_display()
                self.update_operations_table()
                self.update_currency_lists()
                self.save_data()
                
    def clear_all_operations(self):
        reply = QMessageBox.question(self, 'Подтверждение', 
                                   'Вы уверены, что хотите удалить все операции?',
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.operations.clear()
            self.currencies.clear()
            self.pending_currencies.clear()
            
            self.update_amounts_display()
            self.update_operations_table()
            self.update_pending_table()
            self.update_currency_lists()
            self.save_data()
    
    def change_base_currency(self, currency):
        self.base_currency = currency
        self.update_amounts_display()
        self.save_data()
    
    def update_exchange_rate(self, currency, rate):
        self.exchange_rates[currency] = rate
        self.update_amounts_display()
        self.save_data()
            
    def save_data(self):
        data = {
            'operations': self.operations,
            'currencies': self.currencies,
            'pending_currencies': self.pending_currencies,
            'base_currency': self.base_currency,
            'exchange_rates': self.exchange_rates,
            'predefined_expense_names': self.predefined_expense_names,
            'predefined_income_names': self.predefined_income_names
        }
        
        with open('finance_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_data(self):
        if os.path.exists('finance_data.json'):
            with open('finance_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.operations = data.get('operations', [])
                self.currencies = data.get('currencies', {})
                self.pending_currencies = data.get('pending_currencies', {})
                self.base_currency = data.get('base_currency', 'RUB')
                self.exchange_rates = data.get('exchange_rates', self.exchange_rates)
                self.predefined_expense_names = data.get('predefined_expense_names', self.predefined_expense_names)
                self.predefined_income_names = data.get('predefined_income_names', self.predefined_income_names)

class OperationDialog(QDialog):
    def __init__(self, op_type, parent=None, is_pending=False):
        super().__init__(parent)
        self.op_type = op_type
        self.is_pending = is_pending
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        title = 'Добавить доход'
        if self.op_type == 'expense':
            title = 'Добавить расход'
        elif self.is_pending:
            title = 'Добавить ожидаемый доход'
            
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Название с выпадающим списком
        layout.addWidget(QLabel('Название:'))
        
        self.name_combo = QComboBox()
        if self.op_type == 'expense':
            self.name_combo.addItems(self.parent.predefined_expense_names)
        else:
            self.name_combo.addItems(self.parent.predefined_income_names)
        
        self.name_combo.setEditable(False)
        self.name_combo.currentTextChanged.connect(self.on_name_changed)
        layout.addWidget(self.name_combo)
        
        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText('Введите свое название...')
        self.custom_name_input.setVisible(False)
        layout.addWidget(self.custom_name_input)
        
        layout.addWidget(QLabel('Сумма:'))
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(1000000)
        self.amount_input.setValue(100.0)
        layout.addWidget(self.amount_input)
        
        layout.addWidget(QLabel('Валюта:'))
        self.currency_input = QComboBox()
        self.currency_input.addItems(['RUB', 'USD', 'EUR', 'KZT', 'UAH', 'BYN'])
        self.currency_input.setCurrentText('RUB')  # RUB по умолчанию
        self.currency_input.setEditable(True)
        layout.addWidget(self.currency_input)
        
        layout.addWidget(QLabel('Комментарий:'))
        self.comment_input = QTextEdit()
        self.comment_input.setMaximumHeight(100)
        layout.addWidget(self.comment_input)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('Добавить')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def on_name_changed(self, text):
        if text == 'Другое':
            self.custom_name_input.setVisible(True)
            self.custom_name_input.setFocus()
        else:
            self.custom_name_input.setVisible(False)
    
    def get_data(self):
        if self.name_combo.currentText() == 'Другое' and self.custom_name_input.text():
            name = self.custom_name_input.text()
        else:
            name = self.name_combo.currentText()
        
        return (
            name,
            self.amount_input.value(),
            self.currency_input.currentText(),
            self.comment_input.toPlainText(),
            self.is_pending
        )

def main():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = FinanceApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
