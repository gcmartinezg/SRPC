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

class Statistics:
    def __init__(self, plate: str, confidence: float = 0):
        self.plate = plate
        self.top_plate = (plate, confidence)
        self.confidences = [confidence]
        self.calculate_average()

    def add(self, incoming_plate: dict):
        self.get_new_possible_plate(incoming_plate)
        self.confidences.append(incoming_plate['confidence'])
        self.calculate_average()

    def get_new_possible_plate(self, incoming_plate: dict):
        if self.plate is None or len(self.plate) == 0:
            self.plate = incoming_plate['plate']
            self.top_plate = tuple(incoming_plate.values())

        else:
            if self.top_plate[1] < incoming_plate['confidence']:
                self.plate = incoming_plate['plate']
                self.top_plate = tuple(incoming_plate.values())

    def calculate_average(self):
        self.average = sum(self.confidences)/len(self.confidences)

    def __str__(self):
        return f'Statistics(plate = {self.plate}, average = {self.average})'

    def __repr__(self):
        return f'Statistics(plate = {self.plate}, top_plate = {self.top_plate}, confidences = {self.confidences}, average = {self.average})'

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

def get_filename(f) -> str:
    try:
        return f.name[0:(f.name.index('.'))]
    except ValueError:
        #let's hope this never happen
        return ''

def validate_video(f) -> bool:
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
        #print(image)
        edsr_model(path_to_processed_frames+image)

def clean_up():
    """
    TODO handle clean up after finishing the processing:
    Removing the content of the frames folder
    Removing the root's contents of the uploads folder
    """

def pick_frames(name) -> list:
    import os
    from pathlib import Path
    from math import ceil
    import random

    frame_number = len(os.listdir(path_to_raw_frames)) - 1
    frames_to_be_picked = ceil(frame_number * percentage_to_pick)

    random_list = random.sample(range(0, frame_number), frames_to_be_picked)
    picked_frames = [path_to_raw_frames + name[0:name.index('.')] + str(random_number) + '.jpg' for random_number in random_list]
    
    return picked_frames

def get_result_list() -> list:
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

# taken from https://gist.github.com/badocelot/5327427
def damerau_levenshtein_distance_improved(a: str, b: str) -> int:
    # "Infinity" -- greater than maximum possible edit distance
    # Used to prevent transpositions for first characters
    INF = len(a) + len(b)

    # Matrix: (M + 2) x (N + 2)
    matrix  = [[INF for n in range(len(b) + 2)]]
    matrix += [[INF] + list(range(len(b) + 1))]
    matrix += [[INF, m] + [0] * len(b) for m in range(1, len(a) + 1)]

    # Holds last row each element was encountered: DA in the Wikipedia pseudocode
    last_row = {}

    # Fill in costs
    for row in range(1, len(a) + 1):
        # Current character in a
        ch_a = a[row-1]

        # Column of last match on this row: DB in pseudocode
        last_match_col = 0

        for col in range(1, len(b) + 1):
            # Current character in b
            ch_b = b[col-1]

            # Last row with matching character
            last_matching_row = last_row.get(ch_b, 0)

            # Cost of substitution
            cost = 0 if ch_a == ch_b else 1

            # Compute substring distance
            matrix[row+1][col+1] = min(
                matrix[row][col] + cost, # Substitution
                matrix[row+1][col] + 1,  # Addition
                matrix[row][col+1] + 1,  # Deletion

                # Transposition
                # Start by reverting to cost before transposition
                matrix[last_matching_row][last_match_col]
                    # Cost of letters between transposed letters
                    # 1 addition + 1 deletion = 1 substitution
                    + max((row - last_matching_row - 1),
                          (col - last_match_col - 1))
                    # Cost of the transposition itself
                    + 1)

            # If there was a match, update last_match_col
            if cost == 0:
                last_match_col = col

        # Update last row for current character
        last_row[ch_a] = row

    # Return last element
    return matrix[-1][-1]

def get_statistics(result_list: list):
    """TODO pending"""
    unique_plates = []
    for frame_result in result_list:
        candidates = frame_result['results_list']
        if candidates is not None and len(candidates) > 0:
            """dictionaries keep the insertion order from python 3.6+. openalpr returns an ordered list, 
            so the most possible plate always should be the first one."""
            candidate = candidates[0]
            print('candidate', candidate)
            if len(unique_plates) == 0:
                #print('first insert')
                unique_plates.append(Statistics(candidate['plate'], candidate['confidence']))

            else:
                for index, unique_plate in enumerate(unique_plates):
                    #print('distance', unique_plate.plate, 'and', candidate['plate'], '=', damerau_levenshtein_distance_improved(unique_plate.plate, candidate['plate']))
                    if damerau_levenshtein_distance_improved(unique_plate.plate, candidate['plate']) < 3:
                        print('perhaps same')
                        unique_plates[index].add(candidate)

                    else:
                        print('most likely different')
                        unique_plates.append(Statistics(candidate['plate'], candidate['confidence']))

                    print(unique_plates)

    return unique_plates

def get_plate_openalpr(image_name: str) -> list:
    import subprocess
    from os import linesep
    import re
    import json
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
    #print(lines)
    recognized_plates = json.loads(lines)["results"]
    # plates = re.split('plate\d+: \d+ results',  lines)

    result_object_list = []

    for recognized_plate in recognized_plates:
        print(image_name)
        if(len(recognized_plate) > 0):
            candidates = recognized_plate["candidates"]
            for candidate in candidates:
                candidate.pop("matches_template", None)
                result_object_list.append(candidate)

            #print(result_object_list)
        #else: 
            #print("[]")
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