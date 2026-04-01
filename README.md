# Turnip Exchanger 🌱

Plataforma para intercambio de nabos de Animal Crossing: New Horizons.

---

## Requisitos previos

- [Python 3.10+](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Credenciales OAuth de [Discord](https://discord.com/developers/applications) y/o [Google](https://console.cloud.google.com)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd turnip-exchanger
```

### 2. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el `.env` con tus valores:

```properties
# Genera un SECRET_KEY seguro con:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=tu-clave-secreta

DATABASE_URL=postgresql://turnip:turnip1234@localhost:5434/turnip_exchanger

DISCORD_CLIENT_ID=...
DISCORD_CLIENT_SECRET=...
DISCORD_REDIRECT_URI=http://localhost:8000/api/v1/auth/discord/callback

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

> ⚠️ El `.env` nunca debe subirse a Git. Ya está incluido en `.gitignore`.

### 4. Arrancar la base de datos

```bash
docker compose up -d
```

Esto levanta PostgreSQL en el puerto **5434** y Adminer en el **8080**.

Para ver los logs si algo falla:
```bash
docker compose logs db
```

### 5. Aplicar las migraciones

```bash
alembic upgrade head
```

Esto crea todas las tablas en la base de datos.

### 6. Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

La API estará disponible en:
- **API:** http://localhost:8000
- **Documentación:** http://localhost:8000/docs
- **Adminer (BD):** http://localhost:8080

---

## Credenciales de Adminer

| Campo | Valor |
|---|---|
| Sistema | PostgreSQL |
| Servidor | `db` |
| Usuario | `turnip` |
| Contraseña | `turnip1234` |
| Base de datos | `turnip_exchanger` |

> El servidor es `db` y no `localhost` porque Adminer se conecta desde dentro de Docker.

---

## Flujo de trabajo con migraciones

Cada vez que modifiques un modelo, necesitas generar y aplicar una nueva migración:

```bash
# 1. Generar la migración (detecta cambios automáticamente)
alembic revision --autogenerate -m "descripcion del cambio"

# 2. Aplicar la migración
alembic upgrade head
```

Otros comandos útiles:

```bash
# Ver el historial de migraciones
alembic history

# Revertir la última migración
alembic downgrade -1

# Ver en qué migración estás ahora
alembic current
```

---

## Resetear la base de datos (solo esta app)

Si necesitas empezar desde cero sin afectar otros proyectos de Docker:

```bash
# 1. Para los contenedores de esta app
docker compose down

# 2. Borra SOLO el volumen de esta app
docker volume rm tfc_postgres_data

# 3. Vuelve a levantar
docker compose up -d

# 4. Vuelve a aplicar las migraciones
alembic upgrade head
```

> ℹ️ El nombre del volumen (`tfc_postgres_data`) viene del nombre de la carpeta del proyecto. Si la carpeta se llama diferente, ajusta el nombre. Puedes ver todos tus volúmenes con `docker volume ls`.

---

## Estructura del proyecto

```
turnip-exchanger/
├── app/
│   ├── main.py                  # Entrada de la aplicación FastAPI
│   ├── core/
│   │   ├── config.py            # Variables de entorno y configuración
│   │   └── security.py          # Generación y validación de JWT
│   ├── db/
│   │   ├── base.py              # Base declarativa de SQLAlchemy
│   │   └── session.py           # Conexión y sesión a la BD
│   ├── models/                  # Tablas de la base de datos
│   ├── schemas/                 # Validación de datos (Pydantic)
│   ├── services/                # Lógica de negocio
│   └── api/v1/
│       ├── dependencies.py      # Autenticación y permisos
│       ├── router.py            # Registro de endpoints
│       └── endpoints/           # Endpoints por recurso
├── alembic/                     # Migraciones de base de datos
├── tests/                       # Tests
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── .env.example
```
