from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Sistema de Inventario de Laboratorio - V1")

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
