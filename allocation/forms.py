from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import StudentProfile, User

from .models import Allocation, Block, Room


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
        roll_number = self.cleaned_data["roll_number"].strip()
        if (
            User.objects.filter(roll_number__iexact=roll_number).exists()
            or User.objects.filter(username__iexact=roll_number).exists()
        ):
            raise ValidationError("A user with this roll number already exists.")
        return roll_number

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email


class StudentEditForm(forms.Form):
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
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise ValidationError("A user with this email address already exists.")
        return email


class AllocationForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.STUDENT, is_active=True)
        .select_related("profile")
        .order_by("roll_number"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_student"}),
        label="Student",
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True, occupancy__lt=models.F("capacity"))
        .select_related("block")
        .order_by("block__name", "number"),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_room"}),
        label="Available Room",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].label_from_instance = (
            lambda u: (
                f"{getattr(getattr(u, 'profile', None), 'full_name', u.username)} "
                f"({u.roll_number or u.username}) "
                f"[{getattr(getattr(u, 'profile', None), 'gender', '-')}]"
            )
        )
        self.fields["room"].label_from_instance = (
            lambda r: (
                f"{r.block.name} Room {r.number} "
                f"({r.get_room_type_display()}, Policy: {r.block.get_gender_policy_display()}, "
                f"Free: {r.capacity - r.occupancy})"
            )
        )


class RoomChangeRequestForm(forms.Form):
    preferred_room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True).select_related("block").order_by("block__name", "number"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_preferred_room"}),
        label="Preferred Room (Optional)",
        empty_label="-- Any suitable room --",
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "id": "id_reason", "rows": 3}),
        label="Reason for Room Change",
        required=True,
    )

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        if student and hasattr(student, "profile"):
            gender = getattr(student.profile, "gender", None)
            qs = Room.objects.filter(is_active=True)
            if gender:
                qs = qs.filter(block__gender_policy=gender)
            current_alloc = Allocation.objects.filter(student=student, status=Allocation.Status.ACTIVE).first()
            if current_alloc:
                qs = qs.exclude(pk=current_alloc.room_id)
            self.fields["preferred_room"].queryset = qs.select_related("block").order_by("block__name", "number")

        self.fields["preferred_room"].label_from_instance = (
            lambda r: (
                f"{r.block.name} Room {r.number} "
                f"({r.get_room_type_display()}, Free: {max(r.capacity - r.occupancy, 0)})"
            )
        )
