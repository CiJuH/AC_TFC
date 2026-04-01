# Tests manuales

Lista de casos a probar en `/docs` (Swagger). Para cada caso se indica el resultado esperado.

---

## Auth

| Test | Resultado esperado |
|---|---|
| Registrar usuario nuevo | 201 con access_token y refresh_token |
| Registrar con username ya existente | 409 |
| Login correcto | 200 con tokens |
| Login con contraseña incorrecta | 401 |
| Login con usuario inexistente | 401 |
| Refresh con refresh_token válido | 200 con nuevo access_token |
| Refresh con access_token (tipo incorrecto) | 401 |
| Refresh con token inválido/expirado | 401 |
| Endpoint protegido sin token | 401 |
| Endpoint protegido con token expirado | 401 |

---

## Users

| Test | Resultado esperado |
|---|---|
| GET /users/me con token válido | 200 con datos del usuario |
| PATCH /users/me cambiando username | 200 con datos actualizados |
| DELETE /users/me | 204 → luego GET /users/me devuelve 401 |
| GET /users/{id} existente | 200 con datos públicos |
| GET /users/{id} de usuario eliminado | 404 |
| GET /users/{id} inexistente | 404 |

---

## Islands

| Test | Resultado esperado |
|---|---|
| Crear isla | 201 |
| Crear segunda isla (misma cuenta) | 409 |
| GET /islands/me con isla | 200 |
| GET /islands/me sin isla | 404 |
| PATCH /islands/me actualizando descripción | 200 |
| DELETE /islands/me | 204 → GET /islands/me devuelve 404 |
| DELETE /islands/me con cola abierta | 204 → cola queda con status=closed |
| GET /islands/{id} existente | 200 |
| GET /islands/{id} eliminada | 404 |

---

## Queues

| Test | Resultado esperado |
|---|---|
| Crear cola con dodo_code de 5 chars | 201 |
| Crear cola con dodo_code de 4 o 6 chars | 422 |
| Crear cola con limit=0 | 422 |
| Crear cola con limit=101 | 422 |
| Crear cola sin isla previa | 404 |
| Crear segunda cola con cola ya abierta | 409 |
| GET /queues/my | lista de colas de tu isla |
| GET /queues/{id} | 200 |
| PATCH /queues/{id} como host | 200 |
| PATCH /queues/{id} como no-host | 403 |
| POST /queues/{id}/close | 200, status=closed, closed_at != null |
| POST /queues/{id}/close ya cerrada | 409 |

---

## Queue Users

| Test | Resultado esperado |
|---|---|
| Unirse a cola activa | 201, status=waiting |
| Unirse a cola pausada o cerrada | 409 |
| Unirse a cola llena | 409 |
| Unirse dos veces a la misma cola | 409 |
| GET /queues/{id}/participants | lista ordenada por created_at |
| Leave cola en la que estás | 204, status=left |
| Leave cola en la que no estás | 404 |
| PATCH status participante como host | 200 |
| PATCH status participante como no-host | 403 |

---

## Visits

| Test | Resultado esperado |
|---|---|
| POST /visits (host) con visitante en cola | 201, QueueUser pasa a visiting |
| POST /visits como no-host | 403 |
| POST /visits con user no en cola | 404 |
| POST /visits/{id}/end como visitante | 200, left_at != null, QueueUser pasa a done |
| POST /visits/{id}/end como host | 200 |
| POST /visits/{id}/end como tercero | 403 |
| POST /visits/{id}/end ya terminada | 409 |

---

## Reviews

| Test | Resultado esperado |
|---|---|
| POST /reviews tras visita completada | 201 |
| POST /reviews con visita no terminada | 409 |
| POST /reviews como host (no visitante) | 403 |
| POST /reviews duplicada para la misma visita | 409 |
| POST /reviews con rating=0 | 422 |
| POST /reviews con rating=6 | 422 |
| GET /reviews/visit/{id} con review | 200 |
| GET /reviews/visit/{id} sin review | 404 |

---

## Queue Messages

| Test | Resultado esperado |
|---|---|
| Enviar mensaje como host | 201 |
| Enviar mensaje como participante activo (waiting/visiting/skipped) | 201 |
| Enviar mensaje como no-participante | 403 |
| GET /queues/{id}/messages | solo mensajes no eliminados, ordenados por fecha |
| Pin mensaje como host | 200, is_pinned cambia |
| Pin mensaje como no-host | 403 |
| DELETE mensaje propio | 204 |
| DELETE mensaje ajeno como host | 204 |
| DELETE mensaje ajeno como usuario normal | 403 |

---

## Chats

| Test | Resultado esperado |
|---|---|
| POST /chats con otro usuario | 201 |
| POST /chats mismos usuarios dos veces | devuelve el mismo chat (no crea duplicado) |
| POST /chats contigo mismo | 400 |
| POST /chats con usuario inexistente | 404 |
| GET /chats | lista solo tus chats |
| GET /chats/{id}/messages como participante | 200 |
| GET /chats/{id}/messages como tercero | 403 |
| POST mensaje en chat tuyo | 201, last_message_at actualizado |
| PATCH message/{id}/read como receptor | 200, is_read=true |
| PATCH message/{id}/read como emisor | 400 |

---

## Friendships

| Test | Resultado esperado |
|---|---|
| Enviar solicitud de amistad | 201, status=pending |
| Enviar solicitud a ti mismo | 400 |
| Enviar solicitud a usuario inexistente | 404 |
| Enviar solicitud duplicada | 409 |
| Aceptar solicitud como receptor | 200, status=accepted |
| Aceptar solicitud como emisor | 403 |
| Bloquear como cualquiera de los dos | 200, status=blocked |
| DELETE friendship | 204 |
| DELETE friendship ajena | 403 |

---

## Reports

| Test | Resultado esperado |
|---|---|
| Reportar a otro usuario | 201 |
| Reportarte a ti mismo | 400 |
| Reportar usuario inexistente | 404 |
| GET /reports como usuario normal | 403 |
| GET /reports como mod | 200 |
| PATCH /reports/{id}/resolve como mod | 200, is_resolved=true |
| PATCH /reports/{id}/resolve ya resuelto | 409 |

---

## Admin

| Test | Resultado esperado |
|---|---|
| POST /admin/bans como mod | 201, usuario desactivado |
| POST /admin/bans usuario ya baneado | 409 |
| POST /admin/bans como usuario normal | 403 |
| PATCH /admin/bans/{id}/lift | 200, usuario reactivado |
| PATCH /admin/bans/{id}/lift ban ya inactivo | 409 |
| GET /admin/users/{id}/ban sin ban | 404 |
| POST /admin/strikes como mod | 201 |
| GET /admin/users/{id}/strikes | lista de strikes |