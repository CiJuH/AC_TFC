# ACExchanger — Contexto del proyecto

## Qué es
App Android para jugadores de **Animal Crossing: New Horizons**. Permite visitar
islas de otros jugadores o recibir visitas. Los hosts abren su isla con un código
Dodo y gestionan una cola de visitantes. Usos: vender nabos, intercambiar objetos,
visitar islas con catálogos especiales.

## Stack
- **Android**: Jetpack Compose (Kotlin) — maqueta completa
- **Backend**: FastAPI + SQLAlchemy async + PostgreSQL
- **Migraciones**: Alembic (migración inicial: `589de32e1e4c`)
- **Auth**: Discord OAuth, Google OAuth, email/password + JWT (stateless)

## Repos
- Android: `ACExchanger_Android`
- Backend: `TFC` (rama `main`)

---

## Estructura backend

```
app/
├── api/v1/
│   ├── endpoints/        # auth, chats, friendships, islands, queue_messages,
│   │                     # queue_users, queues, reports, reviews, users, visits
│   ├── dependencies.py   # get_current_user, require_admin, require_mod
│   ├── helpers.py
│   └── router.py
├── core/
│   ├── config.py         # settings (env vars)
│   └── security.py       # create_access_token, create_refresh_token, decode_token
├── db/
│   └── session.py        # get_db, AsyncSession
├── models/               # SQLAlchemy — ver tabla abajo
├── schemas/              # Pydantic — un archivo por entidad + auth.py
└── services/
```

## Schemas existentes
`app/schemas/`: auth, ban, chat, friendship, island, private_message,
queue_message, queue_user, queue, report, review, strike, user, visit

### app/schemas/auth.py
```python
class RegisterRequest(BaseModel): username, password
class LoginRequest(BaseModel):    username, password
class RefreshRequest(BaseModel):  refresh_token
class LogoutRequest(BaseModel):   refresh_token
```

---

## Endpoints implementados

| Grupo | Endpoints |
|-------|-----------|
| `auth` | register, login, refresh, logout, discord/login, discord/callback, google/login, google/callback |
| `users` | GET/PATCH/DELETE /me, GET /{id}, GET /{id}/stats |
| `islands` | GET / (con filtros), CRUD isla propia, GET /{id}, GET /{id}/active-queue |
| `queues` | GET /explore, GET /turnip-prices, GET /my, crear, GET/PATCH /{id}, cerrar, GET /{id}/my-position |
| `queue_users` | join, leave, rejoin, list participants, update status |
| `visits` | GET /me (as_host flag), start (host), end (host o visitor), GET /{id} |
| `reviews` | crear, GET /{id}, GET /visit/{id}, GET /user/{id} |
| `queue_messages` | list, send, pin, delete |
| `chats` | list, get_or_create, messages (list/send/mark_read) |
| `friendships` | list, send request, update status, delete |
| `reports` | create, list (mod), resolve (mod) |
| `admin` | bans (create/lift/get), strikes (create/list), users (search, history) |

---

## Modelo de datos

| Tabla | Campos clave |
|-------|-------------|
| **User** | id (uuid), oauth_provider, username, avatar_url, rating, role (admin/mod/visitor), is_active, is_deleted |
| **Island** | id, user_id FK, island_name, host_name, hemisphere, fruit, description, deleted_at |
| **Queue** | id, island_id FK, category (turnips/objects), turnip_price, dodo_code, status (active/paused/closed), limit, requires_fee, visit_ends_at, closed_at |
| **QueueUser** | id, queue_id FK, user_id FK, status (waiting/visiting/skipped/done/left/kicked) |
| **Visit** | id, queue_id FK, island_id FK, user_id FK, entered_at, left_at |
| **Review** | id, visit_id FK (unique), reviewer_id FK, reviewed_id FK, rating (1-5) |
| **Ban** | id, user_id FK (unique), reason, is_active, expires_at (None = permanente) |
| **Strike** | id, user_id FK, reason (no_confirmation/kicked_by_host) |
| **Friendship** | id, user_id FK, friend_id FK, status (pending/accepted/blocked) |
| **Chat** | id, user_a_id FK, user_b_id FK, last_message_at |
| **PrivateMessage** | id, chat_id FK, sender_id FK, content, is_read, is_deleted |
| **QueueMessage** | id, queue_id FK, sender_id FK, content, is_pinned, is_deleted |

### Decisiones de diseño
- `is_host` no se almacena — se calcula en el servicio
- `dodo_code` en Queue, no en Island (los códigos son temporales)
- Posición en cola: no se almacena, se calcula (`skipped` primero, luego `waiting` por `created_at`)
- `skipped`: 1er skip = segunda oportunidad; 2º skip = `kicked` + Strike
- `expires_at = None` en Ban → ban permanente
- `deleted_at = None` en Island → isla activa
- Reviews son sobre el usuario (host), no sobre la isla
- 3 strikes en 7 días = ban automático de 24h

### Mixins (`mixins.py`)
- `UUIDMixin` — `id` UUID primary key
- `CreatedAtMixin` — solo `created_at`
- `TimestampMixin` — `created_at` + `updated_at`

---

## Auth — JWT stateless

- Access token + refresh token, sin tabla en BD
- `decode_token` en `app/core/security.py`
- `get_current_user` en `app/api/v1/dependencies.py` — usa `HTTPBearer`
- Logout: stateless, el servidor valida y devuelve 204, el cliente descarta tokens
- OAuth (Discord/Google): logout solo en cliente

---

## Android — Pantallas implementadas

- **Login/Register** — OAuth + contraseña, sesión en DataStore
- **Home** — saludo por hora, card cola activa, card isla, FAB crear isla
- **Islas** — grid 2 columnas, filtro categoría, ordenación
- **Detalle de isla** — cola con fondo `secondaryContainer`, visitantes, FAB chat
- **Host** — gestión isla: abrir/cerrar, Dodo editable, kick
- **Crear isla** — nombre, host name, hemisferio, fruta, categoría, precio nabos (max 660 bayas), Dodo
- **Mensajes** — lista con buscador, colas pinneadas con color distinto
- **Chat** — burbujas, reply tap largo, menciones @ con autocompletado
- **Visitas** — tabs mis visitas / recibidas, review con estrellas
- **Perfil** — isla única, edición inline, avatar iniciales
- **Ajustes** — sonido, notificaciones Android 13+, cerrar sesión
- **Ayuda** — secciones colapsables: guías, FAQ, glosario

### Pendiente Android
- Pantalla perfil ajeno (reportar, añadir amigo)
- Sistema de amigos completo
- ViewModels y conexión con API
- Notificaciones push con FCM
- Subida de avatar (Coil)

### Navegación
```
login → login_password → register → profile_setup → home
home → host | create_island | queues → island_detail/{id} → chat
home → visits | chat/{id} | profile | help | settings
```

### Estructura Android
```
com.tfc.acexchanger/
├── MainActivity.kt
└── ui/
    ├── auth/          LoginScreen, PasswordLoginScreen, RegisterScreen
    ├── feedback/      ClickFeedback, ClickFeedbackModifier
    ├── help/          HelpScreen
    ├── home/          HomeScreen, HomeModels (DEBUG flags)
    ├── host/          HostScreen, CreateIslandScreen
    ├── islands/       IslandsScreen, IslandDetailScreen, IslandsModels
    ├── messages/      MessagesScreen, ChatScreen, MessagesModels
    ├── profile/       ProfileScreen, ProfileModels (NativeFruit, Hemisphere)
    ├── settings/      SettingsScreen, SettingsRepository (DataStore)
    └── visits/        VisitsScreen, VisitsModels
```

---

## Convenciones

### Backend
- Commits: Conventional Commits en inglés
- Código y comentarios: inglés
- SQLAlchemy async con `AsyncSession`
- Columnas: `Mapped[tipo]` con `mapped_column(...)`
- `__repr__` en todos los modelos

### Android
- Texto visible: **español**; código: **inglés**
- "bells" → siempre **"bayas"**
- `NativeFruit` y `Hemisphere` en `ui/profile/ProfileModels.kt`
- Sonidos: `res/raw/boop_small.ogg`, `res/raw/boop_medium.ogg`
- Usar `clickableWithFeedback` para elementos clickables
- `@OptIn(ExperimentalMaterial3Api::class)` para `TooltipBox`
- `DEBUG_HAS_ISLAND` y `DEBUG_IS_IN_ISLAND` en `HomeModels.kt`
