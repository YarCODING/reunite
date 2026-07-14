from django.forms import ModelForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Profile

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        exclude = ['user']
        widgets = {
            'image': forms.FileInput(),
            'displayname': forms.TextInput(attrs={'placeholder': _('Add display name'), 'class': 'textarea'}),
            'info': forms.Textarea(attrs={'rows':3, 'placeholder': _('Add information'), 'class': 'textarea'})
        }

        labels = {
            'image': _('Image'),
            'displayname': _('Display name'),
            'info': _('Info'),
        }

class EmailForm(ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']