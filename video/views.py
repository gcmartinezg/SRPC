from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from video.forms import upload
from video.functions.functions import handle_uploaded_file, extract_frames, apply_superresolution

# Create your views here.
def formsubmission(request):
    form = upload()
    if request.method == "POST":
        form = upload(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                handle_uploaded_file(uploaded_file)
            except ValueError as err:
                return HttpResponseBadRequest(str(err))

            extract_frames(uploaded_file)
            apply_superresolution(uploaded_file.name)
            return HttpResponse("Archivo cargado exitosamente!")
        else:
            form = upload()
    return render(request, 'video/home.html', {'form': form})