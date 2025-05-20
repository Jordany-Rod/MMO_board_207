from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms
from .models import Post, Reply, Category
from ckeditor.widgets import CKEditorWidget


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            user.generate_confirmation_code()  # Генерируем код подтверждения
        return user

class PostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='default'))

    class Meta:
        model = Post
        fields = ['title', 'category', 'content', 'image']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'content': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Заголовок объявления',
            'content': 'Текст объявления',
            'category': 'Категория',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убедимся, что все категории загружены
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Выберите категорию"

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Напишите ваш отклик...'
            })
        }
        labels = {
            'text': ''
        }