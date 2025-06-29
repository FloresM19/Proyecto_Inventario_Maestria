-- Sistema de Inventario y Préstamo de Equipos de Laboratorio

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

-- Insertar usuarios de prueba
INSERT INTO usuarios (username, password, nombre_completo, email, tipo_usuario) VALUES
('admin', 'admin123', 'Administrador del Sistema', 'admin@laboratorio.edu', 'admin'),
('profesor1', 'prof123', 'Dr. Juan Pérez', 'jperez@laboratorio.edu', 'profesor'),
('estudiante1', 'est123', 'María González', 'mgonzalez@estudiantes.edu', 'estudiante');

-- Crear índices para mejorar rendimiento
CREATE INDEX idx_usuarios_username ON usuarios(username);
