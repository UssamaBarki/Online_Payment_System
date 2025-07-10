from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        pass


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    currency = forms.ChoiceField(choices=[('GBP', 'GBP'), ('USD', 'USD'), ('EUR', 'EUR')])  # Add other currencies as needed
    first_name = forms.CharField(max_length=30)  # Added first name
    last_name = forms.CharField(max_length=30)  # Added last name

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']


class AdminRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_staff = True  # Mark as admin
        if commit:
            user.save()
        return user