from django import forms
from video.functions.functions import validate_file_extension


class upload(forms.Form):
    name = forms.CharField(label="Enter name", max_length=50)
    email = forms.EmailField()
    file = forms.FileField(validators=[validate_file_extension])