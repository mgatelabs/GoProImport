import os
import re
import subprocess
import json
import sys

class GoProVideo:
    segment = 0
    chapter = 0
    key = 0
    filename = ""
    def __init__(self, segment, chapter, filename):
        self.segment = segment
        self.chapter = chapter
        self.key = (self.segment * 10000) + self.chapter
        self.filename = filename
    def __repr__(self):
        return '{' + str(self.segment) + ', ' + str(self.chapter) + ', ' + str(self.key) + '}'

def load_config():
    
    actual_config = {}
    
    if os.path.isfile('./config.json'):
        with open('./config.json', 'r', encoding='utf-8') as f:
            json_file = json.load(f)
        
        if (json_file['ffmpeg'] is None):
            pass
        else:
            actual_config['ffmpeg'] = json_file['ffmpeg']

        if (json_file['gopro_source'] is None):
            pass
        else:
            actual_config['gopro_source'] = json_file['gopro_source']
        
        if (json_file['gopro_destination'] is None):
            pass
        else:
            actual_config['gopro_destination'] = json_file['gopro_destination']    
            
    else:
        print("config.json not found")

    return actual_config

def choose_folder(path):
    all_list = os.listdir(path)
    folder_list = []
    for x in all_list:
        if os.path.isdir(os.path.join(path + "/", x)):
            folder_list.append(x)
    i = 0
    while i < len(folder_list):
        print(str(i) + ": " + folder_list[i] )
        i = i + 1
    selection = input("Which Folder: ")
    return folder_list[int(selection)]

def find_videos(path):
    pat = re.compile("G[HX](\d\d)(\d\d\d\d).*")
    all_list = os.listdir(path)
    file_list = []
    obj_list = []
    for x in all_list:
        if os.path.isfile(os.path.join(path + "/", x)):
            if re.match('^G[HX]\d+.*MP4$', x):
                file_list.append(x)
    i = 0
    while i < len(file_list):
        pieces = (pat.findall(file_list[i]))
        #print(pieces[0][0])
        chap = int(pieces[0][0])
        seg = int(pieces[0][1])
        obj_list.append(GoProVideo(seg, chap, file_list[i]))
        i = i + 1
    return obj_list

def writeOutputFile(items, txtFilePath, fullPath):
    with open(txtFilePath, 'w') as f:
        for x in items:
            f.write("file '")
            f.write(fullPath)
            f.write("\\")
            f.write(x.filename)
            f.write("'\n");

def processVideo(outTxt, outMp4, ffmpeg):
    args = []
    args.append(ffmpeg)
    args.append("-f")
    args.append("concat")
    args.append("-safe")
    args.append("0")
    args.append("-i")
    args.append("\"" + outTxt + "\"")
    args.append("-c")
    args.append("copy")
    args.append("\"" + outMp4 + "\"")
    cmd = " ".join(args)
    print(cmd)
    subprocess.run(cmd, shell=True, capture_output=True)

def filerVideos(videos, desiredSegment):
    result = []
    for x in videos:
        if x.segment == desiredSegment:
            result.append(x)
    return result

print(""" _   _ _     _             ______ _               
| | | (_)   | |            |  ___(_)              
| | | |_  __| | ___  ___   | |_   ___  _____ _ __ 
| | | | |/ _` |/ _ \/ _ \  |  _| | \ \/ / _ \ '__|
\ \_/ / | (_| |  __/ (_) | | |   | |>  <  __/ |   
 \___/|_|\__,_|\___|\___/  \_|   |_/_/\_\___|_|  """)
print("")
print("By Michael Fuller")
print("")
1
config = load_config()

if not 'ffmpeg' in config:
    sys.exit("Please setup the config.json file, ffmpeg key is missing")

if not 'gopro_source' in config:
    sys.exit("Please setup the config.json file, gopro_source key is missing")
    
if not 'gopro_destination' in config:
    sys.exit("Please setup the config.json file, gopro_destination key is missing")

# Choose the Date
root_folder = choose_folder(config['gopro_source'])
# Choose the Camera
folder_two = choose_folder(os.path.join(config['gopro_source'], root_folder));
sub_folder = os.path.join(config['gopro_source'], root_folder, folder_two)
# Find Videos
goProVidoes = find_videos(sub_folder)

goProVidoes.sort(key=lambda x: x.key, reverse=False)

videoKeys = []
videoLookup = {}
for x in goProVidoes:
    if x.segment in videoLookup:
        # No Op
        pass
    else:
        videoKeys.append(x.segment)
        videoLookup[x.segment] = True

directory = os.getcwd()

out_file_path = os.path.join(sub_folder, "out.txt")

out_mp4_prefix =  os.path.join(config['gopro_destination'], root_folder + "_" + folder_two)



if len(videoLookup) > 1:
    print("Multiple Segments, What to Do?")
    print("0: Join All")
    print("1: Separate")
    print("2: Custom")
    choi = input("Which Action: ")
    if choi == '0':
        print("Converting:")
        writeOutputFile(goProVidoes, out_file_path, sub_folder)
        processVideo(out_file_path, out_mp4_prefix + ".mp4", config['ffmpeg'])
    elif choi == '1':
        for videoSegment in videoKeys:
            print("")
            print("Starting Segment: " + str(videoSegment))
            filtered = filerVideos(goProVidoes, videoSegment)
            writeOutputFile(filtered, out_file_path, sub_folder)
            processVideo(out_file_path, out_mp4_prefix + "_" + str(videoSegment) + ".mp4", config['ffmpeg'])
            print("Finished Segment: " + str(videoSegment))
    elif choi == '2':
        toProcess = []
        segmentName = ""
        while True:
            print("Current Files: " + str(toProcess))
            print("Choose a Segment, 0 to continue")
            for videoSegment in videoKeys:
                print("Segment: " + str(videoSegment))
            sel = int(input("Which Segment: "))
            if sel == 0:
                break
            else:
                if len(segmentName) > 0:
                    segmentName = segmentName + "_"
                segmentName += str(sel)
                filtered = filerVideos(goProVidoes, sel)
                toProcess.extend(filtered)
        print("Converting:")
        writeOutputFile(toProcess, out_file_path, sub_folder)
        processVideo(out_file_path, out_mp4_prefix + "_" + segmentName + ".mp4", config['ffmpeg'])
else:
    # Output a Single File
    writeOutputFile(goProVidoes, out_file_path, sub_folder)
    processVideo(out_file_path, out_mp4_prefix + ".mp4", config['ffmpeg'])

print("Finished")