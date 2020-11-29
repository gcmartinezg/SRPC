from django.shortcuts import render
from django.http import HttpResponse
from video.forms import upload
from video.functions.functions import handle_uploaded_file

# Create your views here.
def formsubmission(request):
    form = upload()
    if request.method == "POST":
        form = upload(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])
            return HttpResponse("Archivo cargado exitosamente!")
        else:
            form = upload()
    return render(request, 'video/home.html', {'form': form})

