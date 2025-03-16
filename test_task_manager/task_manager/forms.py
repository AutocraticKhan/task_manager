from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

class LoginForm(AuthenticationForm):
    pass

class SignupForm(UserCreationForm):
    pass

class TaskForm(forms.Form):
    description = forms.CharField(widget=forms.Textarea)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    priority = forms.ChoiceField(choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ])
