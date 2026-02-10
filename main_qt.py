import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QMessageBox, QWidget,QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap,  QFontDatabase, QIcon

# Import the other windows
import network_logic
import teacher_qt as teacher
import student_qt as student
from teacher_qt import AnimatedBubbleButton, NU_BLUE


def get_asset_path(filename):
    """Get the correct path for bundled assets (works for both source and PyInstaller EXE)"""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running from source
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


def get_data_path(subfolder):
    """Get the correct path for data folders (exams, logs, classes) in proctora_data directory"""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle - use current working directory
        base_path = os.getcwd()
    else:
        # Running from source - use script directory
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'proctora_data', subfolder)


def load_custom_fonts():
    """Load Poppins fonts from the fonts directory"""
    font_dir = get_asset_path('fonts')
    loaded_fonts = []
    
    # Try to load Poppins fonts
    poppins_fonts = [
        'Poppins-Regular.ttf',
        'Poppins-Medium.ttf', 
        'Poppins-Bold.ttf'
    ]
    
    for font_file in poppins_fonts:
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                loaded_fonts.append(font_file)
                print(f"Loaded font: {font_file}")
            else:
                print(f"Failed to load font: {font_file}")
        else:
            print(f"Font file not found: {font_file}")
    
    return loaded_fonts


class AntiCheatPortal(QMainWindow):
    """1. MAIN PORTAL - Central login and navigation window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PROCTORA: ANTI-CHEATING SYSTEM")
        self.setWindowIcon(QIcon(get_asset_path("logo.png")))
        self.setFixedSize(900, 600)

        # 1.1 CREATE FOLDERS - Initialize required directories in proctora_data
        for folder in ["exams", "logs", "classes"]:
            os.makedirs(get_data_path(folder), exist_ok=True)

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
        # Prevent dangling references to widgets that will be deleted
        if getattr(self, 'status_label', None) is not None:
            self.status_label = None

        # Preserve embedded student/teacher widgets so they are reusable
        preserve = set()
        if getattr(self, 's_win', None) is not None:
            preserve.add(self.s_win)
        if getattr(self, 't_win', None) is not None:
            preserve.add(self.t_win)

        for child in self.findChildren(QWidget):
            if child == self.bg_label or child in preserve:
                continue
            child.deleteLater()

    def on_teacher_discovered(self, info):
        # Save active teacher address immediately
        self.active_teacher_ip = info.get("ip")
        # Defer UI update to the main thread to avoid touching deleted widgets
        try:
            QTimer.singleShot(0, lambda: self._apply_teacher_info(info))
        except Exception:
            pass

    def _apply_teacher_info(self, info):
        try:
            if hasattr(self, 'status_label') and getattr(self, 'status_label', None) is not None:
                self.status_label.setText(f"Connected: {len(info.get('available_classes', []))} Classes Active")
                self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        except Exception:
            # Widget was likely deleted; ignore update
            pass

    def stop_teacher_server(self):
        """Stop the broadcaster and server threads"""
        if getattr(self, 'broadcaster', None) is not None:
            try:
                self.broadcaster.stop()
            except Exception:
                pass
            self.broadcaster = None
        
        if getattr(self, 'server_thread', None) is not None:
            try:
                self.server_thread.stop()
            except Exception:
                pass
            self.server_thread = None
        
        self.server_started = False
        self.active_teacher_ip = None

    def show_opening_page(self):
        """2. OPENING PAGE - Modernized UI with Logo and Coded Text"""
        # Stop teacher server/broadcaster if running
        self.stop_teacher_server()
        
        self.clear_ui()
        # Instead of a heavy image, use a clean background or a simple logo
        self.bg_label.setPixmap(QPixmap()) # Clear background
        self.bg_label.setStyleSheet("background-color: #F8DD70;") 

        # 2.1 ADD LOGO
        self.logo = QLabel(self)
        self.logo.setPixmap(QPixmap(get_asset_path("logo.png")).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo.setGeometry(375, 80, 150, 150)
        self.logo.show()

        # 2.2 ADD APP TITLE
        self.title = QLabel("PROCTORA", self)
        self.title.setGeometry(0, 240, 900, 50)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 32px; font-weight: bold; color: #0B2C5D; letter-spacing: 2px;")
        self.title.show()

        # 2.3 SUBTITLE
        self.subtitle = QLabel("Anti-Cheat Examination System", self)
        self.subtitle.setGeometry(0, 285, 900, 30)
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("font-size: 14px; color: #666; font-style: italic;")
        self.subtitle.show()

        # 2.4 BUTTONS (Styled as modern blocks)
        self.btn_t = AnimatedBubbleButton("TEACHER PORTAL", self, radius=8)
        self.btn_t.setGeometry(300, 350, 300, 50)
        self.btn_t.clicked.connect(self.show_teacher_page)
        self.btn_t.show()

        self.btn_s = AnimatedBubbleButton("STUDENT PORTAL", self, radius=8, color="#ffffff", text_col="#0B2C5D")
        self.btn_s.setGeometry(300, 415, 300, 50)
        # Add a subtle border to the white button
        # self.btn_s border removed for cleaner appearance
        self.btn_s.clicked.connect(self.show_student_login)
        self.btn_s.show()

    def show_teacher_page(self):
        """3. TEACHER PAGE - Hook networking and display menu"""
        # Explicitly clean up old teacher window
        if hasattr(self, 't_win') and self.t_win is not None:
            try:
                self.t_win.hide()
                self.t_win.deleteLater()
            except Exception:
                pass
            self.t_win = None
        
        self.clear_ui()
        self.bg_label.setPixmap(QPixmap())
        self.bg_label.setStyleSheet("background-color: #F8DD70;")

        if not self.server_started:
            # Start the Lighthouse (UDP) and the Server (TCP)
            classes = [f[:-5] for f in os.listdir(get_data_path("classes")) if f.endswith(".json")]
            self.broadcaster = network_logic.TeacherBroadcaster(classes)
            self.broadcaster.start()

            self.server_thread = teacher.RequestHandler(self)
            self.server_thread.start()
            self.server_started = True

        # 3.0 ADD LOGO - Centered horizontally
        self.logo_teacher = QLabel(self)
        self.logo_teacher.setPixmap(QPixmap(get_asset_path("logo.png")).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo_teacher.setGeometry(400, 20, 100, 100)
        self.logo_teacher.show()

        # 3.0B ADD TITLE - Consistent with student login
        self.teacher_title = QLabel("TEACHER PORTAL", self)
        self.teacher_title.setGeometry(0, 130, 900, 45)
        self.teacher_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.teacher_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0B2C5D;")
        self.teacher_title.show()

        # 3.1 MENU OPTIONS (Existing code continues)
        options = [
            ("GENERATE EXAM", 195, "exam"),
            ("VIEW EXAM LOGS", 265, "logs"),
            ("CREATE NEW CLASS", 335, "create_class"),
            ("MANAGE CLASSES", 405, "manage_class")
        ]

        for text, y, key in options:
            btn = AnimatedBubbleButton(text.title(), self, radius=8, animate=False)
            btn.setGeometry(306, y, 288, 44)
            btn.clicked.connect(lambda ch, k=key: self.launch_teacher(k))
            btn.show()

        back = AnimatedBubbleButton("← Back", self, radius=8, animate=False)
        back.setGeometry(20, 20, 90, 34)
        back.clicked.connect(self.show_opening_page)
        back.show()

    def show_student_login(self):
        """4. STUDENT LOGIN - Professionalized with Coded Labels"""
        # Destroy old student widget if it exists
        if hasattr(self, 's_win') and self.s_win is not None:
            try:
                self.s_win.hide()
                self.s_win.deleteLater()
            except Exception:
                pass
            self.s_win = None
        
        self.clear_ui()
        self.bg_label.setStyleSheet("background-color: #F8DD70;")

        # 4.1 LOGO - Consistent size and positioning with teacher page
        self.logo_sm = QLabel(self)
        self.logo_sm.setPixmap(QPixmap(get_asset_path("logo.png")).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo_sm.setGeometry(400, 20, 100, 100)
        self.logo_sm.show()

        # 4.2 HEADER - Consistent positioning with teacher portal
        self.login_header = QLabel("STUDENT SIGN-IN", self)
        self.login_header.setGeometry(0, 130, 900, 45)
        self.login_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_header.setStyleSheet("font-size: 28px; font-weight: bold; color: #0B2C5D;")
        self.login_header.show()

        # 4.3 STATUS INDICATOR (Live)
        self.status_label = QLabel(self)
        self.status_label.setGeometry(300, 180, 300, 30)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Show connected status if a teacher was discovered, otherwise show offline message
        if self.active_teacher_ip:
            self.on_teacher_discovered({"ip": self.active_teacher_ip, "available_classes": []})
        else:
            self.status_label.setText("Offline — No teacher detected")
            self.status_label.setStyleSheet("color: #dc3545; font-style: italic; font-weight: bold;")
        self.status_label.show()

        # 4.4 INPUTS
        self.name_entry = QLineEdit(self)
        self.name_entry.setPlaceholderText("Full Name")
        self.name_entry.setGeometry(300, 245, 300, 45)
        self.name_entry.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 6px;")
        self.name_entry.show()

        self.pass_entry = QLineEdit(self)
        self.pass_entry.setPlaceholderText("Access Password")
        self.pass_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_entry.setGeometry(300, 305, 300, 45)
        self.pass_entry.setStyleSheet("background-color: #ffffff;")
        self.pass_entry.returnPressed.connect(self.launch_student)
        self.pass_entry.show()

        # 4.5 BUTTONS
        login = AnimatedBubbleButton("SIGN IN", self, radius=8)
        login.setGeometry(300, 375, 300, 50)
        login.clicked.connect(self.launch_student)
        login.show()

        back = AnimatedBubbleButton("← Back", self, radius=8, animate=False)
        back.setGeometry(20, 20, 90, 34)
        back.clicked.connect(self.show_opening_page)
        back.show()
    def launch_teacher(self, page):
        """5. LAUNCH TEACHER - Embed teacher window for specified page"""
        # Destroy old teacher widget if it exists
        if hasattr(self, 't_win') and self.t_win is not None:
            try:
                self.t_win.hide()
                self.t_win.deleteLater()
            except Exception:
                pass
            self.t_win = None
        
        self.clear_ui()
        self.bg_label.setStyleSheet("background-color: #F8DD70;")
        
        # Create embedded teacher widget
        self.t_win = teacher.TeacherWindow(page, self)
        self.t_win.setParent(self)
        self.t_win.setGeometry(0, 0, 900, 600)
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
            # Embed the student UI into this main window instead of opening a new top-level window
            # Reuse existing student widget if present
            if hasattr(self, 's_win') and self.s_win is not None:
                self.s_win.student_name = n
                self.s_win.teacher_ip = self.active_teacher_ip
                self.s_win.student_class = resp.get("classname")
                try:
                    self.s_win.refresh_exam_list()
                except Exception:
                    pass
                # Ensure it's visible
                self.s_win.show()
            else:
                # Clear current UI and create embedded student widget
                self.clear_ui()
                self.s_win = student.StudentWindow(n, self.active_teacher_ip, self, resp["classname"])
                self.s_win.setParent(self)
                self.s_win.setGeometry(0, 0, 900, 600)
                self.s_win.show()
        else:
            QMessageBox.warning(self, "Denied", "Credentials not found on network.")

if __name__ == "__main__":
    # 7. MAIN LOOP - Initialize and run application
    app = QApplication(sys.argv)
    
    # Load custom fonts
    loaded_fonts = load_custom_fonts()
    
    # Light Mode Stylesheet
    app.setStyle('Fusion')
    light_stylesheet = """
    QMainWindow, QWidget, QDialog {
        background-color: #f5f5f5;
        color: #FFD700 ;
        font-family: Poppins;
    }
    QLabel {
        background-color: transparent;
        color: #000000;
        font-family: Poppins;
    }
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        color: #000000;
        border: none;
        border-radius: 4px;
        padding: 4px;
        font-family: Poppins;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: none;
    }
    QPushButton {
        background-color: #0B2C5D;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 4px 8px;
        font-weight: bold;
        font-family: Poppins;
    }
    QPushButton:hover {
        background-color: #154c9e;
    }
    QPushButton:pressed {
        background-color: #0a1f47;
    }
    QComboBox {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 2px;
        font-family: Poppins;
    }
    QComboBox:hover {
        border: 1px solid #0B2C5D;
    }
    QCheckBox, QRadioButton {
        color: #000000;
        background-color: transparent;
        spacing: 5px;
        padding: 1px;
        font-family: Poppins;
    }
    QCheckBox::indicator, QRadioButton::indicator {
        width: 13px;
        height: 13px;
        border: 1.5px solid #0B2C5D;
        border-radius: 2px;
        background-color: #ffffff;
    }
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {
        border: 1.5px solid #154c9e;
        background-color: #f8faff;
    }
    QCheckBox::indicator:checked {
        background-color: #0B2C5D;
        border: 1.5px solid #0B2C5D;
    }
    QRadioButton::indicator {
        border-radius: 6px;
    }
    QRadioButton::indicator:checked {
        background-color: #0B2C5D;
        border: 1.5px solid #0B2C5D;
        border-radius: 6px;
    }
    QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 2px;
        font-family: Poppins;
    }
    QGroupBox {
        color: #000000;
        border: 1px solid #cccccc;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
        font-family: Poppins;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0px 3px 0px 3px;
    }
    QListWidget, QTableWidget, QTreeWidget {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
        gridline-color: #e0e0e0;
        font-family: Poppins;
    }
    QHeaderView::section {
        background-color: #e8e8e8;
        color: #000000;
        padding: 4px;
        border: 1px solid #cccccc;
    }
    QScrollBar:vertical {
        background-color: #f5f5f5;
        width: 12px;
        border: none;
    }
    QScrollBar::handle:vertical {
        background-color: #cccccc;
        border-radius: 6px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #999999;
    }
    """
    app.setStyleSheet(light_stylesheet)
    
    portal = AntiCheatPortal()
    portal.show()
    sys.exit(app.exec())