path = 'video/static/uploads/'
path_to_uploaded_file = path + 'fileupload'
path_to_frames = path + 'frames/'
path_to_raw_frames = path_to_frames + 'raw/'
path_to_processed_frames = path_to_frames + 'processed/'
percentage_to_pick = 0.05
current_directory = None

class Result:
    def __init__(self, image_name, results_list):
        self.image_name = image_name
        self.results_list = results_list

    def __str__(self):
        return f'Result(image_name = {self.image_name}, results_list = {self.results_list})'

    def __repr__(self):
        return f'Result(image_name = {self.image_name}, results_list = {self.results_list})'

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
        cv2.imwrite(path_to_raw_frames + get_filename(f)+str(i)+'.jpg',frame)
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

def edsr_model(image_path):
    import cv2
    from cv2 import dnn_superres

    # Create an SR object
    sr = dnn_superres.DnnSuperResImpl_create()

    print(image_path)
    # Read image
    image = cv2.imread(image_path)

    # Read the desired model
    path = "video/static/models/EDSR_x3.pb"
    sr.readModel(path)

    # Set the desired model and scale to get correct pre- and post-processing
    sr.setModel("edsr", 3)

    # Upscale the image
    result = sr.upsample(image)

    # Save the image
    cv2.imwrite(image_path, result)

def copy_files(file_list):
    from shutil import copy as cp

    for image_path in file_list:
        cp(image_path, path_to_processed_frames)

def apply_superresolution(filename):
    import os

    picked_frames = pick_frames(filename)
    copy_files(picked_frames)

    for image in os.listdir(path_to_processed_frames):
        if image.index('.') == 0:
            continue
        print(image)
        edsr_model(path_to_processed_frames+image)

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
    import random

    frame_number = len(os.listdir(path_to_raw_frames)) - 1
    frames_to_be_picked = ceil(frame_number * percentage_to_pick)

    random_list = random.sample(range(0, frame_number), frames_to_be_picked)
    picked_frames = [path_to_raw_frames + name[0:name.index('.')] + str(random_number) + '.jpg' for random_number in random_list]
    
    return picked_frames

def placeholder():
    import os
    #import Result

    results_per_frame = []

    for image in os.listdir(path_to_processed_frames):
        if image.index('.') == 0:
            continue

        frame_result = Result(image, get_plate_openalpr(image))
        results_per_frame.append(frame_result)

    #result = get_statistics(results_per_frame)

    return results_per_frame

#def get_statistics(results):
    

def get_plate_openalpr(image_name):
    import subprocess
    from os import linesep
    import re
    global current_directory
    if current_directory is None:
        cd = ['echo', '%cd%']
        p_cd = subprocess.Popen(cd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines_bytes_cd = b''
        array_cd = []
        for line in p_cd.stdout.readlines():
            lines_bytes_cd = lines_bytes_cd + line
        current_directory = lines_bytes_cd.decode('utf-8').strip()
    #print(len(lines_cd))
    # cmd = ['docker', 'run', '-i', '--rm', '-v', "D:/Documentos/workspace/python/SRPC/video/static/uploads/frames/processed/:/data:ro", 'openalpr', '-c',
    #         'eu', image_name]
    cmd = ['docker', 'run', '-i', '--rm', '-v', current_directory+"/video/static/uploads/frames/processed/:/data:ro", 'openalpr', '-c', 
            'eu', '--json',image_name]
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines_bytes = b''
    for line in p.stdout.readlines():
        lines_bytes = lines_bytes + line
    
    retval = p.wait()
    lines = lines_bytes.decode('utf-8').strip()
    print(lines)
    # plates = re.split('plate\d+: \d+ results',  lines)

    result_object_list = []
    """
    for plate in plates:
        if not plate:
            continue
        
        candidates = plate.strip().split('\n')
        result_list = []
        for candidate in candidates:
            if not candidate:
                continue
            
            matcher = re.search(r'\s{0,4}-\s(\w+)\s+confidence:\s([0-9]*[.,]{0,1}[0-9]*)',candidate)
            tuple_matcher = matcher.group(1,2)
            result_list.append(tuple_matcher)
        
        result_object_list.append(result_list)
    """

    return result_object_list


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