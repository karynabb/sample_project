import datetime

from django import forms


class OfferingDescriptionsRationalesGenerationForm(forms.Form):
    limit = forms.IntegerField(
        label="Limit of questionnaires to generate offering descriptions and rationales"
    )


class GamesGenerationForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=datetime.date.today,
        label="Start Date",
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=lambda: datetime.date.today() + datetime.timedelta(weeks=1),
        label="End Date",
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and start_date < datetime.date.today():
            self.add_error("start_date", "Start date cannot be in the past")

        if start_date and end_date and start_date > end_date:
            self.add_error(
                "end_date", "End date must be greater than or equal to the start date"
            )

        return cleaned_data
