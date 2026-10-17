from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import BookForm, RegisterForm
from .models import MAX_ACTIVE_LOANS, Book, Borrowing, Category


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


def with_issued(qs):
    return qs.annotate(
        issued=Count("borrowings", filter=Q(borrowings__returned_on__isnull=True))
    )


# ---------- Books ----------
class BookListView(ListView):
    model = Book
    template_name = "library/book_list.html"
    context_object_name = "books"
    paginate_by = 9

    def get_queryset(self):
        qs = with_issued(Book.objects.select_related("category"))
        q = self.request.GET.get("q", "").strip()
        cat = self.request.GET.get("category", "")
        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q)
            )
        if cat.isdigit():
            qs = qs.filter(category_id=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_category"] = self.request.GET.get("category", "")
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        return ctx


class BookDetailView(DetailView):
    model = Book
    template_name = "library/book_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["already_borrowed"] = (
            user.is_authenticated
            and Borrowing.objects.filter(
                book=self.object, member=user, returned_on__isnull=True
            ).exists()
        )
        return ctx


class BookCreateView(StaffRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "library/book_form.html"
    success_url = reverse_lazy("book_list")

    def form_valid(self, form):
        messages.success(self.request, "Book added.")
        return super().form_valid(form)


class BookUpdateView(StaffRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "library/book_form.html"
    success_url = reverse_lazy("book_list")

    def form_valid(self, form):
        messages.success(self.request, "Book updated.")
        return super().form_valid(form)


class BookDeleteView(StaffRequiredMixin, DeleteView):
    model = Book
    template_name = "library/book_confirm_delete.html"
    success_url = reverse_lazy("book_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Cannot delete: this book has borrowing history.")
            return redirect("book_detail", pk=self.object.pk)
        messages.success(self.request, "Book deleted.")
        return response


# ---------- Borrowing ----------
@login_required
@require_POST
def borrow_book(request, pk):
    with transaction.atomic():
        book = get_object_or_404(Book.objects.select_for_update(), pk=pk)
        active = Borrowing.objects.filter(member=request.user, returned_on__isnull=True)
        if book.available_copies < 1:
            messages.error(request, "No copies available right now.")
        elif active.filter(book=book).exists():
            messages.error(request, "You already have this book.")
        elif active.count() >= MAX_ACTIVE_LOANS:
            messages.error(request, f"You can borrow at most {MAX_ACTIVE_LOANS} books at a time.")
        else:
            b = Borrowing.objects.create(book=book, member=request.user)
            messages.success(request, f"Borrowed '{book.title}'. Due on {b.due_on:%d %b %Y}.")
    return redirect("book_detail", pk=pk)


@login_required
@require_POST
def return_book(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk, returned_on__isnull=True)
    if not (request.user.is_staff or borrowing.member == request.user):
        raise PermissionDenied
    borrowing.returned_on = timezone.localdate()
    borrowing.save(update_fields=["returned_on"])
    if borrowing.fine:
        messages.warning(request, f"Returned late. Fine: Rs. {borrowing.fine}")
    else:
        messages.success(request, "Book returned. Thank you!")
    if request.user.is_staff and request.POST.get("from") == "all":
        return redirect("all_borrowings")
    return redirect("my_borrowings")


class MyBorrowingsView(LoginRequiredMixin, ListView):
    template_name = "library/my_borrowings.html"
    context_object_name = "borrowings"

    def get_queryset(self):
        return Borrowing.objects.filter(member=self.request.user).select_related("book")


class AllBorrowingsView(StaffRequiredMixin, ListView):
    template_name = "library/all_borrowings.html"
    context_object_name = "borrowings"
    paginate_by = 20

    def get_queryset(self):
        qs = Borrowing.objects.select_related("book", "member")
        status = self.request.GET.get("status")
        today = timezone.localdate()
        if status == "active":
            qs = qs.filter(returned_on__isnull=True)
        elif status == "overdue":
            qs = qs.filter(returned_on__isnull=True, due_on__lt=today)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status"] = self.request.GET.get("status", "")
        ctx["total_books"] = Book.objects.count()
        ctx["active_count"] = Borrowing.objects.filter(returned_on__isnull=True).count()
        ctx["overdue_count"] = Borrowing.objects.filter(
            returned_on__isnull=True, due_on__lt=timezone.localdate()
        ).count()
        return ctx


# ---------- Accounts ----------
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("book_list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})
