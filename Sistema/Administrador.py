import sys
import hashlib
import cv2
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QCheckBox, QMessageBox, 
                             QStackedWidget, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from database import conectar

class AdminApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión - Administrador")
        self.resize(700, 500)
        self.setStyleSheet("background-color: #f4f6f9; color: #333;")
        
        self.layout_principal = QVBoxLayout()
        self.stacked_widget = QStackedWidget()
        
        # Variables para la cámara y registro temporal
        self.camera = None
        self.timer_camara = QTimer()
        self.timer_camara.timeout.connect(self.actualizar_frame_captura)
        self.detector_qr = cv2.QRCodeDetector()
        self.registro_pendiente = {}
        self.modo_captura = "" # Puede ser "QR" o "FACIAL"
        
        # Pantallas
        self.pantalla_login = self.crear_pantalla_login()
        self.pantalla_registro = self.crear_pantalla_registro()
        self.pantalla_dashboard = self.crear_pantalla_dashboard()
        self.pantalla_captura = self.crear_pantalla_captura()
        
        self.stacked_widget.addWidget(self.pantalla_login)      # Índice 0
        self.stacked_widget.addWidget(self.pantalla_registro)   # Índice 1
        self.stacked_widget.addWidget(self.pantalla_dashboard)  # Índice 2
        self.stacked_widget.addWidget(self.pantalla_captura)    # Índice 3
        
        self.layout_principal.addWidget(self.stacked_widget)
        self.setLayout(self.layout_principal)

    # --- UI: Login (Índice 0) ---
    def crear_pantalla_login(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.txt_login_user = QLineEdit(placeholderText="Usuario (ej. AdminPro)")
        self.txt_login_pass = QLineEdit(placeholderText="Contraseña")
        self.txt_login_pass.setEchoMode(QLineEdit.Password)
        
        btn_login = QPushButton("Iniciar Sesión")
        btn_login.clicked.connect(self.iniciar_sesion)
        
        layout.addWidget(QLabel("<h2>Inicio de Sesión Admin</h2>"))
        layout.addWidget(self.txt_login_user)
        layout.addWidget(self.txt_login_pass)
        layout.addWidget(btn_login)
        widget.setLayout(layout)
        return widget

    # --- UI: Registro Formulario (Índice 1) ---
    def crear_pantalla_registro(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.txt_reg_user = QLineEdit(placeholderText="Nombre de Usuario")
        self.txt_reg_correo = QLineEdit(placeholderText="Correo Institucional")
        self.txt_reg_pass = QLineEdit(placeholderText="Contraseña")
        self.txt_reg_pass.setEchoMode(QLineEdit.Password)
        self.txt_reg_pass_conf = QLineEdit(placeholderText="Confirmar Contraseña")
        self.txt_reg_pass_conf.setEchoMode(QLineEdit.Password)
        
        self.chk_qr = QCheckBox("Añadir Código QR")
        self.chk_facial = QCheckBox("Añadir Reconocimiento Facial")
        
        # Botones Siguiente y Cancelar
        layout_botones = QHBoxLayout()
        btn_siguiente = QPushButton("Siguiente ➔")
        btn_siguiente.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        btn_siguiente.clicked.connect(self.validar_registro)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px;")
        btn_cancelar.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2)) # Vuelve al dashboard
        
        layout_botones.addWidget(btn_cancelar)
        layout_botones.addWidget(btn_siguiente)
        
        layout.addWidget(QLabel("<h2>Registro de Alumnos</h2>"))
        layout.addWidget(self.txt_reg_user)
        layout.addWidget(self.txt_reg_correo)
        layout.addWidget(self.txt_reg_pass)
        layout.addWidget(self.txt_reg_pass_conf)
        layout.addWidget(self.chk_qr)
        layout.addWidget(self.chk_facial)
        layout.addLayout(layout_botones)
        widget.setLayout(layout)
        return widget

    # --- UI: Captura de Cámara (Índice 3) ---
    def crear_pantalla_captura(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.lbl_instruccion_captura = QLabel("Instrucciones...")
        self.lbl_instruccion_captura.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.lbl_instruccion_captura.setAlignment(Qt.AlignCenter)
        
        self.lbl_video_admin = QLabel("Iniciando cámara...")
        self.lbl_video_admin.setAlignment(Qt.AlignCenter)
        self.lbl_video_admin.setMinimumSize(480, 360)
        self.lbl_video_admin.setStyleSheet("background-color: black;")
        
        self.btn_capturar_rostro = QPushButton("📸 Capturar Rostro")
        self.btn_capturar_rostro.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 10px;")
        self.btn_capturar_rostro.clicked.connect(self.extraer_rostro)
        self.btn_capturar_rostro.hide() # Se oculta hasta que toque escaneo facial
        
        btn_cancelar_captura = QPushButton("Cancelar Registro")
        btn_cancelar_captura.clicked.connect(self.detener_captura_y_volver)
        
        layout.addWidget(self.lbl_instruccion_captura)
        layout.addWidget(self.lbl_video_admin)
        layout.addWidget(self.btn_capturar_rostro)
        layout.addWidget(btn_cancelar_captura)
        widget.setLayout(layout)
        return widget

    # --- UI: Dashboard (Índice 2) ---
    def crear_pantalla_dashboard(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.lbl_bienvenida = QLabel("<h2>Panel de Control</h2>")
        
        btn_ir_registro = QPushButton("+ Registrar Nuevo Alumno")
        btn_ir_registro.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        btn_ir_registro.clicked.connect(self.limpiar_y_abrir_registro)
        
        self.tabla_asistencias = QTableWidget(0, 4)
        self.tabla_asistencias.setHorizontalHeaderLabels(["ID", "Usuario", "Fecha/Hora", "Estado"])
        
        btn_cerrar_sesion = QPushButton("Cerrar Sesión")
        btn_cerrar_sesion.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        layout.addWidget(self.lbl_bienvenida)
        layout.addWidget(btn_ir_registro)
        layout.addWidget(self.tabla_asistencias)
        layout.addWidget(btn_cerrar_sesion)
        widget.setLayout(layout)
        return widget


    # ================= LOGICA =================

    def iniciar_sesion(self):
        user = self.txt_login_user.text()
        pwd = hashlib.sha256(self.txt_login_pass.text().encode()).hexdigest()
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM usuarios WHERE usuario=? AND password=?", (user, pwd))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            self.lbl_bienvenida.setText(f"<h2>Bienvenido, Administrador {user}</h2>")
            self.cargar_asistencias()
            self.stacked_widget.setCurrentIndex(2) # Ir al Dashboard
        else:
            QMessageBox.warning(self, "Error", "Credenciales incorrectas")

    def limpiar_y_abrir_registro(self):
        self.txt_reg_user.clear()
        self.txt_reg_correo.clear()
        self.txt_reg_pass.clear()
        self.txt_reg_pass_conf.clear()
        self.chk_qr.setChecked(False)
        self.chk_facial.setChecked(False)
        self.stacked_widget.setCurrentIndex(1)

    def validar_registro(self):
        user = self.txt_reg_user.text()
        correo = self.txt_reg_correo.text()
        p1 = self.txt_reg_pass.text()
        p2 = self.txt_reg_pass_conf.text()
        
        if not user or not p1:
            QMessageBox.warning(self, "Error", "Llene los campos obligatorios")
            return
        if p1 != p2:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
            return
        if not self.chk_qr.isChecked() and not self.chk_facial.isChecked():
            QMessageBox.warning(self, "Error", "Debe seleccionar al menos QR o Reconocimiento Facial")
            return
            
        # Guardamos los datos en memoria para procesarlos tras usar la cámara
        pwd_hash = hashlib.sha256(p1.encode()).hexdigest()
        self.registro_pendiente = {
            "usuario": user, "correo": correo, "password": pwd_hash,
            "req_qr": self.chk_qr.isChecked(),
            "req_facial": self.chk_facial.isChecked(),
            "qr_data": "", "facial_data": ""
        }
        
        # Iniciar cámara y cambiar de pantalla
        self.stacked_widget.setCurrentIndex(3)
        self.iniciar_camara_registro()

    def iniciar_camara_registro(self):
        self.camera = cv2.VideoCapture(0)
        self.timer_camara.start(30)
        self.avanzar_etapa_captura() # Define si empieza pidiendo QR o Cara

    def avanzar_etapa_captura(self):
        # Lógica para decidir qué sigue
        if self.registro_pendiente["req_qr"] and not self.registro_pendiente["qr_data"]:
            self.modo_captura = "QR"
            self.lbl_instruccion_captura.setText(f"Mostrando cámara... Acerque el QR para el alumno: {self.registro_pendiente['usuario']}")
            self.btn_capturar_rostro.hide()
            
        elif self.registro_pendiente["req_facial"] and not self.registro_pendiente["facial_data"]:
            self.modo_captura = "FACIAL"
            self.lbl_instruccion_captura.setText(f"Mire a la cámara y presione Capturar para: {self.registro_pendiente['usuario']}")
            self.btn_capturar_rostro.show()
            
        else:
            # Si ya se completó lo que se pidió, guardar en Base de Datos
            self.guardar_usuario_en_db()

    def actualizar_frame_captura(self):
        ret, frame = self.camera.read()
        if not ret: return

        # Si estamos en modo QR, escaneamos en tiempo real
        if self.modo_captura == "QR":
            data, bbox, _ = self.detector_qr.detectAndDecode(frame)
            if data:
                self.registro_pendiente["qr_data"] = data.strip()
                QMessageBox.information(self, "Éxito", "Código QR asimilado correctamente.")
                self.avanzar_etapa_captura()

        # Dibujar en pantalla de PyQt5
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        img_qt = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.lbl_video_admin.setPixmap(QPixmap.fromImage(img_qt).scaled(self.lbl_video_admin.width(), self.lbl_video_admin.height(), Qt.KeepAspectRatio))

    def extraer_rostro(self):
        # Función que se activa al apretar el botón de "Capturar Rostro"
        ret, frame = self.camera.read()
        if not ret: return
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            import face_recognition
            encodings = face_recognition.face_encodings(frame_rgb)
            if encodings:
                # Convertimos el array de la IA a texto para guardarlo en la Base de Datos
                self.registro_pendiente["facial_data"] = json.dumps(encodings[0].tolist())
                QMessageBox.information(self, "Éxito", "Rostro asimilado correctamente.")
                self.avanzar_etapa_captura()
            else:
                QMessageBox.warning(self, "Error", "No se detectó un rostro claro. Acerquese e intente de nuevo.")
        except ImportError:
            QMessageBox.critical(self, "Error", "La librería de IA (face_recognition) no está instalada.")
            self.detener_captura_y_volver()

    def guardar_usuario_en_db(self):
        self.detener_captura_y_volver()
        
        try:
            conn = conectar()
            cursor = conn.cursor()
            # Guardamos el código QR y el texto del Rostro directamente en las columnas correspondientes
            cursor.execute('''
                INSERT INTO usuarios (usuario, correo, password, tiene_qr, tiene_facial, rol)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.registro_pendiente["usuario"], self.registro_pendiente["correo"], 
                  self.registro_pendiente["password"], self.registro_pendiente["qr_data"], 
                  self.registro_pendiente["facial_data"], 'alumno'))
            conn.commit()
            QMessageBox.information(self, "Finalizado", "Alumno registrado con sus datos biométricos y guardado en la Base de Datos.")
            self.cargar_asistencias()
        except Exception as e:
            QMessageBox.warning(self, "Error Base de Datos", f"El usuario ya existe o hubo un error: {e}")
        finally:
            conn.close()

    def detener_captura_y_volver(self):
        self.timer_camara.stop()
        if self.camera and self.camera.isOpened():
            self.camera.release()
        self.stacked_widget.setCurrentIndex(2) # Vuelve al Dashboard
        
    def cargar_asistencias(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, u.usuario, a.fecha_hora, a.estado 
            FROM asistencias a JOIN usuarios u ON a.usuario_id = u.id
            ORDER BY a.fecha_hora DESC
        ''')
        datos = cursor.fetchall()
        conn.close()
        
        self.tabla_asistencias.setRowCount(0)
        for row_num, row_data in enumerate(datos):
            self.tabla_asistencias.insertRow(row_num)
            for col_num, data in enumerate(row_data):
                self.tabla_asistencias.setItem(row_num, col_num, QTableWidgetItem(str(data)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = AdminApp()
    ventana.show()
    sys.exit(app.exec_())