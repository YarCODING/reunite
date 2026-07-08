from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'type', 'category', 'city', 'description', 'image']
        
        INPUT_CLASSES = (
            "w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 "
            "bg-gray-50 dark:bg-gray-800 text-sm text-slate-900 dark:text-white "
            "placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none "
            "focus:border-primary dark:focus:border-primary/70 focus:ring-4 focus:ring-primary/10 transition duration-200"
        )
        
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'e.g., iPhone 13 Pro Max'}),
            'type': forms.Select(attrs={'class': INPUT_CLASSES}),
            'category': forms.Select(attrs={'class': INPUT_CLASSES}),
            'city': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'e.g., Berlin'}),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASSES, 
                'rows': 4, 
                'placeholder': 'Provide details (color, serial numbers, unique marks)...'
            }),
            'image': forms.FileInput(attrs={
                'class': "w-full text-sm text-gray-500 dark:text-gray-400 "
                         "file:mr-4 file:py-2.5 file:px-4 file:rounded-xl "
                         "file:border-0 file:text-xs file:font-bold file:uppercase file:tracking-wider "
                         "file:bg-primary/10 dark:file:bg-primary/20 file:text-primary dark:file:text-primary "
                         "hover:file:bg-primary/20 dark:hover:file:bg-primary/30 file:cursor-pointer transition"
            }),
        }