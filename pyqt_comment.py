# pyqt_comment.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CommentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Add Comment")
        self.setFixedSize(400, 250)
        try:
            self.setWindowIcon(QIcon(resource_path('logo.ico')))
        except Exception:
            pass  # Handle missing icon gracefully

        # Set up the layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Comment Text Field
        self.comment_field = QTextEdit()
        self.comment_field.setPlaceholderText("Enter your comment here...")
        self.comment_field.setFont(QFont("Helvetica", 10))
        layout.addWidget(self.comment_field)

        # Submit Button
        self.submit_button = QPushButton("Submit")
        self.submit_button.setFixedHeight(40)
        self.submit_button.setFont(QFont("Helvetica", 10, QFont.Bold))
        self.submit_button.clicked.connect(self.submit_comment)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

        # Apply Style Sheet
        self.apply_styles()

    def apply_styles(self):
        # Define a QSS style similar to ttkbootstrap's "flatly" theme
        qss = """
            QWidget {
                background-color: #f8f9fa;
                color: #212529;
                font-family: Helvetica;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """
        self.setStyleSheet(qss)

    def submit_comment(self):
        comment = self.comment_field.toPlainText().strip()
        if comment:
            print(comment)  # This will be captured by the Tkinter app
            self.close()
        else:
            # Optionally, show an error message or highlight the field
            pass

def main():
    app = QApplication(sys.argv)
    window = CommentWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
