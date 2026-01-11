import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel, QComboBox,
    QMessageBox
)
from PyQt5.QtCore import Qt
from backup_worker import simulate_backup


class BackupApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Backup for AI Chats")
        self.resize(700, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Выбор проекта
        proj_layout = QHBoxLayout()
        self.proj_input = QLineEdit()
        self.proj_input.setPlaceholderText("Путь к PyCharm-проекту")
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.browse_project)
        proj_layout.addWidget(self.proj_input)
        proj_layout.addWidget(browse_btn)
        layout.addLayout(proj_layout)

        # Выбор формата
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Формат для ИИ-чата:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["qwen", "deepseek"])
        fmt_layout.addWidget(self.format_combo)
        fmt_layout.addStretch()
        layout.addLayout(fmt_layout)

        # Кнопка запуска
        self.run_btn = QPushButton("Запустить бэкап")
        self.run_btn.clicked.connect(self.run_backup)
        layout.addWidget(self.run_btn)

        # Лог-вывод
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

    def browse_project(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку проекта", os.path.expanduser("~")
        )
        if folder:
            self.proj_input.setText(folder)

    def run_backup(self):
        project = self.proj_input.text().strip()
        fmt = self.format_combo.currentText()

        if not project:
            QMessageBox.warning(self, "Ошибка", "Укажите путь к проекту!")
            return

        self.log_area.append("⏳ Запуск...\n")
        QApplication.processEvents()  # Обновить интерфейс

        try:
            result = simulate_backup(project, fmt)
            self.log_area.append(result + "\n")
        except Exception as e:
            self.log_area.append(f"❌ Ошибка: {str(e)}\n")


def main():
    app = QApplication(sys.argv)
    window = BackupApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
