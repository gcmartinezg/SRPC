from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from video.forms import upload
from video.functions.functions import handle_uploaded_file, extract_frames, apply_superresolution, get_result_list, get_statistics
from json import JSONEncoder, dumps

class CustomEncoder(JSONEncoder):
    def default(self, o):
            return o.__dict__

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
            result_list = get_result_list()
            response = get_statistics(result_list)

            return HttpResponse(dumps(response, cls=CustomEncoder), 'application/json')
            #return HttpResponse('xd')
        else:
            form = upload()
    return render(request, 'video/home.html', {'form': form})