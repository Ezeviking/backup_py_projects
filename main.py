import os
import json
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QFileDialog, QMessageBox, QCheckBox, QListWidget, QAbstractItemView, QMenu
)
from PyQt5.QtCore import Qt
import sys


class ProjectBackupApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyCharm Project Backup & AI Prep")
        self.setGeometry(100, 100, 900, 700)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Settings section
        settings_layout = QHBoxLayout()
        self.project_dir_label = QLabel("Project Directory:")
        self.project_dir_combo = QComboBox()
        self.project_dir_combo.setEditable(True)
        self.browse_button = QPushButton("Browse...")
        self.refresh_button = QPushButton("Refresh")

        settings_layout.addWidget(self.project_dir_label)
        settings_layout.addWidget(self.project_dir_combo, 1)
        settings_layout.addWidget(self.browse_button)
        settings_layout.addWidget(self.refresh_button)

        main_layout.addLayout(settings_layout)

        # Project selection
        project_layout = QHBoxLayout()
        project_label = QLabel("Select Project:")
        self.project_combo = QComboBox()
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_combo, 1)
        main_layout.addLayout(project_layout)

        # File tree and actions
        tree_actions_layout = QHBoxLayout()

        # Tree view for project structure
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Project Structure")
        self.tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Action buttons
        action_widget = QWidget()
        action_layout = QVBoxLayout(action_widget)

        self.toggle_excluded_button = QPushButton("Show Excluded")
        self.toggle_excluded_button.setCheckable(True)
        action_layout.addWidget(self.toggle_excluded_button)

        # Подключите сигнал
        self.toggle_excluded_button.clicked.connect(self.toggle_excluded_visibility)

        self.backup_button = QPushButton("Create Backup")
        self.prepare_qwen_button = QPushButton("Prepare for Qwen")
        self.save_filter_button = QPushButton("Save Filter State")
        self.canvas_qwen_button = QPushButton("One Canvas for Qwen")
        self.save_filter_button.clicked.connect(self.save_current_filter_state)
        self.select_all_button = QPushButton("Select All Files")
        self.clear_selection_button = QPushButton("Clear Selection")

        action_layout.addWidget(self.backup_button)
        action_layout.addWidget(self.prepare_qwen_button)
        action_layout.addWidget(self.save_filter_button)
        action_layout.addWidget(self.canvas_qwen_button)
        action_layout.addWidget(self.select_all_button)
        action_layout.addWidget(self.clear_selection_button)
        action_layout.addStretch()

        tree_actions_layout.addWidget(self.tree_widget, 3)
        tree_actions_layout.addWidget(action_widget)

        main_layout.addLayout(tree_actions_layout)

        # Selected files list
        selected_label = QLabel("Selected Files for AI Preparation:")
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        main_layout.addWidget(selected_label)
        main_layout.addWidget(self.selected_list, 1)

        # Initialize data
        self.projects_dir = ""
        self.selected_files = []
        self.excluded_items = set()
        self.settings_file = "backup_settings.json"

        # Auto-detect project directory after widgets are created
        self.detect_project_directory()

        # Connect signals
        self.browse_button.clicked.connect(self.browse_project_dir)
        self.refresh_button.clicked.connect(self.refresh_projects)
        self.project_combo.currentTextChanged.connect(self.load_project_structure)
        self.backup_button.clicked.connect(self.create_backup)
        self.prepare_qwen_button.clicked.connect(self.prepare_for_qwen)
        self.canvas_qwen_button.clicked.connect(self.export_one_canvas_for_qwen)
        self.select_all_button.clicked.connect(self.select_all_files)
        self.clear_selection_button.clicked.connect(self.clear_file_selection)

        # Load settings and refresh projects
        self.load_settings()
        self.refresh_projects()

    def detect_project_directory(self):
        """Автоматически определяет директорию проектов (на уровень выше текущего проекта)"""
        # Получаем директорию текущего файла (где находится этот скрипт)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Поднимаемся на уровень выше
        parent_dir = os.path.dirname(current_dir)

        # Проверяем, есть ли в родительской директории другие PyCharm-проекты
        if os.path.isdir(parent_dir):
            project_dirs = []
            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, ".idea")):
                    project_dirs.append(item)

            # Если нашли другие проекты в родительской директории, используем её
            if len(project_dirs) > 1:  # Если кроме текущего есть другие проекты
                self.projects_dir = parent_dir
            else:
                # Иначе используем текущую директорию
                self.projects_dir = current_dir
        else:
            self.projects_dir = current_dir

        # Обновляем комбобокс
        self.project_dir_combo.addItem(self.projects_dir)
        self.project_dir_combo.setCurrentText(self.projects_dir)

    def load_settings(self):
        """Load saved settings from JSON file"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                recent_dirs = settings.get("recent_dirs", [])

                # Добавляем недавние директории в комбобокс, если их нет
                for dir_path in recent_dirs:
                    if self.project_dir_combo.findText(dir_path) == -1:
                        self.project_dir_combo.addItem(dir_path)

                if settings.get("last_used_dir"):
                    index = self.project_dir_combo.findText(settings["last_used_dir"])
                    if index >= 0:
                        self.project_dir_combo.setCurrentIndex(index)
                        self.projects_dir = settings["last_used_dir"]
                        self.refresh_projects()

                # Загружаем последний открытый проект
                if settings.get("last_opened_project"):
                    last_project_index = self.project_combo.findText(settings["last_opened_project"])
                    if last_project_index >= 0:
                        self.project_combo.setCurrentIndex(last_project_index)
                        # Загружаем структуру последнего проекта
                        self.load_project_structure(settings["last_opened_project"])

    def save_settings(self):
        """Save current settings to JSON file"""
        recent_dirs = [self.project_dir_combo.itemText(i) for i in range(self.project_dir_combo.count())]
        # Keep only last 10 directories
        if len(recent_dirs) > 10:
            recent_dirs = recent_dirs[-10:]

        settings = {
            "recent_dirs": recent_dirs,
            "last_used_dir": self.projects_dir,
            "last_opened_project": self.project_combo.currentText()
        }

        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def save_settings(self):
        """Save current settings to JSON file"""
        recent_dirs = [self.project_dir_combo.itemText(i) for i in range(self.project_dir_combo.count())]
        # Keep only last 10 directories
        if len(recent_dirs) > 10:
            recent_dirs = recent_dirs[-10:]

        settings = {
            "recent_dirs": recent_dirs,
            "last_used_dir": self.projects_dir
        }

        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def save_current_filter_state(self):
        """Сохраняет текущее состояние фильтрации"""
        project_name = self.project_combo.currentText()
        if project_name:
            self.save_filter_state(project_name)
            QMessageBox.information(self, "Success", "Filter state saved successfully!")

    def browse_project_dir(self):
        """Open directory browser for selecting projects directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Projects Directory")
        if dir_path:
            self.projects_dir = dir_path
            # Добавляем директорию в комбобокс, если её там ещё нет
            if self.project_dir_combo.findText(dir_path) == -1:
                self.project_dir_combo.addItem(dir_path)
            self.project_dir_combo.setCurrentText(dir_path)
            self.refresh_projects()

    def refresh_projects(self):
        """Refresh the list of projects in the combo box"""
        self.project_combo.clear()
        if self.projects_dir and os.path.isdir(self.projects_dir):
            for item in os.listdir(self.projects_dir):
                item_path = os.path.join(self.projects_dir, item)
                if os.path.isdir(item_path):
                    # Проверяем, является ли это PyCharm-проектом (имеет .idea папку)
                    if os.path.exists(os.path.join(item_path, ".idea")):
                        self.project_combo.addItem(item)
            self.save_settings()

    def load_project_structure(self, project_name):
        """Load the project structure into the tree widget"""
        self.tree_widget.clear()
        if not project_name or not self.projects_dir:
            return

        project_path = os.path.join(self.projects_dir, project_name)
        if not os.path.exists(project_path):
            return

        # Загружаем исключенные элементы
        self.excluded_items = self.load_excluded_items(project_name)

        self.populate_tree_with_exclusions(self.tree_widget.invisibleRootItem(), project_path, project_name)

        # Устанавливаем контекстное меню
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)

        # Полностью разворачиваем дерево
        self.tree_widget.expandAll()

        # Применяем фильтр отображения
        self.apply_exclusion_filter()

        # Загружаем сохранённый список файлов для подготовки к ИИ
        selection_file = os.path.join(self.projects_dir, project_name, "qwen_selection.json")
        if os.path.exists(selection_file):
            with open(selection_file, 'r', encoding='utf-8') as f:
                selected_relative_paths = json.load(f)

            # Отмечаем соответствующие файлы в дереве
            self.mark_selected_files_in_tree(self.tree_widget.invisibleRootItem(),
                                             selected_relative_paths, project_path)

        # Обновляем внутренний список выбранных файлов
        self.selected_files = self.get_checked_files()
        self.update_selected_list()
        self.save_settings()

    def mark_selected_files_in_tree(self, parent_item, selected_relative_paths, project_base_path):
        """Отмечает файлы в дереве в соответствии с сохранённым списком"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            child_path = child.data(0, Qt.UserRole)

            # Если это файл, проверяем, есть ли он в сохранённом списке
            if os.path.isfile(child_path):
                # Получаем относительный путь от базовой директории проекта
                rel_path = os.path.relpath(child_path, project_base_path)
                if rel_path in selected_relative_paths:
                    child.setCheckState(0, Qt.Checked)

            # Рекурсивно обрабатываем подэлементы
            self.mark_selected_files_in_tree(child, selected_relative_paths, project_base_path)

    def populate_tree(self, parent_item, path, display_name):
        """Recursively populate the tree with directory structure"""
        item = QTreeWidgetItem(parent_item, [display_name])
        item.setData(0, Qt.UserRole, path)

        # Add checkbox to items that are files
        if os.path.isfile(path):
            item.setCheckState(0, Qt.Unchecked)

        # Only scan if it's a directory
        if os.path.isdir(path):
            try:
                for entry in sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())):
                    if self.should_include(entry):
                        self.populate_tree(item, entry.path, entry.name)
            except PermissionError:
                pass  # Skip entries we don't have permission to access

    def populate_tree_with_filter_check(self, parent_item, path, display_name, saved_items):
        """Populate the tree with directory structure and apply saved filter state"""
        item = QTreeWidgetItem(parent_item, [display_name])
        item.setData(0, Qt.UserRole, path)

        # Add checkbox to items that are files
        if os.path.isfile(path):
            item.setCheckState(0, Qt.Unchecked)

        # Only scan if it's a directory
        if os.path.isdir(path):
            try:
                for entry in sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())):
                    if self.should_include(entry):
                        rel_path = os.path.relpath(entry.path,
                                                   os.path.join(self.projects_dir, self.project_combo.currentText()))
                        # Показываем элемент, если он есть в сохранённом списке или если это новое добавление
                        show_item = rel_path in saved_items or not saved_items
                        self.populate_tree_with_filter_check(item, entry.path, entry.name, saved_items)
                        # Если элемент не должен отображаться, скрываем его
                        if saved_items and rel_path not in saved_items:
                            item.setHidden(True)
            except PermissionError:
                pass  # Skip entries we don't have permission to access

    def should_include(self, entry):
        """Determine if a file/directory should be included in the tree"""
        name = entry.name.lower()

        # Skip common PyCharm/Python directories
        skip_dirs = {'.idea', '__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules'}
        if entry.is_dir() and name in skip_dirs:
            return False

        # Skip image directories
        image_dirs = {'images', 'img', 'pics', 'photos', 'screenshots'}
        if entry.is_dir() and name in image_dirs:
            return False

        # Skip common image extensions
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp'}
        if entry.is_file() and any(name.endswith(ext) for ext in image_exts):
            return False

        # Always include .py files
        if entry.is_file() and name.endswith('.py'):
            return True

        # Include other common source files
        source_exts = {'.py', '.js', '.ts', '.html', '.css', '.json', '.txt', '.md', '.yaml', '.yml'}
        if entry.is_file() and any(name.endswith(ext) for ext in source_exts):
            return True

        # Include directories
        if entry.is_dir():
            return True

        return False

    def select_all_files(self):
        """Select all Python files in the tree"""
        self.select_files_recursive(self.tree_widget.invisibleRootItem(), True)

    def clear_file_selection(self):
        """Clear all file selections"""
        self.select_files_recursive(self.tree_widget.invisibleRootItem(), False)
        self.selected_list.clear()
        self.selected_files = []

    def select_files_recursive(self, item, state):
        """Recursively set check state for all file items"""
        if item.childCount() == 0 and os.path.isfile(item.data(0, Qt.UserRole)):  # It's a file
            item.setCheckState(0, Qt.Checked if state else Qt.Unchecked)
            if state and item.text(0).endswith('.py'):
                file_path = item.data(0, Qt.UserRole)
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
        else:
            for i in range(item.childCount()):
                self.select_files_recursive(item.child(i), state)

        self.update_selected_list()

    def update_selected_list(self):
        """Update the selected files list widget"""
        self.selected_list.clear()
        for file_path in self.selected_files:
            self.selected_list.addItem(file_path)

    def get_checked_files(self):
        """Get list of all checked files in the tree"""
        checked_files = []

        def traverse_items(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.checkState(0) == Qt.Checked and os.path.isfile(child.data(0, Qt.UserRole)):
                    checked_files.append(child.data(0, Qt.UserRole))
                traverse_items(child)

        traverse_items(self.tree_widget.invisibleRootItem())
        return checked_files

    def create_backup(self):
        """Create a backup of the selected project"""
        project_name = self.project_combo.currentText()
        if not project_name:
            QMessageBox.warning(self, "Warning", "Please select a project first.")
            return

        project_path = os.path.join(self.projects_dir, project_name)
        if not os.path.exists(project_path):
            QMessageBox.warning(self, "Warning", "Project directory does not exist.")
            return

        # Create backup directory
        backup_dir = os.path.join(self.projects_dir, f"{project_name}_backup")
        if os.path.exists(backup_dir):
            reply = QMessageBox.question(
                self, "Confirm",
                f"Backup directory '{backup_dir}' exists. Replace it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                backup_dir = QFileDialog.getExistingDirectory(self, "Select Backup Location")
                if not backup_dir:
                    return

        # Perform backup (excluding unnecessary directories)
        try:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)

            shutil.copytree(
                project_path,
                backup_dir,
                ignore=shutil.ignore_patterns(
                    '.idea', '__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules',
                    '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.svg', '*.ico', '*.webp'
                )
            )
            QMessageBox.information(self, "Success", f"Backup created at:\n{backup_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create backup:\n{str(e)}")

    def prepare_for_qwen(self):
        """Prepare selected files for Qwen (copy to forQwen folder, change extension to .txt)"""
        project_name = self.project_combo.currentText()
        if not project_name:
            QMessageBox.warning(self, "Warning", "Please select a project first.")
            return

        # Get selected files (either from checkboxes or previously saved)
        selected_files = self.get_checked_files()
        if not selected_files:
            QMessageBox.warning(self, "Warning", "Please select files to prepare for Qwen.")
            return

        # Create destination directory
        dest_dir = os.path.join(self.projects_dir, project_name, "forQwen")
        os.makedirs(dest_dir, exist_ok=True)

        try:
            copied_count = 0
            for src_path in selected_files:
                if src_path.endswith('.py'):
                    filename = os.path.basename(src_path)
                    dest_filename = filename[:-3] + '.txt'  # Change .py to .txt
                    dest_path = os.path.join(dest_dir, dest_filename)

                    shutil.copy2(src_path, dest_path)
                    copied_count += 1

            # Save selected files list for next time
            selection_file = os.path.join(self.projects_dir, project_name, "qwen_selection.json")
            with open(selection_file, 'w', encoding='utf-8') as f:
                json.dump([os.path.relpath(p, os.path.join(self.projects_dir, project_name))
                           for p in selected_files], f, ensure_ascii=False, indent=2)

            QMessageBox.information(
                self, "Success",
                f"Copied {copied_count} files to:\n{dest_dir}\n\nExtensions changed to .txt"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to prepare files for Qwen:\n{str(e)}")

        # Update internal list
        self.selected_files = selected_files
        self.update_selected_list()

    def save_filter_state(self, project_name):
        """Сохраняет состояние фильтрации для проекта"""
        filter_file = os.path.join(self.projects_dir, project_name, "filter_state.json")
        filtered_items = []

        def collect_filtered_items(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if not child.isHidden():
                    child_path = child.data(0, Qt.UserRole)
                    rel_path = os.path.relpath(child_path, os.path.join(self.projects_dir, project_name))
                    filtered_items.append(rel_path)
                collect_filtered_items(child)

        collect_filtered_items(self.tree_widget.invisibleRootItem())

        with open(filter_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_items, f, ensure_ascii=False, indent=2)

    def load_filter_state(self, project_name):
        """Загружает состояние фильтрации для проекта"""
        filter_file = os.path.join(self.projects_dir, project_name, "filter_state.json")
        if os.path.exists(filter_file):
            with open(filter_file, 'r', encoding='utf-8') as f:
                filtered_items = set(json.load(f))
            return filtered_items
        return set()

    def populate_tree_with_exclusions(self, parent_item, path, display_name):
        """Populate the tree with directory structure considering exclusions"""
        item = QTreeWidgetItem(parent_item, [display_name])
        item.setData(0, Qt.UserRole, path)

        # Add checkbox to items that are files
        if os.path.isfile(path):
            item.setCheckState(0, Qt.Unchecked)

        # Only scan if it's a directory
        if os.path.isdir(path):
            try:
                for entry in sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())):
                    if self.should_include(entry):
                        self.populate_tree_with_exclusions(item, entry.path, entry.name)
            except PermissionError:
                pass  # Skip entries we don't have permission to access

    def show_context_menu(self, position):
        """Показывает контекстное меню для исключения элементов"""
        item = self.tree_widget.itemAt(position)
        if item:
            menu = QMenu()

            # Проверяем, является ли элемент исключенным
            item_path = item.data(0, Qt.UserRole)
            project_name = self.project_combo.currentText()
            rel_path = os.path.relpath(item_path, os.path.join(self.projects_dir, project_name))

            is_excluded = rel_path in self.excluded_items

            if is_excluded:
                action = menu.addAction("Include Item")
            else:
                action = menu.addAction("Exclude Item")

            action.triggered.connect(lambda: self.toggle_exclusion(item))
            menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def toggle_exclusion(self, item):
        """Переключает состояние исключения элемента"""
        item_path = item.data(0, Qt.UserRole)
        project_name = self.project_combo.currentText()
        rel_path = os.path.relpath(item_path, os.path.join(self.projects_dir, project_name))

        if rel_path in self.excluded_items:
            # Убираем из исключенных
            self.excluded_items.remove(rel_path)
        else:
            # Добавляем в исключенные
            self.excluded_items.add(rel_path)

        # Сохраняем состояние
        self.save_excluded_items(project_name)

        # Применяем фильтр
        self.apply_exclusion_filter()

    def load_excluded_items(self, project_name):
        """Загружает список исключенных элементов"""
        exclude_file = os.path.join(self.projects_dir, project_name, "excluded_items.json")
        if os.path.exists(exclude_file):
            with open(exclude_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()

    def save_excluded_items(self, project_name):
        """Сохраняет список исключенных элементов"""
        exclude_file = os.path.join(self.projects_dir, project_name, "excluded_items.json")
        os.makedirs(os.path.dirname(exclude_file), exist_ok=True)
        with open(exclude_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.excluded_items), f, ensure_ascii=False, indent=2)

    def apply_exclusion_filter(self):
        """Применяет фильтр для отображения/скрытия исключенных элементов"""
        show_excluded = self.toggle_excluded_button.isChecked()

        def process_item(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                child_path = child.data(0, Qt.UserRole)
                project_name = self.project_combo.currentText()
                rel_path = os.path.relpath(child_path, os.path.join(self.projects_dir, project_name))

                # Если элемент исключен
                is_excluded = rel_path in self.excluded_items

                # Устанавливаем видимость в зависимости от состояния кнопки
                child.setHidden(is_excluded and not show_excluded)

                # Рекурсивно обрабатываем детей
                process_item(child)

        process_item(self.tree_widget.invisibleRootItem())

    def toggle_excluded_visibility(self):
        """Переключает видимость исключенных элементов"""
        self.apply_exclusion_filter()

    def build_project_structure(self, selected_files, project_root):
        tree = {}
        for file_path in selected_files:
            rel = os.path.relpath(file_path, project_root)
            parts = rel.split(os.sep)
            node = tree
            for part in parts:
                node = node.setdefault(part, {})
        return tree

    def format_structure(self, tree, indent=0):
        lines = []
        for key in sorted(tree.keys()):
            lines.append("  " * indent + f"- {key}")
            if tree[key]:
                lines.extend(self.format_structure(tree[key], indent + 1))
        return lines

    def export_one_canvas_for_qwen(self):
        project_name = self.project_combo.currentText()
        if not project_name:
            QMessageBox.warning(self, "Warning", "Select project first.")
            return

        project_root = os.path.join(self.projects_dir, project_name)
        selected_files = self.get_checked_files()

        if not selected_files:
            QMessageBox.warning(self, "Warning", "No files selected.")
            return

        # ---- STRUCTURE ----
        structure_tree = self.build_project_structure(selected_files, project_root)
        structure_text = "\n".join(self.format_structure(structure_tree))

        canvas = []
        canvas.append(f"PROJECT: {project_name}\n")
        canvas.append("STRUCTURE:")
        canvas.append(structure_text)
        canvas.append("\n")

        # ---- FILES ----
        for file_path in selected_files:
            rel = os.path.relpath(file_path, project_root)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
            except Exception as e:
                code = f"# ERROR READING FILE: {e}"

            canvas.append(
                "\n" + "=" * 50 +
                f"\n# FILE: {rel}\n" +
                "=" * 50 + "\n"
                           "```python\n" +
                code +
                "\n```\n"
            )

        result = "\n".join(canvas)

        QApplication.clipboard().setText(result)

        QMessageBox.information(
            self,
            "Done",
            "One canvas copied to clipboard.\nPaste it directly into Qwen."
        )


def main():
    app = QApplication(sys.argv)
    window = ProjectBackupApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
