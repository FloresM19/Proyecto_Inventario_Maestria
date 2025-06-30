from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Sistema de Inventario de Laboratorio - V2")

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

# ========== EQUIPOS - NUEVO EN V2.0 ==========

@app.get("/equipos")
async def get_equipos():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, descripcion, estado, created_at FROM equipos ORDER BY id")
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

        # Verificar que el equipo existe
        cur.execute("SELECT id FROM equipos WHERE id = %s", (equipo_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Equipo no encontrado")

        # Actualizar equipo
        cur.execute(
            "UPDATE equipos SET nombre = %s, descripcion = %s, estado = %s WHERE id = %s",
            (equipo.nombre, equipo.descripcion, equipo.estado, equipo_id)
        )
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
 