from django import forms
from django.contrib.auth import get_user_model

from schedule.models import Slot

User = get_user_model()


class CreateSlotForm(forms.ModelForm):
    class Meta:
        model = Slot
        fields = ('date', 'time')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
        }


class UpdateSlotForm(forms.ModelForm):

    class Meta:
        model = Slot
        fields = ['user', 'is_booked', 'date', 'time']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'is_booked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
