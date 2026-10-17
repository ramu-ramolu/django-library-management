from django.urls import path

from . import views

urlpatterns = [
    path("", views.BookListView.as_view(), name="book_list"),
    path("books/add/", views.BookCreateView.as_view(), name="book_add"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("books/<int:pk>/edit/", views.BookUpdateView.as_view(), name="book_edit"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book_delete"),
    path("books/<int:pk>/borrow/", views.borrow_book, name="borrow_book"),
    path("borrowings/<int:pk>/return/", views.return_book, name="return_book"),
    path("my-books/", views.MyBorrowingsView.as_view(), name="my_borrowings"),
    path("manage/borrowings/", views.AllBorrowingsView.as_view(), name="all_borrowings"),
    path("register/", views.register, name="register"),
]
