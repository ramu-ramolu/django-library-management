from django.contrib import admin

from .models import Book, Borrowing, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "isbn", "category", "total_copies"]
    list_filter = ["category"]
    search_fields = ["title", "author", "isbn"]


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ["book", "member", "borrowed_on", "due_on", "returned_on"]
    list_filter = ["returned_on", "due_on"]
    search_fields = ["book__title", "member__username"]
