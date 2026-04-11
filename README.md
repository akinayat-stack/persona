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

---

## REST API (Django REST Framework)

### 1) Setup

1. Install DRF:
   ```bash
   pip install djangorestframework
   ```
2. Add app in `INSTALLED_APPS`:
   ```python
   'rest_framework'
   ```
3. Configure defaults in `snapgram/settings.py`:
   - Authentication: Session + Basic auth
   - Permissions: `IsAuthenticated`

### 2) Serializers

The project now includes `ModelSerializer` classes for all core models:

- `ProfileSerializer`
- `PostSerializer`
- `CommentSerializer`
- `MessageSerializer`
- `FollowSerializer`

Validation included:
- Post requires at least caption or image.
- Comment/message content cannot be blank.
- Sender/receiver must be different users.
- Follower/following cannot be the same user.

### 3) CRUD with ViewSets (high-level)

Base path: `/api/viewsets/`

| Model | Endpoint |
|---|---|
| Profiles | `/api/viewsets/profiles/` |
| Posts | `/api/viewsets/posts/` |
| Comments | `/api/viewsets/comments/` |
| Messages | `/api/viewsets/messages/` |
| Follows | `/api/viewsets/follows/` |

Supported methods out-of-the-box: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.

### 4) CRUD with APIView (low-level)

Base path: `/api/apiview/`

| Model | List/Create | Detail (get/put/delete) |
|---|---|---|
| Profiles | `/api/apiview/profiles/` | `/api/apiview/profiles/<id>/` |
| Posts | `/api/apiview/posts/` | `/api/apiview/posts/<id>/` |
| Comments | `/api/apiview/comments/` | `/api/apiview/comments/<id>/` |
| Messages | `/api/apiview/messages/` | `/api/apiview/messages/<id>/` |
| Follows | `/api/apiview/follows/` | `/api/apiview/follows/<id>/` |

Implemented methods:
- List endpoint: `get`, `post`
- Detail endpoint: `get`, `put`, `delete`

### 5) API testing examples

#### Postman examples

Use `http://127.0.0.1:8000` as the base URL.

1. **GET posts**
   - Method: `GET`
   - URL: `/api/viewsets/posts/`

2. **POST post**
   - Method: `POST`
   - URL: `/api/viewsets/posts/`
   - Body (JSON):
     ```json
     {
       "author_id": 1,
       "caption": "My first API post"
     }
     ```

3. **PUT post**
   - Method: `PUT`
   - URL: `/api/viewsets/posts/1/`
   - Body (JSON):
     ```json
     {
       "author_id": 1,
       "caption": "Updated caption"
     }
     ```

4. **DELETE post**
   - Method: `DELETE`
   - URL: `/api/viewsets/posts/1/`

The same request patterns also work for APIView endpoints under `/api/apiview/...`.

#### JavaScript `fetch` example

```html
<div id="posts"></div>

<script>
  async function loadPosts() {
    const response = await fetch('/api/viewsets/posts/', {
      credentials: 'include'
    });

    if (!response.ok) {
      document.getElementById('posts').innerHTML = '<p>Failed to load posts.</p>';
      return;
    }

    const posts = await response.json();

    const html = `
      <table border="1" cellpadding="8">
        <thead>
          <tr><th>ID</th><th>Author</th><th>Caption</th><th>Created</th></tr>
        </thead>
        <tbody>
          ${posts.map(post => `
            <tr>
              <td>${post.id}</td>
              <td>${post.author?.username ?? 'N/A'}</td>
              <td>${post.caption}</td>
              <td>${post.created_at}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    document.getElementById('posts').innerHTML = html;
  }

  loadPosts();
</script>
```

