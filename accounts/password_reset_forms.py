from django import forms
from django.contrib.auth.password_validation import validate_password


class RequestResetForm(forms.Form):
    email = forms.EmailField()


class VerifyResetOTPForm(forms.Form):
    email = forms.EmailField()
    otp = forms.CharField(min_length=6, max_length=6, strip=True)
    new_password = forms.CharField(widget=forms.PasswordInput, validators=[validate_password])
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned
