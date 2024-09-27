import os
import json

def fetch_inputfiles(dir):
    files = None
    try:
        files = os.listdir(dir)
    except FileNotFoundError:
        return None
    files = [f for f in files if os.path.isfile(dir+'/'+f)]
    return files

def fetch_foot_angles(file_name):
    with open(file_name, 'r') as file:
        data = json.load(file)
    return data