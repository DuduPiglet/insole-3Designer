import os

def fetch_files(dir):
    files = None
    try:
        files = os.listdir(dir)
    except FileNotFoundError:
        return None
    files = [f for f in files if os.path.isfile(dir+'/'+f)]
    return files