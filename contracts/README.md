# Contratos MoveCodeBeats

Os contratos publicos usam versionamento explicito para que backend e frontend
possam evoluir sem depender da estrutura interna das classes Python.

## REST v1

- `GET /api/v1/health`
- `GET /api/v1/catalog`
- `GET /api/v1/profiles`
- `GET /api/v1/profiles/{profile_id}`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `PATCH /api/v1/sessions/{session_id}/profile`

## WebSocket v1

Conexao:

`/api/v1/sessions/{session_id}/stream`

Envelope do servidor:

```json
{
  "schema_version": "1.0",
  "type": "music.state.v1",
  "timestamp": 1770000000.0,
  "session_id": "uuid",
  "data": {}
}
```

Eventos enviados pelo servidor:

- `session.status.v1`
- `runtime.status.v1`
- `music.state.v1`
- `preview.frame.v1`
- `profile.selected.v1`
- `error.v1`

Evento aceito do cliente:

```json
{
  "schema_version": "1.0",
  "type": "profile.select.v1",
  "data": {
    "profile_id": "happy"
  }
}
```

Novos campos opcionais podem ser adicionados dentro de `data` sem alterar a
versao principal. Mudancas incompatíveis exigem um novo tipo de evento ou uma
nova versao da API.
