import os
import requests
# from utility import localFileServerPath

headers = {
    'accept': 'application/json'
}

path_of_the_directory = 'massUpload'
end_point = 'http://127.0.0.1:8000/dashboard'
ext = ('.pdf')
dirLength = len(os.listdir(path_of_the_directory))
currentCount = 1
for files in os.listdir(path_of_the_directory):
    if files.endswith(ext):
        print(files)
        tags = input("Enter tags: ")
        currentFile = os.path.join(path_of_the_directory,files)
        files = {
            'uploadedfile': open(currentFile, 'rb', encoding='utf-8'),
            'categorytexts': (None, str(tags))
        }
        response = requests.post(end_point, headers=headers, files=files)
        print(str(currentCount) + "/" + str(dirLength) + ": " + currentFile)  
        currentCount += 1
    else:
        continue