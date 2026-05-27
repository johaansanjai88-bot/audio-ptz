# PTZ Camera API Documentation

Base URL: `http://localhost:5000`

---

## Cameras

### List all cameras
`GET /api/cameras`

**Response:**
```json
{
  "cameras": [
    { "id": "cam1", "name": "Front Entrance", "ip": "192.168.1.100" },
    { "id": "cam2", "name": "Rear Parking",   "ip": "192.168.1.101" }
  ]
}
```

---

## Movement

### Pan
`POST /api/cameras/{id}/pan`
```json
{ "direction": "right", "speed": 0.5, "duration": 1.0 }
```

### Tilt
`POST /api/cameras/{id}/tilt`
```json
{ "direction": "up", "speed": 0.5, "duration": 1.0 }
```

### Zoom
`POST /api/cameras/{id}/zoom`
```json
{ "level": 2.0, "speed": 0.5 }
```

### Combined Move (continuous)
`POST /api/cameras/{id}/move`
```json
{ "pan": 0.5, "tilt": 0.0, "zoom": 0.0 }
```
Values range from -1.0 to 1.0.

### Stop
`POST /api/cameras/{id}/stop`

### Go Home
`POST /api/cameras/{id}/home`

---

## Presets

### List presets
`GET /api/cameras/{id}/presets`

### Go to preset
`POST /api/cameras/{id}/preset/{token}`

### Save preset
`POST /api/cameras/{id}/preset/{token}/save`
```json
{ "name": "Front Gate" }
```

---

## Status & Stream

### Get position status
`GET /api/cameras/{id}/status`
```json
{ "pan": 0.12, "tilt": -0.05, "zoom": 0.3, "moving": false }
```

### Live MJPEG stream
`GET /api/cameras/{id}/stream`

Suitable for use as `<img src="...">` in a browser.

---

## Error Responses

All errors return:
```json
{ "error": "Description of what went wrong" }
```

HTTP codes used: `200 OK`, `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`
