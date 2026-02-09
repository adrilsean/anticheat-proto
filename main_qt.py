import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QMessageBox, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPalette, QColor

# Import the other windows
import network_logic
import teacher_qt as teacher
import student_qt as student
from teacher_qt import AnimatedBubbleButton, NU_BLUE


class AntiCheatPortal(QMainWindow):
    """1. MAIN PORTAL - Central login and navigation window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PROCTORA: ANTI-CHEATING SYSTEM")
        self.setFixedSize(900, 600)

        # 1.1 CREATE FOLDERS - Initialize required directories
        for folder in ["exams", "logs", "classes"]:
            os.makedirs(folder, exist_ok=True)

        # 1.2 BACKGROUND LABEL - Display background image
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 900, 600)
        self.show_opening_page()
        
        self.active_teacher_ip = None 
        self.server_started = False  
        self.listener = network_logic.DiscoveryListener()
        self.listener.teacher_found.connect(self.on_teacher_discovered)
        self.listener.start()

    def set_bg(self, img_path):
        """1.3 SET BACKGROUND - Load and scale background image"""
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            self.bg_label.setPixmap(pixmap.scaled(900, 600, Qt.AspectRatioMode.IgnoreAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation))

    def clear_ui(self):
        """1.4 CLEAR UI - Remove all widgets except background"""
        for child in self.findChildren(QWidget):
            if child != self.bg_label: 
                child.deleteLater()

    def on_teacher_discovered(self, info):
        self.active_teacher_ip = info["ip"]
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Connected: {len(info['available_classes'])} Classes Active")
            self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")

    def show_opening_page(self):
        """2. OPENING PAGE - Display main entry screen with Teacher/Student buttons"""
        self.set_bg("67 (2).png")
        self.clear_ui()

        # 2.1 TEACHER BUTTON - Navigate to teacher panel
        self.btn_t = AnimatedBubbleButton("TEACHER", self, radius=24)
        self.btn_t.setGeometry(324, 345, 252, 50)
        self.btn_t.clicked.connect(self.show_teacher_page)
        self.btn_t.show()

        # 2.2 STUDENT BUTTON - Navigate to student login
        self.btn_s = AnimatedBubbleButton("STUDENT", self, radius=24)
        self.btn_s.setGeometry(324, 418, 252, 50)
        self.btn_s.clicked.connect(self.show_student_login)
        self.btn_s.show()

    def show_teacher_page(self):
        """3. TEACHER PAGE - Hook networking and display menu"""
        self.set_bg("69.png")
        self.clear_ui()

        if not self.server_started:
            # Start the Lighthouse (UDP) and the Server (TCP)
            classes = [f[:-5] for f in os.listdir("classes") if f.endswith(".json")]
            self.broadcaster = network_logic.TeacherBroadcaster(classes)
            self.broadcaster.start()

            self.server_thread = teacher.RequestHandler(self)
            self.server_thread.start()
            self.server_started = True

        # 3.1 MENU OPTIONS (Existing code continues)
        options = [
            ("GENERATE EXAM", 251, "exam"),
            ("VIEW EXAM LOGS", 325, "logs"),
            ("CREATE NEW CLASS", 406, "create_class"),
            ("MANAGE CLASSES", 484, "manage_class")
        ]

        for text, y, key in options:
            btn = AnimatedBubbleButton(text.upper(), self, radius=20)
            btn.setGeometry(295, y, 288, 44)
            btn.clicked.connect(lambda ch, k=key: self.launch_teacher(k))
            btn.show()

        back = AnimatedBubbleButton("BACK", self, color="#E7F0FE", radius=15, text_col=NU_BLUE)
        back.setGeometry(89, 250, 126, 36)
        back.clicked.connect(self.show_opening_page)
        back.show()

    def show_student_login(self):
        """4. STUDENT LOGIN PAGE - Display student login form"""
        self.set_bg("7.png")
        self.clear_ui()

        # 4.1 CREATE ENTRY WIDGETS - Name and password input fields
        self.name_entry = QLineEdit(self)
        self.pass_entry = QLineEdit(self)

        # 4.2 APPLY PLACEHOLDER COLOR - Set dark blue color for placeholder text
        palette = self.name_entry.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#0B2C5D"))
        self.name_entry.setPalette(palette)
        self.pass_entry.setPalette(palette)

        # 4.3 NAME ENTRY SETUP - Configure name input field
        self.name_entry.setPlaceholderText("ENTER NAME")
        self.name_entry.setGeometry(300, 313, 300, 45)
        self.name_entry.setStyleSheet("border-radius: 22px; padding-left: 15px; background: transparent; border: 2px solid #0B2C5D; color: #0B2C5D;")

        # 4.4 PASSWORD ENTRY SETUP - Configure password input field with echo mode
        self.pass_entry.setPlaceholderText("ENTER PASSWORD")
        self.pass_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_entry.setGeometry(300, 368, 300, 45)
        self.pass_entry.setStyleSheet("border-radius: 22px; padding-left: 15px; background: transparent; border: 2px solid #0B2C5D; color: #0B2C5D;")

        # 4.5 SHOW ENTRY WIDGETS - Display input fields
        self.name_entry.show()
        self.pass_entry.show()

        # 4.6 LOGIN BUTTON - Authenticate student and launch exam
        login = AnimatedBubbleButton("LOGIN", self, radius=24)
        login.setGeometry(324, 445, 252, 50)
        login.clicked.connect(self.launch_student)
        login.show()

        # 4.7 BACK BUTTON - Return to opening page
        back = AnimatedBubbleButton("BACK", self, color="#E7F0FE", radius=15, text_col=NU_BLUE)
        back.setGeometry(45, 175, 126, 36)
        back.clicked.connect(self.show_opening_page)
        back.show()

    def launch_teacher(self, page):
        """5. LAUNCH TEACHER - Open teacher window for specified page"""
        self.hide()
        self.t_win = teacher.TeacherWindow(page, self)
        self.t_win.show()

    def launch_student(self):
        """CRITICAL FIX: Use network login and pass classname"""
        if not self.active_teacher_ip:
            QMessageBox.warning(self, "Offline", "Waiting for teacher...")
            return

        n, p = self.name_entry.text().strip(), self.pass_entry.text().strip()
        
        # Perform Network Login
        resp = network_logic.network_request(self.active_teacher_ip, {
            "type": "LOGIN", "name": n, "password": p
        })

        if resp.get("status") == "success":
            self.hide()
            # Pass all 4 required arguments to the StudentWindow
            self.s_win = student.StudentWindow(n, self.active_teacher_ip, self, resp["classname"])
            self.s_win.show()
        else:
            QMessageBox.warning(self, "Denied", "Credentials not found on network.")

if __name__ == "__main__":
    # 7. MAIN LOOP - Initialize and run application
    app = QApplication(sys.argv)
    portal = AntiCheatPortal()
    portal.show()
    sys.exit(app.exec())