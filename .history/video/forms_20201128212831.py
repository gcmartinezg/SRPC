from django import forms

class upload(forms.Form):
    name = forms.CharField(label="Enter name", max_length=50)
    email = forms.EmailField()
    file = forms.FileField()