# 📋 Guía de Gestión de Permisos de Usuarios

Esta guía explica cómo gestionar usuarios y permisos en el sistema de administración del hotel.

## 🏗️ Arquitectura del Sistema de Permisos

El sistema utiliza un modelo de permisos basado en **roles** con las siguientes entidades:

- **Usuario**: Usuario del sistema Django
- **Rol**: Define un conjunto de permisos (ej: Super Administrador, Recepcionista)
- **Permiso**: Acción específica en un módulo (ej: "crear" en "empleados")
- **UsuarioRol**: Asigna roles a usuarios
- **RolPermiso**: Asigna permisos a roles

## 🎭 Roles Disponibles

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| `super_admin` | Super Administrador | Acceso completo a todos los módulos |
| `admin_general` | Administrador General | Gestión general sin configuración del sistema |
| `recepcionista` | Recepcionista | Gestión de reservas, huéspedes y servicios básicos |
| `solo_lectura` | Solo Lectura | Solo visualización de información |

## 🔧 Comandos de Gestión

### 1. Asignar Rol a Usuario

```bash
# Asignar rol super_admin al usuario benja y marcarlo como staff
docker compose exec web python manage.py asignar_rol benja super_admin --staff

# Asignar rol recepcionista sin marcar como staff
docker compose exec web python manage.py asignar_rol maria recepcionista

# Ver roles disponibles
docker compose exec web python manage.py asignar_rol --listar-roles

# Asignar rol y ver permisos resultantes
docker compose exec web python manage.py asignar_rol juan admin_general --staff --ver-permisos
```

### 2. Gestionar Usuarios

```bash
# Listar todos los usuarios
docker compose exec web python manage.py gestionar_usuarios --listar

# Ver información detallada de un usuario
docker compose exec web python manage.py gestionar_usuarios --usuario benja

# Remover rol de un usuario
docker compose exec web python manage.py gestionar_usuarios --remover-rol benja recepcionista

# Activar/desactivar usuario
docker compose exec web python manage.py gestionar_usuarios --activar-usuario maria
docker compose exec web python manage.py gestionar_usuarios --desactivar-usuario juan
```

### 3. Inicializar Sistema de Roles

```bash
# Crear roles y permisos básicos
docker compose exec web python manage.py init_roles

# Resetear y recrear todo el sistema de permisos
docker compose exec web python manage.py init_roles --reset
```

## 🔐 Tipos de Permisos por Módulo

### Módulos Disponibles:
- **empleados**: Gestión de empleados
- **habitaciones**: Gestión de habitaciones
- **reservas**: Gestión de reservas
- **huespedes**: Gestión de huéspedes
- **servicios**: Gestión de servicios
- **planes**: Gestión de planes
- **promociones**: Gestión de promociones
- **reportes**: Generación de reportes
- **dashboard**: Acceso al panel principal
- **configuracion**: Configuración del sistema
- **usuarios**: Gestión de usuarios
- **roles**: Gestión de roles

### Acciones Disponibles:
- **ver**: Visualizar información
- **crear**: Crear nuevos registros
- **editar**: Modificar registros existentes
- **eliminar**: Eliminar registros
- **exportar**: Exportar datos
- **aprobar**: Aprobar acciones
- **confirmar**: Confirmar operaciones
- **cancelar**: Cancelar operaciones

## 👥 Casos de Uso Comunes

### Crear un Nuevo Administrador
```bash
# 1. Crear usuario (si no existe)
docker compose exec web python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.create_user('nuevo_admin', 'admin@hotel.com', 'password123')
print(f'Usuario {user.username} creado')
"

# 2. Asignar rol de administrador
docker compose exec web python manage.py asignar_rol nuevo_admin admin_general --staff
```

### Crear un Recepcionista
```bash
# 1. Crear usuario
docker compose exec web python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.create_user('recepcionista1', 'recepcion@hotel.com', 'password123')
print(f'Usuario {user.username} creado')
"

# 2. Asignar rol de recepcionista
docker compose exec web python manage.py asignar_rol recepcionista1 recepcionista --staff
```

### Dar Máximos Permisos a un Usuario
```bash
# Asignar rol super_admin (como se hizo con benja)
docker compose exec web python manage.py asignar_rol usuario super_admin --staff --ver-permisos
```

## 🛡️ Verificación de Permisos

### En el Código
```python
from administracion.permissions import usuario_tiene_permiso

# Verificar si un usuario puede crear empleados
if usuario_tiene_permiso(request.user, 'empleados', 'crear'):
    # Permitir acción
    pass
```

### Decoradores de Vista
```python
from administracion.permissions import requiere_staff_y_permiso

@requiere_staff_y_permiso('empleados', 'crear')
def crear_empleado(request):
    # Solo usuarios con permiso pueden acceder
    pass
```

## 🔍 Verificar Estado de un Usuario

```bash
# Ver información completa del usuario
docker compose exec web python manage.py gestionar_usuarios --usuario nombre_usuario

# Verificar permisos específicos
docker compose exec web python manage.py shell -c "
from django.contrib.auth.models import User
from administracion.permissions import obtener_permisos_usuario

user = User.objects.get(username='nombre_usuario')
permisos = obtener_permisos_usuario(user)
for modulo, acciones in permisos.items():
    print(f'{modulo}: {acciones}')
"
```

## ⚠️ Consideraciones Importantes

1. **Staff Status**: Para acceder al sistema de administración, el usuario debe tener `is_staff=True`
2. **Roles Activos**: Solo los roles con `activo=True` otorgan permisos
3. **Super Admin**: El rol `super_admin` tiene acceso completo a todos los módulos
4. **Seguridad**: Nunca asignes permisos innecesarios a los usuarios

## 🚀 Acceso al Sistema

1. **URL de Login**: `http://localhost:8000/administracion/login/`
2. **Credenciales**: Usar el username y password del usuario
3. **Redirección**: Después del login exitoso, redirige al dashboard

## 📊 Ejemplo: Estado Actual del Usuario 'benja'

```
=== INFORMACIÓN DE benja ===
ID: 1
Email: beninja1912@gmail.com
Staff: Sí
Superuser: No
Activo: Sí

Roles asignados:
• Super Administrador

Permisos por módulo:
• configuracion: editar, ver
• dashboard: ver
• empleados: crear, editar, eliminar, ver
• habitaciones: crear, editar, eliminar, ver
• huespedes: crear, editar, eliminar, ver
• planes: crear, editar, eliminar, ver
• promociones: crear, editar, eliminar, ver
• reportes: exportar, generar, ver
• reservas: cancelar, confirmar, crear, editar, eliminar, ver
• roles: asignar, crear, editar, ver
• servicios: crear, editar, eliminar, ver
• usuarios: crear, editar, eliminar, ver
```

El usuario **benja** ahora tiene los máximos permisos posibles en el sistema y puede acceder a todas las funcionalidades de administración.