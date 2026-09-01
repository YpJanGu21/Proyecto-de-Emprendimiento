import sqlite3
import hashlib

def conectar():
    return sqlite3.connect("asistencia.db")
    

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            correo TEXT,
            password TEXT,
            tiene_qr BOOLEAN,
            tiene_facial BOOLEAN,
            rol TEXT
        )
    ''')
    
    # Tabla de Asistencias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    
    # Crear el AdminPro por defecto si no existe
    cursor.execute("SELECT * FROM usuarios WHERE usuario = 'AdminPro'")
    if not cursor.fetchone():
        pwd_hash = hashlib.sha256("Admin1234".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (usuario, correo, password, tiene_qr, tiene_facial, rol)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('AdminPro', 'admin@institucion.cl', pwd_hash, False, False, 'superadmin'))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_db()
    print("Base de datos inicializada correctamente.")