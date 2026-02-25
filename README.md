# Persona

A social media web application built with Django (MVT architecture) and PostgreSQL.

---

## Tech Stack

- Python 3.12
- Django 4.2.9
- PostgreSQL
- Bootstrap 5

---

## Requirements

- Python 3.11 or 3.12
- PostgreSQL installed and running

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/persona.git
cd persona
```

**2. Create and activate virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create PostgreSQL database**

Open pgAdmin or psql and run:
```sql
CREATE DATABASE persona_db;
CREATE USER persona_user WITH PASSWORD 'persona_password';
GRANT ALL PRIVILEGES ON DATABASE persona_db TO persona_user;
```

**5. Run migrations**
```bash
python manage.py makemigrations core
python manage.py migrate
```

**6. Create admin account**
```bash
python manage.py createsuperuser
```

**7. Start the server**
```bash
python manage.py runserver
```

Open in browser: `http://localhost:8000`

Admin panel: `http://localhost:8000/admin`

---

## Pages

| Page | URL |
|---|---|
| Login / Register | `/` |
| Feed | `/feed/` |
| Profile | `/profile/<username>/` |
| Create Post | `/post/create/` |
| Post Detail | `/post/<id>/` |
| Messages | `/messages/` |
| Chat | `/messages/<username>/` |
| Search | `/search/` |
| Admin | `/admin/` |

---

## Features

- Register and login
- Image posts and text-only posts
- Like posts and messages
- Comments with emoji picker
- Follow / unfollow users
- Direct messaging
- User search
- Edit profile and avatar

---

## Database Models

| Model | Description |
|---|---|
| Profile | User bio and avatar |
| Post | Image or text posts |
| Comment | Comments on posts |
| Message | Direct messages |
| Follow | Follow relationships |

---

## Authors

- Your Name
- Partner Name

*University Project — Django MVT — 2025/2026*
