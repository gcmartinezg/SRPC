from django import forms

class upload(forms.Form):
    name = forms.CharField(label="Enter name", max_lenght=50)
    email = forms.EmailField()
    file = forms.FileField()