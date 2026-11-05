import datetime

from django import forms

from .services import REPORT_TYPES


def _first_of_month():
    return datetime.date.today().replace(day=1)


class ReportForm(forms.Form):
    type = forms.ChoiceField(choices=REPORT_TYPES.items(), label="Report")
    date_from = forms.DateField(label="From", initial=_first_of_month, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(label="To", initial=datetime.date.today, widget=forms.DateInput(attrs={"type": "date"}))

    def clean(self):
        data = super().clean()
        if data.get("date_from") and data.get("date_to") and data["date_from"] > data["date_to"]:
            raise forms.ValidationError("The start date must be on or before the end date.")
        return data
