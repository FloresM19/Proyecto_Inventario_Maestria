from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, timedelta

app = FastAPI(title="Sistema de Inventario de Laboratorio - V4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class LoginRequest(BaseModel):
    username: str
    password: str

class EquipoCreate(BaseModel):
    nombre: str
    descripcion: str = ""
    estado: str = "disponible"

class EquipoUpdate(BaseModel):
    nombre: str
    descripcion: str = ""
    estado: str

class PrestamoCreate(BaseModel):
    equipo_id: int
    usuario_id: int
    motivo: str

# Conexión a base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="db",
            database="inventario_laboratorio",
            user="admin",
            password="password123",
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

# Función para registrar en historial - NUEVA EN V4.0
def registrar_historial(conn, equipo_id, estado_anterior, estado_nuevo, usuario_id, motivo):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO historial_equipos (equipo_id, estado_anterior, estado_nuevo, usuario_responsable, motivo)
            VALUES (%s, %s, %s, %s, %s)
        """, (equipo_id, estado_anterior, estado_nuevo, usuario_id, motivo))
        print(f"✅ Historial registrado: {estado_anterior} -> {estado_nuevo} para equipo {equipo_id}")
    except Exception as e:
        print(f"❌ Error registrando historial: {str(e)}")
        # No lanzar excepción para no interrumpir la operación principal

# ========== AUTENTICACIÓN ==========

@app.post("/login")
async def login(login_data: LoginRequest):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, nombre_completo, tipo_usuario FROM usuarios WHERE username = %s AND password = %s AND activo = TRUE",
            (login_data.username, login_data.password)
        )
        user = cur.fetchone()

        if user:
            return {
                "success": True,
                "message": "Login exitoso",
                "user": dict(user)
            }
        else:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    finally:
        conn.close()

# ========== EQUIPOS ==========

@app.get("/equipos")
async def get_equipos():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, descripcion, estado, created_at FROM equipos ORDER BY id")
        return cur.fetchall()
    finally:
        conn.close()

@app.get("/equipos/disponibles")
async def get_equipos_disponibles():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, descripcion, estado FROM equipos WHERE estado = 'disponible' ORDER BY id")
        return cur.fetchall()
    finally:
        conn.close()

@app.get("/equipos/{equipo_id}")
async def get_equipo(equipo_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, descripcion, estado, created_at FROM equipos WHERE id = %s", (equipo_id,))
        equipo = cur.fetchone()

        if equipo:
            return equipo
        else:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
    finally:
        conn.close()

@app.post("/equipos")
async def crear_equipo(equipo: EquipoCreate):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO equipos (nombre, descripcion, estado) VALUES (%s, %s, %s) RETURNING id",
            (equipo.nombre, equipo.descripcion, equipo.estado)
        )
        equipo_id = cur.fetchone()['id']

        # Registrar en historial
        registrar_historial(conn, equipo_id, 'nuevo', equipo.estado, None, f"Equipo creado: {equipo.nombre}")

        conn.commit()
        return {"id": equipo_id, "message": "Equipo creado exitosamente"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/equipos/{equipo_id}")
async def actualizar_equipo(equipo_id: int, equipo: EquipoUpdate):
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Verificar que el equipo existe y obtener estado actual
        cur.execute("SELECT estado FROM equipos WHERE id = %s", (equipo_id,))
        equipo_actual = cur.fetchone()
        if not equipo_actual:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")

        estado_anterior = equipo_actual['estado']

        # Actualizar equipo
        cur.execute(
            "UPDATE equipos SET nombre = %s, descripcion = %s, estado = %s WHERE id = %s",
            (equipo.nombre, equipo.descripcion, equipo.estado, equipo_id)
        )

        # Registrar en historial si cambió el estado
        if estado_anterior != equipo.estado:
            registrar_historial(conn, equipo_id, estado_anterior, equipo.estado, None, "Equipo actualizado")

        conn.commit()
        return {"message": "Equipo actualizado exitosamente"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/equipos/{equipo_id}")
async def eliminar_equipo(equipo_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Verificar que el equipo existe
        cur.execute("SELECT id FROM equipos WHERE id = %s", (equipo_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Equipo no encontrado")

        # Registrar en historial antes de eliminar
        registrar_historial(conn, equipo_id, 'existente', 'eliminado', None, "Equipo eliminado del sistema")

        # Eliminar equipo
        cur.execute("DELETE FROM equipos WHERE id = %s", (equipo_id,))
        conn.commit()
        return {"message": "Equipo eliminado exitosamente"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/equipos/disponibles/count")
async def count_equipos_disponibles():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM equipos WHERE estado = 'disponible'")
        result = cur.fetchone()
        return {"equipos_disponibles": result['total']}
    finally:
        conn.close()
# ========== PRÉSTAMOS ==========

@app.get("/prestamos")
async def get_prestamos():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.equipo_id, p.usuario_id, p.motivo_prestamo as motivo,
                   p.fecha_prestamo, p.fecha_devolucion_real as fecha_devolucion,
                   p.estado, e.nombre as equipo_nombre, u.nombre_completo as usuario_nombre
            FROM prestamos p
            JOIN equipos e ON p.equipo_id = e.id
            JOIN usuarios u ON p.usuario_id = u.id
            ORDER BY p.fecha_prestamo DESC
        """)
        return cur.fetchall()
    finally:
        conn.close()

@app.get("/prestamos/usuario/{usuario_id}")
async def get_prestamos_usuario(usuario_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.equipo_id, p.motivo_prestamo as motivo,
                   p.fecha_prestamo, p.fecha_devolucion_real as fecha_devolucion,
                   p.estado, e.nombre as equipo_nombre
            FROM prestamos p
            JOIN equipos e ON p.equipo_id = e.id
            WHERE p.usuario_id = %s
            ORDER BY p.fecha_prestamo DESC
        """, (usuario_id,))
        return cur.fetchall()
    finally:
        conn.close()

@app.post("/prestamos")
async def crear_prestamo(prestamo: PrestamoCreate):
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Verificar equipo disponible
        cur.execute("SELECT estado, nombre FROM equipos WHERE id = %s", (prestamo.equipo_id,))
        equipo = cur.fetchone()

        if not equipo:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")

        if equipo['estado'] != 'disponible':
            raise HTTPException(status_code=400, detail="El equipo no está disponible")

        # Verificar usuario existe
        cur.execute("SELECT nombre_completo FROM usuarios WHERE id = %s AND activo = TRUE", (prestamo.usuario_id,))
        usuario = cur.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Crear préstamo
        fecha_devolucion = date.today() + timedelta(days=7)
        cur.execute("""
            INSERT INTO prestamos (equipo_id, usuario_id, fecha_devolucion_esperada, motivo_prestamo, estado)
            VALUES (%s, %s, %s, %s, 'activo') RETURNING id
        """, (prestamo.equipo_id, prestamo.usuario_id, fecha_devolucion, prestamo.motivo))

        prestamo_id = cur.fetchone()['id']

        # Cambiar estado del equipo
        cur.execute("UPDATE equipos SET estado = 'prestado' WHERE id = %s", (prestamo.equipo_id,))

        # Registrar en historial
        registrar_historial(conn, prestamo.equipo_id, 'disponible', 'prestado', prestamo.usuario_id, f"Préstamo: {prestamo.motivo}")

        conn.commit()
        return {"id": prestamo_id, "message": "Préstamo creado exitosamente"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/prestamos/{prestamo_id}/devolver")
async def devolver_equipo(prestamo_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Obtener información del préstamo
        cur.execute("SELECT equipo_id, usuario_id FROM prestamos WHERE id = %s AND estado = 'activo'", (prestamo_id,))
        prestamo = cur.fetchone()

        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo activo no encontrado")

        # Actualizar préstamo
        cur.execute(
            "UPDATE prestamos SET estado = 'devuelto', fecha_devolucion_real = CURRENT_TIMESTAMP WHERE id = %s",
            (prestamo_id,)
        )

        # Cambiar estado del equipo
        cur.execute("UPDATE equipos SET estado = 'disponible' WHERE id = %s", (prestamo['equipo_id'],))

        # Registrar en historial
        registrar_historial(conn, prestamo['equipo_id'], 'prestado', 'disponible', prestamo['usuario_id'], "Devolución de préstamo")

        conn.commit()
        return {"message": "Devolución registrada exitosamente"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ========== HISTORIAL - NUEVO EN V4.0 ==========

@app.get("/historial")
async def get_historial(limit: int = 50):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT h.id, h.equipo_id, h.estado_anterior, h.estado_nuevo, 
                   h.usuario_responsable, h.motivo, h.fecha_cambio,
                   e.nombre as equipo_nombre,
                   u.nombre_completo as usuario_nombre
            FROM historial_equipos h
            JOIN equipos e ON h.equipo_id = e.id
            LEFT JOIN usuarios u ON h.usuario_responsable = u.id
            ORDER BY h.fecha_cambio DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()
    finally:
        conn.close()

@app.get("/historial/equipo/{equipo_id}")
async def get_historial_equipo(equipo_id: int):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT h.id, h.estado_anterior, h.estado_nuevo, 
                   h.usuario_responsable, h.motivo, h.fecha_cambio,
                   e.nombre as equipo_nombre,
                   u.nombre_completo as usuario_nombre
            FROM historial_equipos h
            JOIN equipos e ON h.equipo_id = e.id
            LEFT JOIN usuarios u ON h.usuario_responsable = u.id
            WHERE h.equipo_id = %s
            ORDER BY h.fecha_cambio DESC
        """, (equipo_id,))
        return cur.fetchall()
    finally:
        conn.close()
