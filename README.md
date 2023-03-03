# audiosync

Keep converted audio in sync with source material

## Quick Start

```bash
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Build Docker image

```bash
docker build . -t audiosync:$(date +"%Y-%m-%dT%H-%M-%S%z")
```
