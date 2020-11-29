def handle_uploaded_file(f):
    with open('video/static/fileupload'+f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
