# Library Management System (Django)

A full-featured library app: book catalogue with search, member accounts,
borrow/return workflow, due dates, automatic fines, and a staff dashboard.

## Features
- Register / login / logout (Django auth)
- Browse, search (title/author/ISBN), filter by category, pagination
- Members: borrow books (max 3 at a time, 14-day loan), return books, see fines
- Staff: add / edit / delete books, view all borrowings, filter overdue, mark returned
- Fine: Rs. 5 per overdue day (change in `library/models.py`)
- Available copies computed from active borrowings (no counter-sync bugs)
- Django admin configured for all models

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations library
python manage.py migrate
python manage.py createsuperuser   # staff account
python manage.py seed_books        # optional sample data
python manage.py runserver
```
Open http://127.0.0.1:8000/ (admin at /admin/).

## Structure
```
library_project/   settings, root urls
library/
  models.py        Category, Book, Borrowing (+ fine logic)
  views.py         list/detail/CRUD, borrow, return, register
  forms.py         BookForm (ISBN + copies validation), RegisterForm
  templates/       base, books, borrowings, auth pages
  management/commands/seed_books.py
```

## Ideas to extend (good for your portfolio)
- Django REST Framework API + token auth
- Book cover image upload (Pillow + MEDIA_ROOT)
- Email reminders for due dates (Celery / management command + cron)
- Reservations queue, PostgreSQL, Docker, deployment on Render/Railway
- Unit tests for borrow limits and fine calculation
