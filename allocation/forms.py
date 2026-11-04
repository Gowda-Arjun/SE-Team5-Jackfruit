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
