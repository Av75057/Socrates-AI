# LLM Streaming SSE

## Endpoint

`POST /chat/message/stream`

Request body matches the existing `POST /chat` payload:

```json
{
  "session_id": "session-key",
  "message": "Объясни второй закон Ньютона",
  "action": "none",
  "conversation_id": 123,
  "client_message_id": "uuid",
  "assignment_id": 42
}
```

Response is an SSE stream with three event types:

- `meta`: early metadata such as `conversation_id` and `session_key`
- `chunk`: the next text chunk from the tutor
- `done`: the final full `ChatResponse` payload, identical in shape to `POST /chat`

## Notes

- The legacy `POST /chat` endpoint remains available for compatibility and queue replay.
- Full tutor replies are persisted only after a successful streamed completion.
- Cancelling the request from the frontend aborts the in-flight generation and starts the next one.

## Manual Test

Start the backend and run:

```bash
curl -N -H 'Content-Type: application/json' \
  -X POST http://127.0.0.1:8000/chat/message/stream \
  -d '{"session_id":"stream-test","message":"Привет","action":"none"}'
```

You should see `meta`, then multiple `chunk` events, then a final `done` event with the full JSON payload.
