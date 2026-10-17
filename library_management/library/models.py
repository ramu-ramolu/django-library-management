from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

LOAN_DAYS = 14                    # how long a book can be kept
FINE_PER_DAY = Decimal("5.00")    # fine per overdue day (Rs.)
MAX_ACTIVE_LOANS = 3              # max books a member can hold at once


def default_due_date():
    return timezone.localdate() + timedelta(days=LOAN_DAYS)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    isbn = models.CharField("ISBN", max_length=13, unique=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="books"
    )
    description = models.TextField(blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def available_copies(self):
        # Uses the `issued` annotation when present (avoids N+1 in list pages)
        issued = getattr(self, "issued", None)
        if issued is None:
            issued = self.borrowings.filter(returned_on__isnull=True).count()
        return max(self.total_copies - issued, 0)

    @property
    def is_available(self):
        return self.available_copies > 0


class Borrowing(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="borrowings")
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )
    borrowed_on = models.DateField(default=timezone.localdate)
    due_on = models.DateField(default=default_due_date)
    returned_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-borrowed_on", "-id"]

    def __str__(self):
        return f"{self.book.title} -> {self.member}"

    @property
    def is_returned(self):
        return self.returned_on is not None

    @property
    def is_overdue(self):
        return not self.is_returned and timezone.localdate() > self.due_on

    @property
    def fine(self):
        end = self.returned_on or timezone.localdate()
        late_days = (end - self.due_on).days
        return FINE_PER_DAY * late_days if late_days > 0 else Decimal("0.00")
