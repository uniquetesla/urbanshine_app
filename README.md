# UrbanShine (urbanshine_app)

Grundgerüst einer internen Firmenplattform auf Basis von **Django**, **PostgreSQL**, **Gunicorn** und **Docker Compose**.

## Projektstruktur

```text
urbanshine_app/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── manage.py
├── urbanshine/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/
│   ├── accounts/
│   ├── customers/
│   ├── orders/
│   ├── catalog/
│   ├── employees/
│   ├── scheduling/
│   ├── invoices/
│   ├── offers/
│   ├── checkout/
│   ├── documents/
│   ├── damage/
│   ├── time_tracking/
│   ├── portal/
│   └── company/
├── templates/
├── static/
└── media/
```

## Voraussetzungen

- Docker
- Docker Compose Plugin (`docker compose`)

## Schnellstart (Development)

1. Umgebungsdatei anlegen:
   ```bash
   cp .env.example .env
   ```
2. Container starten:
   ```bash
   docker compose up --build
   ```
3. Applikation öffnen:
   - App: http://localhost:8090/
   - Healthcheck: http://localhost:8090/health/
   - Django Admin: http://localhost:8090/admin/

Beim Start führt der Web-Container automatisch aus:
- `python manage.py migrate`
- `python manage.py collectstatic --noinput`
- Start von Gunicorn

### Standard-Adminlogin (automatisch via Migration)
- Benutzername: `admin`
- Passwort: `admin1234`

## Nützliche Befehle

### Superuser anlegen
```bash
docker compose run --rm web python manage.py createsuperuser
```

### Migrationen erstellen
```bash
docker compose run --rm web python manage.py makemigrations
```

### Migrationen anwenden
```bash
docker compose run --rm web python manage.py migrate
```

## Konfiguration

Alle relevanten Einstellungen kommen aus `.env`:

- `DJANGO_ENV=development|production`
- `DJANGO_DEBUG=True|False`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_*`
- `TIME_ZONE`

### Development vs. Production

- **Development**: `DJANGO_ENV=development`, `DJANGO_DEBUG=True`
- **Production**: `DJANGO_ENV=production`, `DJANGO_DEBUG=False`, eigener sicherer `DJANGO_SECRET_KEY`

Zusätzlich aktiviert `production` sichere Cookie- und Header-Einstellungen in Django.

## Static & Media

- **Static Files**: WhiteNoise (`whitenoise.middleware.WhiteNoiseMiddleware`) + `collectstatic` nach `/app/staticfiles`
- **Media Uploads**: unter `/app/media`
- Beide Pfade sind als Docker Volumes in `docker-compose.yml` hinterlegt.

## Deployment-Hinweise (Raspberry Pi / Ubuntu Server)

- Dieses Setup ist für containerisierten Betrieb via Docker Compose geeignet.
- Auf Raspberry Pi muss ein passendes OS / Docker Setup mit ARM-Unterstützung vorhanden sein.
- Für Produktionsbetrieb:
  - `.env` mit sicheren Werten bereitstellen
  - Reverse Proxy (z. B. Nginx/Caddy) vor den `web`-Container setzen
  - Backups für `postgres_data` einrichten
