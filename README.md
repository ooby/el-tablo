# Выведение талонов из РМИС на табло очереди

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Как работает?

Для работы нужен `python` и пакет `pyserial`

Необходимо приготовить файл `settings.json`

```json
{
  "frequency": 3000,
  "restContext": "/equeue",
  "restQuery": "/tickets",
  "restHost": "https://dev.is-mis.ru",
  "boards": [
    {
      "id": 1,
      "resources": [1],
      "serial": "/dev/ttyUSB0",
      "blnconf": 14,
      "blcount": 4,
      "blspeed": 20
    },
    {
      "id": 2,
      "resources": [2, 4],
      "serial": "/dev/ttyUSB1",
      "blnconf": 14,
      "blcount": 4,
      "blspeed": 20
    }
  ]
}
```

Далее:

```bash
python main.py settings.json
```