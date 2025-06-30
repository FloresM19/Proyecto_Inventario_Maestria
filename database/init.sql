-- Sistema de Inventario y Préstamo de Equipos de Laboratorio
-- Versión 2.0: Login + Gestión de Equipos - Script de inicialización de la base de datos

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    tipo_usuario VARCHAR(20) DEFAULT 'estudiante', -- estudiante, profesor, admin
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de equipos de laboratorio - NUEVA EN V2.0
CREATE TABLE IF NOT EXISTS equipos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'disponible', -- disponible, prestado
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar usuarios de prueba
INSERT INTO usuarios (username, password, nombre_completo, email, tipo_usuario) VALUES
('admin', 'admin123', 'Administrador del Sistema', 'admin@laboratorio.edu', 'admin'),
('profesor1', 'prof123', 'Dr. Juan Pérez', 'jperez@laboratorio.edu', 'profesor'),
('estudiante1', 'est123', 'María González', 'mgonzalez@estudiantes.edu', 'estudiante');

-- Insertar equipos de prueba - NUEVO EN V2.0
INSERT INTO equipos (nombre, descripcion, estado) VALUES
('Cable HDMI 2m', 'Cable HDMI de 2 metros para conexiones', 'disponible'),
('Cable HDMI 5m', 'Cable HDMI de 5 metros para conexiones largas', 'disponible'),
('Proyector Epson', 'Proyector para presentaciones', 'disponible'),
('Proyector BenQ', 'Proyector de alta resolución', 'disponible'),
('Laptop Dell Inspiron', 'Laptop para desarrollo y presentaciones', 'disponible'),
('Laptop HP Pavilion', 'Laptop para estudiantes', 'disponible'),
('Adaptador USB-C a HDMI', 'Adaptador para conectar dispositivos USB-C', 'disponible'),
('Micrófono inalámbrico', 'Micrófono para presentaciones', 'disponible'),
('Cámara web HD', 'Cámara para videoconferencias', 'disponible');

-- Crear índices para mejorar rendimiento
CREATE INDEX idx_usuarios_username ON usuarios(username);
CREATE INDEX idx_equipos_estado ON equipos(estado);