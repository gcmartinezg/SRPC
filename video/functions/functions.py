path = 'video/static/uploads/'
path_to_uploaded_file = path + 'fileupload'
path_to_frames = path + 'frames/'
percentage_to_pick = 0.05

#TODO document functions 
def handle_uploaded_file(f):
    save_uploaded_file(f)
    try:
        validate_video(f)
    except ValueError as err:
        try:
            remove_file(f)
        except OSError as os_error:
            print(str(os_error))
            #RIP, nothing we can do. let's cross our fingers and pray for this never to happen
        else:
            raise err

def save_uploaded_file(f):
    with open(path_to_uploaded_file + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
            
# Opens the Video file
def extract_frames(f):
    import cv2

    cap=cv2.VideoCapture(path_to_uploaded_file + f.name)
    i=0
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        cv2.imwrite(path_to_frames + get_filename(f)+str(i)+'.jpg',frame)
        i+=1

    cap.release()
    cv2.destroyAllWindows()

def get_filename(f):
    try:
        return f.name[0:(f.name.index('.'))]
    except ValueError:
        #let's hope this never happen
        return ''

def validate_video(f):
    import moviepy.editor
    from pathlib import Path

    path = path_to_uploaded_file + f.name
    video = moviepy.editor.VideoFileClip(path)
    video_duration_sec = int(video.duration)
    #print(video_duration_sec)
    video_filesize = int(Path(path).stat().st_size)
    video.close()
    
    #TODO find more suitable exception to raise
    #TODO revisit the values on this conditions
    if video_duration_sec > 15:
        raise ValueError('The file exceeds 15 seconds')
    if video_filesize > 31457280:
        raise ValueError('The file exceeds 30 megabytes')

    return True

def remove_file(f):
    import os

    os.remove(path_to_uploaded_file+f.name)

def validate_file_extension(value):
    import os
    from django.core.exceptions import ValidationError

    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.mp4', '.mkv', '.avi']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')

def edsr_model(image):
    import cv2
    from cv2 import dnn_superres

    sr = dnn_superres.DnnSuperResImpl_create()
    path = 'video/static/models/EDSR_x3.pb'# ... /path/to/EDSR_x3.pb
    sr.readModel(path)
    sr.setModel("edsr", 3)
    result = sr.upsample(image)
    cv2.imwrite('path', result)# falta guardar en una ruta diferente a la de los frames 
    
def clean_up():
    """
    TODO handle clean up after finishing the processing:
    Removing the content of the frames folder
    Removing the root's contents of the uploads folder
    """

def pick_frames(name):
    import os
    from pathlib import Path
    from math import ceil

    frame_number = len(os.listdir(path_to_frames))
    frames_to_be_picked = ceil(frame_number * percentage_to_pick)

    random_list = random.sample(range(0, frame_number), frames_to_be_picked)
    picked_frames = [path_to_frames + name + random_number + '.jpg' for random_number in random_list]
    
    return picked_frames

def get_plate_openalpr(image_name):
    import subprocess
    cmd = ['docker', 'run', '-i', '--rm', '-v', path_to_frames+":/data:ro", 'openalpr', '-c',
           'eu', image_name]
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = b''
    for line in p.stdout.readlines():
        lines = lines + line
    retval = p.wait()
    print(lines.decode('utf-8').strip())

def get_plate_platerecognizer(image_path):
    import requests
    from pprint import pprint

    regions = ['co'] # Change to your country
    with open(image_path, 'rb') as fp:
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            data=dict(regions=regions),  # Optional
            files=dict(upload=fp),
            headers={'Authorization': 'Token c237819a800f880ca82b75543315a65330334d3d'})
    return response.json()