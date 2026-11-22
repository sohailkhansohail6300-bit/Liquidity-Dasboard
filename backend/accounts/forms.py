from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.core.exceptions import ValidationError

from .models import User


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput, strip=False)

    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'kind', 'status', 'is_active',
            'is_demo', 'is_superuser', 'groups', 'user_permissions',
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The two password fields did not match.')
        elif password1:
            try:
                password_validation.validate_password(password1, self.instance)
            except ValidationError as error:
                self.add_error('password1', error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            self.save_m2m()
        return user


class AdminUserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
