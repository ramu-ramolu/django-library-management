from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["title", "author", "isbn", "category", "description", "total_copies"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_isbn(self):
        isbn = self.cleaned_data["isbn"].replace("-", "").strip()
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise forms.ValidationError("Enter a valid 10 or 13 digit ISBN.")
        return isbn

    def clean_total_copies(self):
        copies = self.cleaned_data["total_copies"]
        if self.instance.pk:
            issued = self.instance.borrowings.filter(returned_on__isnull=True).count()
            if copies < issued:
                raise forms.ValidationError(
                    f"{issued} copies are currently issued; total cannot be lower."
                )
        return copies


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
