# Sistema de Gestión de PQRS para Empresas Públicas

## Descripción del Proyecto
Este proyecto implementa un sistema web de gestión de PQRS (Peticiones, Quejas, Reclamos y Sugerencias) para empresas públicas, desarrollado bajo el marco SCRUM. El objetivo es digitalizar y mejorar el proceso de atención al ciudadano, garantizando transparencia, eficiencia y cumplimiento normativo.

## Metodología SCRUM
- **Product Owner:** [Nombre]
- **Scrum Master:** [Nombre]
- **Equipo de Desarrollo:** [Nombres]

## Sprints Planificados
1. **Sprint 1: Registro de Ciudadanos** (Actual)
   - Historia de Usuario: Como ciudadano, quiero registrarme en el sistema para poder enviar solicitudes oficiales.
   - Funcionalidades: Registro y login básico para ciudadanos.

2. **Sprint 2: Gestión de PQRS**
   - Registro de solicitudes, asignación automática de radicado.

3. **Sprint 3: Seguimiento y Notificaciones**
   - Consulta de estado, notificaciones por email.

4. **Sprint 4: Panel de Administración**
   - Gestión de solicitudes por funcionarios.

5. **Sprint 5: Reportes y Estadísticas**
   - Generación de reportes y cumplimiento normativo.

## Tecnologías Utilizadas
- **Framework:** Reflex (Python)
- **Base de Datos:** SQLModel (SQLite/PostgreSQL)
- **Autenticación:** bcrypt
- **Frontend:** Reflex UI Components

## Instalación y Ejecución
1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar la aplicación: `reflex run`
3. Acceder en: http://localhost:3000

## Estructura del Proyecto
- `autenticacion.py`: Archivo principal de la aplicación
- `usuario_model.py`: Modelo de datos para usuarios
- `rxconfig.py`: Configuración de Reflex

## Requisitos Funcionales (Resumidos)
- Gestión de usuarios con roles (Ciudadano, Funcionario, Administrador)
- Registro y seguimiento de PQRS
- Cumplimiento con Ley 1755 de 2015
- Reportes y estadísticas

## Próximos Pasos
- Implementar módulos adicionales según sprints.
- Integrar notificaciones por email.
- Desplegar en producción.