# ACExchanger — Contexto del proyecto

## Qué es
ACExchanger es una app Android para jugadores de Animal Crossing: New Horizons (TFC).
Permite visitar islas de otros jugadores o recibir visitas. Los hosts abren su isla con
un código Dodo y gestionan una cola de visitantes. Usos principales: vender nabos,
intercambiar objetos, visitar islas con catálogos especiales.

## Stack
- **Android**: Jetpack Compose (Kotlin) — maqueta completa
- **Backend**: FastAPI + SQLAlchemy async + PostgreSQL — en construcción
- **Migraciones**: Alembic
- **Auth**: Discord OAuth, Google OAuth, email/password + JWT

## Repos
- Android: `ACExchanger_Android` (maqueta completa)
- Backend: `TFC` (en construcción, rama `main`)

## Estado actual del backend
- Modelos SQLAlchemy: ✅ finalizados
- Schemas Pydantic: ✅ finalizados (`app/schemas/`)
- Migraciones Alembic: ✅ migración inicial limpia (`589de32e1e4c`)
- Endpoints implementados: ✅ todos
  - `auth`: register, login, refresh, logout, Discord OAuth, Google OAuth
  - `users`: GET/PATCH/DELETE /me, GET /{id}, GET /{id}/stats
  - `islands`: CRUD isla propia, GET /islands (con filtros), GET /{id}, GET /{id}/active-queue
  - `queues`: crear, GET /my, GET /explore, GET /turnip-prices, GET/PATCH /{id}, cerrar, GET /{id}/my-position
  - `queue_users`: join, leave, rejoin, list participants, update status
  - `visits`: GET /me (as_host flag), start (host), end (host o visitor), GET /{id}
  - `reviews`: crear, GET /{id}, GET /visit/{id}, GET /user/{id}
  - `queue_messages`: list, send, pin, delete
  - `chats`: list, get_or_create, messages (list/send/mark_read)
  - `friendships`: list, send request, update status, delete
  - `reports`: create, list (mod), resolve (mod)
  - `admin`: bans (create/lift/get), strikes (create/list), users (search, history)
- Todo lo implementado en esta fase: concurrent_visitors, exclusion mutua, dodo_code condicional, _advance_queue, close_queue limpia participantes, conteos incluyen skipped
- Migracion a1b2c3d4e5f6: concurrent_visitors INTEGER NOT NULL DEFAULT 4
- `PATCH /users/me` comprueba unicidad de username (409 si ya existe)
- `QueueDetailResponse` incluye `host_user_id` para poder reportar al anfitrión desde la pantalla de detalle
- `PATCH /queues/{id}/participants/{user_id}` acepta `apply_strike: bool = False`; si True y new_status=kicked, añade Strike(kicked_by_host) y ejecuta auto-ban
- Siguiente paso: VisitsViewModel + ReviewsViewModel (Android), auto-cierre colas 12h (APScheduler), Discord/Google OAuth

## Modelo de datos (dbml)
```
Table User {
  id uuid
  oauth_provider (discord/google/email, nullable)
  oauth_id (nullable)
  password_hash (nullable, solo si email)
  username str
  avatar_url str (nullable)
  rating float
  is_active bool
  is_deleted bool
  deleted_at datetime (nullable)
  role (admin/mod/visitor)
  created_at, updated_at
}

Table Island {
  id uuid
  user_id uuid FK
  island_name str
  host_name str
  hemisphere (north/south)
  fruit (apple/pear/cherry/peach/orange)
  description text (nullable)
  deleted_at datetime (nullable)
  created_at, updated_at
}

Table Chat {
  id uuid
  user_a_id uuid FK
  user_b_id uuid FK
  last_message_at datetime (nullable)
  created_at datetime
  UniqueConstraint(user_a_id, user_b_id)
}

Table Queue {
  id uuid
  island_id uuid FK
  -- Event info
  category (turnips/objects)
  turnip_price int (nullable, solo si category = turnips)
  description text (nullable)
  dodo_code str (5 chars)
  -- Queue settings
  status (active/paused/closed)
  limit int (default 10)
  concurrent_visitors int (default 4, max 7 — límite real de ACNH)
  requires_fee bool
  fee_description str (nullable)
  -- Timestamps
  visit_ends_at datetime (nullable, hora estimada de cierre)
  created_at datetime
  closed_at datetime (nullable, None = abierta)
}

Table QueueUser {
  id uuid
  queue_id uuid FK
  user_id uuid FK
  status (waiting/visiting/skipped/done/left/kicked)
  created_at, updated_at
  -- posición calculada por created_at, no almacenada
  -- índice en status para consultas eficientes
  UniqueConstraint(queue_id, user_id)
}

Table Visit {
  id uuid
  queue_id uuid FK
  island_id uuid FK
  user_id uuid FK
  entered_at datetime (nullable)
  left_at datetime (nullable, None = sigue en isla)
  created_at datetime
}

Table Review {
  id uuid
  visit_id uuid FK (unique)
  reviewer_id uuid FK
  reviewed_id uuid FK
  rating int (1-5, CheckConstraint)
  comment text (nullable)
  created_at, updated_at
}

Table Ban {
  id uuid
  user_id uuid FK (unique)
  banned_by_id uuid FK (nullable)
  reason text
  ban_from datetime
  is_active bool
  expires_at datetime (nullable, None = permanente)
  created_at, updated_at
}

Table Strike {
  id uuid
  user_id uuid FK
  reason (no_confirmation/kicked_by_host)
  created_at datetime
  -- 3 strikes en 7 días = ban automático de 24h
  -- strike por no_confirmation se aplica al 2º skip en la misma cola (el 1º es segunda oportunidad)
}

Table Friendship {
  id uuid
  user_id uuid FK
  friend_id uuid FK
  status (pending/accepted/blocked)
  created_at, updated_at
  UniqueConstraint(user_id, friend_id)
}

Table PrivateMessage {
  id uuid
  chat_id uuid FK
  sender_id uuid FK
  content text
  is_read bool
  is_deleted bool
  created_at datetime
}

Table QueueMessage {
  id uuid
  queue_id uuid FK
  sender_id uuid FK
  content text
  is_pinned bool
  is_deleted bool
  deleted_by uuid FK (nullable)
  created_at datetime
}
```

## Relaciones
- User 1--* Island
- User 1--1 Ban
- User 1--* Strike
- User 1--* Friendship (como user_id y como friend_id)
- User 1--* Chat (como user_a o user_b, viewonly)
- User 1--* PrivateMessage (como sender)
- Island 1--* Queue
- Queue 1--* QueueUser
- Queue 1--* QueueMessage
- Queue 1--* Visit
- User 1--* Visit
- Visit 1--1 Review

## Decisiones de diseño relevantes
- `is_host` no se almacena ni se deriva en User — se calcula en el servicio con una query eficiente
- `dodo_code` vive como columna en Queue, en claro — los códigos son temporales y no tienen valor fuera de contexto
- `turnip_price`, `category` y `description` viven en Queue, no en Island — cada cola es un evento con su propio contexto; Island solo guarda la info permanente de la isla
- `position` en QueueUser no se almacena — orden de cola: `skipped` primero, luego `waiting` por `created_at`
- `skipped` es un estado temporal (primera vez que se salta a alguien) — si vuelve a ser saltado, pasa a `kicked` + Strike
- `kicked` es terminal (expulsado tras 2º skip); `left` es salida voluntaria
- `expires_at = None` en Ban implica ban permanente — no hay campo `is_permanent`
- `deleted_at = None` en Island implica isla activa — no hay campo `is_active`
- Las reviews son sobre el usuario (host), no sobre la isla — la visita es el "ticket" que habilita la review
- Chat existe como entidad propia para guardar `last_message_at` y ordenar conversaciones eficientemente
- En FastAPI, rutas estáticas (`/explore`, `/me`) deben declararse antes de rutas dinámicas (`/{id}`) si tienen la misma profundidad de path
- `concurrent_visitors` en Queue es distinto de `limit`: `limit` = tamaño máximo de la cola de espera; `concurrent_visitors` = cuántos pueden estar dentro de la isla a la vez (1–7, límite real de ACNH es 7)
- Exclusión mutua host↔visitante: un usuario no puede unirse a una cola si tiene una cola activa como host, y viceversa. Se aplica en backend (`join_queue`) y se muestra aviso en frontend
- El `dodo_code` solo se devuelve a usuarios cuyo `QueueUser.status == "visiting"` en esa cola — el resto no tiene permiso para entrar todavía
- Tiempo dentro de la isla: se calcula en frontend como `now - QueueUser.updated_at` cuando `status = visiting` (updated_at cambia al transicionar a ese estado); no se almacena como campo separado

## Mixins disponibles (mixins.py)
- `UUIDMixin` — añade `id` (UUID primary key)
- `CreatedAtMixin` — añade solo `created_at`
- `TimestampMixin` — añade `created_at` + `updated_at`

## Convenciones de código
- Modelos con UUIDMixin + el mixin de timestamps apropiado según el modelo
- Columnas: `Mapped[tipo]` con `mapped_column(...)`
- Relationships tipados: `Mapped["Modelo"]` o `Mapped["Modelo | None"]`
- `__repr__` en todos los modelos
- SQLAlchemy async con AsyncSession
- Commits en inglés con Conventional Commits (feat/fix/refactor/chore/docs)
- Comentarios en el código en inglés

## Estado actual de la app Android
- `ui/common/ReportDialog.kt` — diálogo reutilizable de reporte (5 razones: scam, no_show, rude_behavior, cheating, other)
- `IslandDetailScreen`: botón Flag en header para reportar al anfitrión; botón "Ya me voy" llama a `endVisit` (no `leaveQueue`) cuando el usuario está visitando
- `HostScreen`: VisitorWithMenu muestra tiempo en isla + opción "Reportar usuario"; HostQueueRow tiene botón Flag para reportar; diálogo de expulsión pregunta si aplicar strike
- `HomeViewModel` / `HomeAlert`: sealed class que distingue alertas urgentes (dialog) de informativas (snackbar); emite notificaciones del sistema via `NotificationHelper`
- `ProfileScreen`: error de username duplicado se muestra inline en el campo (rojo), no como snackbar
- Tiempo en isla del visitante: se calcula en ambas pantallas (IslandDetailScreen y HostScreen) con `now - QueueUser.updated_at`

## Convenciones de la app Android
- Todo el texto visible en español, código en inglés
- "bells" → siempre "bayas"
- NativeFruit y Hemisphere están en ui/profile/ProfileModels.kt
- clickableWithFeedback para elementos clickables
- DEBUG_HAS_ISLAND y DEBUG_IS_IN_ISLAND en HomeModels.kt para simular estados
- Notificaciones del sistema via `NotificationHelper` (objeto singleton en `ui/notifications/`); canal `acexchanger_queue`; requiere permiso POST_NOTIFICATIONS en Android 13+
