from django.core.management.base import BaseCommand

from library.models import Book, Category

SAMPLE = [
    ("Fluent Python", "Luciano Ramalho", "9781492056355", "Programming", 3),
    ("Python Crash Course", "Eric Matthes", "9781593279288", "Programming", 2),
    ("Two Scoops of Django", "Daniel Feldroy", "9780692915721", "Programming", 2),
    ("Clean Code", "Robert C. Martin", "9780132350884", "Programming", 2),
    ("Wings of Fire", "A. P. J. Abdul Kalam", "9788173711466", "Biography", 4),
    ("The Guide", "R. K. Narayan", "9780143039648", "Fiction", 2),
    ("Sapiens", "Yuval Noah Harari", "9780062316097", "History", 3),
]


class Command(BaseCommand):
    help = "Load sample categories and books"

    def handle(self, *args, **options):
        for title, author, isbn, cat, copies in SAMPLE:
            category, _ = Category.objects.get_or_create(name=cat)
            Book.objects.get_or_create(
                isbn=isbn,
                defaults={"title": title, "author": author, "category": category, "total_copies": copies},
            )
        self.stdout.write(self.style.SUCCESS("Sample books loaded."))
