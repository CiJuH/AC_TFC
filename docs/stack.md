# Stack del backend

## FastAPI
Framework web para construir APIs en Python. Define los endpoints (`@router.get`, `@router.post`...), valida los datos de entrada y salida automáticamente, y genera documentación interactiva en `/docs`.

**En este proyecto:** el punto de entrada es `app/main.py`. Los endpoints se organizan en `app/api/v1/endpoints/`.

---

## SQLAlchemy (async)
ORM (Object-Relational Mapper): permite trabajar con la base de datos usando clases Python en lugar de SQL puro. Cada clase en `app/models/` representa una tabla.

Usamos la versión **async** con `AsyncSession` para que las queries a la BD no bloqueen el servidor mientras esperan respuesta.

**En este proyecto:** los modelos están en `app/models/`. La sesión se obtiene via `get_db()` en `app/db/session.py`.

---

## Alembic
Gestiona las migraciones de base de datos: los cambios en el esquema (crear tablas, añadir columnas, renombrar...) se guardan como scripts versionados en `alembic/versions/`.

Flujo de trabajo:
1. Cambias un modelo en `app/models/`
2. Ejecutas `alembic revision --autogenerate -m "descripcion"` → genera el script
3. Ejecutas `alembic upgrade head` → aplica el cambio a la BD

**Importante — cambios en enums:**

Alembic compara tablas y columnas, pero no el contenido de los tipos enum. Por eso cuando añades, renombras o eliminas un valor de un enum, el script generado queda vacío (`pass`) y hay que editarlo a mano.

Casos y cómo tratarlos:

- **Añadir un valor** (ej: añadir `'mod'` a `UserRole`):
  ```python
  # upgrade
  op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'mod'")
  # downgrade: PostgreSQL no permite eliminar valores de un enum directamente, dejar pass
  ```

- **Renombrar un valor** (ej: `'open'` → `'active'` en `QueueStatus`):
  ```python
  # upgrade
  op.execute("ALTER TYPE queuestatus RENAME VALUE 'open' TO 'active'")
  # downgrade
  op.execute("ALTER TYPE queuestatus RENAME VALUE 'active' TO 'open'")
  ```

- **Crear un tipo nuevo para una columna en tabla existente** (ej: añadir columna con enum nuevo a tabla ya existente):
  ```python
  # upgrade — hay que crear el tipo antes del add_column
  sa.Enum('valor1', 'valor2', name='nombretipo').create(op.get_bind())
  op.add_column('tabla', sa.Column('col', sa.Enum('valor1', 'valor2', name='nombretipo')))
  # downgrade — hay que dropearlo después del drop_column
  op.drop_column('tabla', 'col')
  sa.Enum(name='nombretipo').drop(op.get_bind())
  ```
  > Nota: cuando Alembic hace `CREATE TABLE` con una columna enum, crea el tipo automáticamente. El problema ocurre solo con `ALTER TABLE ADD COLUMN`.

---

## Pydantic
Librería de validación de datos. FastAPI la usa para definir qué datos acepta y devuelve cada endpoint.

Los **schemas** (en `app/schemas/`) son distintos de los modelos SQLAlchemy:
- Los modelos SQLAlchemy representan las tablas
- Los schemas Pydantic representan los datos de la API (requests y responses)

Ejemplo: el modelo `User` tiene `password_hash`, pero el schema `UserResponse` no lo expone.

**En este proyecto:** también usada en `app/core/config.py` (`BaseSettings`) para cargar variables de entorno del `.env`.

### Tipos de schema por recurso

Cada recurso puede tener hasta tres schemas, dependiendo de quién lo crea y cómo:

- **`Create`** — datos que el usuario envía para crear el recurso (sin `id`, sin campos generados por el servidor).
- **`Update`** — campos modificables, todos opcionales.
- **`Response`** — lo que devuelve la API (incluye `id`, timestamps, etc.).

Qué schemas tiene cada recurso depende de su naturaleza:

| Schemas | Cuándo | Ejemplo |
|---|---|---|
| Solo `Response` | El servidor crea el recurso automáticamente por lógica, no hay endpoint de creación directa | `Visit`, `Strike` |
| `Create` + `Response` | El usuario lo crea pero no puede editarlo | `Report`, `QueueMessage` |
| `Create` + `Update` + `Response` | El usuario lo crea y también puede modificarlo | `Island`, `Queue`, `Friendship` |
| `Update` + `Response` | La creación va por un flujo especial (ej: OAuth), pero sí se puede editar | `User` |

---

## PostgreSQL
Base de datos relacional. Corre en Docker en el puerto `5434`.

Acceso visual: Adminer en `http://localhost:8080` (usuario: `turnip`, contraseña: `turnips`, BD: `turnip_exchanger`).

---

## Docker / Docker Compose
Docker empaqueta servicios en contenedores aislados. `docker-compose.yml` define los servicios del proyecto:
- `db`: PostgreSQL en el puerto 5434
- `adminer`: interfaz web para explorar la BD en el puerto 8080

Comandos útiles:
```bash
docker compose up -d        # arranca todos los servicios en background
docker compose down         # para y elimina los contenedores
docker compose up -d db     # arranca solo la BD
```

---

## JWT (JSON Web Tokens)
Sistema de autenticación sin estado. Tras el login, el servidor genera dos tokens:
- **access_token**: de corta duración (60 min), se envía en cada request
- **refresh_token**: de larga duración (30 días), solo para obtener un nuevo access_token

**En este proyecto:** generados en `app/core/security.py`, usados en los endpoints de auth.

---

## OAuth (Discord / Google)
Permite al usuario autenticarse con su cuenta de Discord o Google sin crear una contraseña. El flujo es:
1. El usuario hace click en "Login con Discord"
2. Se redirige a Discord, el usuario acepta
3. Discord redirige de vuelta con un `code`
4. El backend intercambia ese `code` por los datos del usuario
5. Se crea o actualiza el usuario en la BD y se devuelven tokens JWT

**En este proyecto:** implementado en `app/api/v1/endpoints/auth.py`.
