from django import forms
from django.core.exceptions import ValidationError

from .models import Block, Room


class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ["name", "gender_policy"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "id_name"}),
            "gender_policy": forms.Select(attrs={"class": "form-select", "id": "id_gender_policy"}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["block", "floor", "number", "room_type", "capacity"]
        widgets = {
            "block": forms.Select(attrs={"class": "form-select", "id": "id_block"}),
            "floor": forms.NumberInput(attrs={"class": "form-control", "id": "id_floor"}),
            "number": forms.TextInput(attrs={"class": "form-control", "id": "id_number"}),
            "room_type": forms.Select(attrs={"class": "form-select", "id": "id_room_type"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "id": "id_capacity", "min": 1}),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is not None and capacity < 1:
            raise ValidationError("Capacity must be at least 1.")
        return capacity

    def clean(self):
        cleaned_data = super().clean()
        block = cleaned_data.get("block")
        number = cleaned_data.get("number")
        if block and number:
            qs = Room.objects.filter(block=block, number=number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({"number": "A room with this number already exists in this block."})
        return cleaned_data


class StudentCreateForm(forms.Form):
    from accounts.models import StudentProfile

    roll_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_roll_number"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "id": "id_email"}),
    )
    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_full_name"}),
    )
    gender = forms.ChoiceField(
        choices=StudentProfile.Gender.choices,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_gender"}),
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_phone"}),
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "id": "id_address", "rows": 2}),
        required=False,
    )
    guardian_name = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_guardian_name"}),
    )
    guardian_phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_guardian_phone"}),
    )
    emergency_contact = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_emergency_contact"}),
    )

    def clean_roll_number(self):
        from accounts.models import User

        roll_number = self.cleaned_data["roll_number"].strip()
        if (
            User.objects.filter(roll_number__iexact=roll_number).exists()
            or User.objects.filter(username__iexact=roll_number).exists()
        ):
            raise ValidationError("A user with this roll number already exists.")
        return roll_number

    def clean_email(self):
        from accounts.models import User

        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email


class StudentEditForm(forms.Form):
    from accounts.models import StudentProfile

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "id": "id_email"}),
    )
    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_full_name"}),
    )
    gender = forms.ChoiceField(
        choices=StudentProfile.Gender.choices,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_gender"}),
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_phone"}),
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "id": "id_address", "rows": 2}),
        required=False,
    )
    guardian_name = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_guardian_name"}),
    )
    guardian_phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_guardian_phone"}),
    )
    emergency_contact = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_emergency_contact"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        from accounts.models import User

        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise ValidationError("A user with this email address already exists.")
        return email
