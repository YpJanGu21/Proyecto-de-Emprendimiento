import sys
from datetime import datetime, time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QMessageBox)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from database import conectar

class UsuarioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terminal de Acceso")
        self.resize(800, 500)
        
        layout_principal = QHBoxLayout()
        
        # --- Panel Izquierdo: Botones de ingreso ---
        panel_izq = QVBoxLayout()
        lbl_instruccion = QLabel("<h2>Seleccione su método de ingreso</h2>")
        
        btn_qr = QPushButton("Ingreso por Código QR")
        btn_qr.setMinimumHeight(100)
        btn_qr.clicked.connect(self.simular_escaneo_qr) # Reemplazar con lógica cv2
        
        btn_facial = QPushButton("Reconocimiento Facial")
        btn_facial.setMinimumHeight(100)
        btn_facial.clicked.connect(self.simular_escaneo_facial) # Reemplazar con lógica cv2
        
        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        panel_izq.addWidget(lbl_instruccion)
        panel_izq.addWidget(btn_qr)
        panel_izq.addWidget(btn_facial)
        panel_izq.addWidget(self.lbl_resultado)
        
        # --- Panel Derecho: Historial Lateral ---
        panel_der = QVBoxLayout()
        panel_der.addWidget(QLabel("<h3>Últimos 10 Ingresos</h3>"))
        
        self.lista_historial = QListWidget()
        panel_der.addWidget(self.lista_historial)
        
        layout_principal.addLayout(panel_izq, 2)
        layout_principal.addLayout(panel_der, 1)
        self.setLayout(layout_principal)
        
        self.actualizar_historial_lateral()

    def registrar_ingreso(self, id_usuario, nombre_usuario):
        ahora = datetime.now()
        hora_actual = ahora.time()
        
        # Definir rango de hora (7:30 a 8:20)
        hora_inicio = time(7, 30)
        hora_fin = time(8, 20)
        
        if hora_inicio <= hora_actual <= hora_fin:
            estado = "A Tiempo"
            color = "green"
        else:
            estado = "Atrasado/Fuera de horario"
            color = "red"
            
        mensaje = f"El alumno {nombre_usuario} llegó a las {ahora.strftime('%H:%M:%S')}"
        self.lbl_resultado.setText(mensaje)
        self.lbl_resultado.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        
        # Guardar en base de datos
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO asistencias (usuario_id, estado) VALUES (?, ?)", (id_usuario, estado))
        conn.commit()
        conn.close()
        
        self.actualizar_historial_lateral()

    def actualizar_historial_lateral(self):
        self.lista_historial.clear()
        conn = conectar()
        cursor = conn.cursor()
        # Traer solo los últimos 10
        cursor.execute('''
            SELECT u.usuario, a.fecha_hora, a.estado 
            FROM asistencias a JOIN usuarios u ON a.usuario_id = u.id
            ORDER BY a.fecha_hora DESC LIMIT 10
        ''')
        datos = cursor.fetchall()
        conn.close()
        
        for fila in datos:
            item = f"{fila[0]} - {fila[1][-8:]}" # Nombre - Hora
            self.lista_historial.addItem(item)

    # --- Funciones Mock (Reemplazar con OpenCV y modelos) ---
    def simular_escaneo_qr(self):
        # Aquí va tu código de cv2.VideoCapture() y cv2.QRCodeDetector()
        # Para el ejemplo, simulamos que detectó al usuario con ID 2
        self.registrar_ingreso(2, "AlumnoPrueba") 

    def simular_escaneo_facial(self):
        # Aquí va tu código de face_recognition
        self.registrar_ingreso(2, "AlumnoPrueba")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = UsuarioApp()
    ventana.show()
    sys.exit(app.exec_())