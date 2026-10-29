from django import forms

from .models import FeeStructure


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ["term", "room_type", "amount", "due_date", "effective_from"]
        widgets = {
            "term": forms.TextInput(attrs={"class": "form-control"}),
            "room_type": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "min": "0.01", "step": "0.01"}
            ),
            "due_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "effective_from": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }
