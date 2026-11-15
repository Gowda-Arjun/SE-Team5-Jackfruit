from datetime import date, timedelta

from django import forms

from .models import FeeStructure


class ReconciliationForm(forms.Form):
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        today = date.today()
        kwargs.setdefault(
            "initial",
            {"date_from": today - timedelta(days=30), "date_to": today},
        )
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            self.add_error("date_to", "The end date must be on or after the start date.")
        return cleaned_data


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
