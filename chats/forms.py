from django.forms import ModelForm
from django import forms
from .models import *
from django.utils.translation import gettext_lazy as _

class ChatmessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body']
        labels = {
            'body': '',
        }
        widgets = {
            'body' : forms.TextInput(attrs={'placeholder': _('Add message ...'), 'class': 'p-4 text-black', 'maxlength' : '300', 'autofocus': True }),
        }