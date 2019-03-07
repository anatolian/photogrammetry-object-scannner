#!/usr/bin/env python

import socket
from time import sleep
from datetime import datetime
#from sh import gphoto2 as gp
import signal, os, subprocess
import RPi.GPIO as GPIO
import json
import sys
# from os_capture import capture # Importing this script causes one camera to take a shot. I guess Python is built to be like that. 
from download_and_rename import download_and_rename

import socket
import threading
import csv
import time

# two_camera_batch..., but cleaner. 2/9
# Camera control code credit: The Zan Show
# Motor control code credit: https://medium.com/@Keithweaver_/controlling-stepper-motors-using-python-with-a-raspberry-pi-b3fbd482f886

# Set up motor pins and step cycle at the start of the script
GPIO.setmode(GPIO.BCM)

# Also set up pins for the new TB6600 motor driver
MD_DIR = 17 # Board 11 (SPI1 CS0)
MD_PUL = 27 # Board 13
MD_ENA = 22 # Board 15
GPIO.setup(MD_PUL, GPIO.OUT)
GPIO.setup(MD_DIR, GPIO.OUT)
GPIO.setup(MD_ENA, GPIO.OUT)
# Set enable to always HIGH
GPIO.output(MD_ENA, 1)
# We don't really care for direction so I guess we can keep it low
GPIO.output(MD_DIR, 0)

# Define constant commands for terimnal window camera control
CAMERA_PIC_PATH = "/store_00020001/DCIM/100CANON"
DELETE_FLAG = "-D" # equivalent to "--delete-all-files"
RECURSE_FLAG = "-R"
DOWNLOAD_ALL_FLAG = "-P" # equivalent to "--get-all-files"
clearCommand = ["gphoto2", "--folder", CAMERA_PIC_PATH, \
                DELETE_FLAG, RECURSE_FLAG]
captureAndDownloadCommand = ["--capture-image-and-download"]
downloadCommand = [DOWNLOAD_ALL_FLAG]
autoDetectCommand = ['gphoto2', '--auto-detect']

# Define some directory paths
HOME_PI = "/home/pi/"
CAPTURE_METHOD_FILE= HOME_PI+'Scripts/os_capture.py'
DELETE_METHOD_FILE = HOME_PI+'Scripts/os_delete.py'
DOWNLOAD_AND_RENAME_METHOD_FILE = HOME_PI+'Scripts/download_and_rename.py'
CAPTURE_METHOD_FALLBACK_FILE= HOME_PI+'Scripts/os_capture_and_download.py'
DOWNLOAD_AND_RENAME_ALT_METHOD_FILE = HOME_PI+'Scripts/download_and_rename_by_input.py'
IMAGE_STORAGE_BASE_ADDR = HOME_PI+"Desktop/gphoto/images/"

# These are used to filter printouts from --auto-detect to find the port numbers
CAMERA_MODEL = "Canon EOS 1300D"
CAMERA_MODEL_NO_SPACE = "Canon\ EOS\ 1300D"

# More constants for motor control
NUM_OF_PICS_PER_SHERD = 20.0 # The number of pictures you want to take in a full cycle. 
DELAY = 0.002 # Unit: seconds. The time that the controller code waits before doing the next step.
FULL_STEPPER_CYCLE_STEPS = 200 # Stepper motors use 200 steps for a full cycle.
GEAR_RATIO = 4 # Multiply this number to FULL_STEPPER_CYCLE_STEPS to get the real number of steps our small motor needs to turn in order to make the big table spin one full cycle. See line below.
MICRO_STEPPING_SCALE = 8 # The fraction of a step that each pulse drives
FULL_CYCLE_STEPS = FULL_STEPPER_CYCLE_STEPS * GEAR_RATIO * MICRO_STEPPING_SCALE
AVG_STEPS_PER_SHOT = FULL_CYCLE_STEPS / NUM_OF_PICS_PER_SHERD
SLEEP_TIME_BETWEEN_SHOTS = 1 # Unit: seconds. Planned to wait this long for oscillation to vanish before taking the next turn, but it seems the delay that cameras need to capture rendered this useless.
REDEMPTION_TIMEOUT = 15
REDEMPTION_POLL_FREQ = 2
REDEMPTION_POLL_INTERVAL = 1.0 / REDEMPTION_POLL_FREQ

# Testing Vars
PHOTO_FAILS = 0
CYCLE_START = 0
BEGIN_DOWNLOAD = 0
FINISH_DOWNLOAD = 0

# Read in some file that records previous state
#STATE_FILE = open(HOME_PI+'Scripts/vars/parameters.json', 'r+')
'''try:
    STATE_VAR = json.load(STATE_FILE)
except:
    print("JSON failed again as usual. Creating a new one.")
    STATE_FILE.close()
    with open(HOME_PI+'Scripts/vars/parameters.json', 'w') as json_is_crap_again:
        json.dump({"sherd ID": 420}, json_is_crap_again)
    STATE_FILE = open(HOME_PI+'Scripts/vars/parameters.json', 'r+')
    STATE_VAR = json.load(STATE_FILE)
'''
#SHERD_ID = STATE_VAR["sherd ID"]

# Parameters for debug mode / logging
openproc = False
DEBUG_MODE = False # If True, write debug logfiles
KEEP_OLD_LOG_FILE = False # Change this to True once we know how to chmod newly created files
if DEBUG_MODE:
    from gphoto_log_trim_tool import trim_file

# Kill the gphoto process that starts
# whenever we turn on the camera or reboot the raspberry pi.
# Also kill the gvfsd thing or whatever it's called
def killGphoto2Process():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    # Search for the process we want to kill
    for line in out.splitlines():
        if (b'gvfsd-gphoto2' in line) or (b'gvfs-gphoto2-volume-monitor' in line):
            # Kill that process!
            pid = int(line.split(None,1)[0])
            os.kill(pid, signal.SIGKILL)


# Unmount external drive then remount to new location
# This lets you write to this read-only drive
# Haven't found way to make it work with /etc/.fstab
# Only need this for if rpi boots up again i think?
def mountDrive():
    if helpMountDrive() != True:
        if subprocess.call("mount | grep /mnt/usb", shell=True) == 1: # mounted unsuccessful
            print("External drive unable to be mounted")
            return False
    return True

def helpMountDrive():
    mounted = subprocess.call("mount | grep /mnt/usb", shell=True) # 0 = mounted, 1 = not
    if mounted == 1:
        if subprocess.call("mount | grep /dev/sda1", shell=True) == 0:
            subprocess.call("sudo umount /dev/sda1", shell=True)
            subprocess.call("sudo mount /dev/sda1 /mnt/usb -o uid=pi,gid=pi", shell=True)
        elif subprocess.call("mount | grep /dev/sdb1", shell=True) == 0:
            subprocess.call("sudo umount /dev/sdb1", shell=True)
            subprocess.call("sudo mount /dev/sdb1 /mnt/usb -o uid=pi,gid=pi", shell=True)
        else:
            print("External drive undetected")
        return False
    else:
        print("External drive ready to use")
        return True

# Reset the capture target to card, so we can keep the file
def resetCaptureTarget():
    # Use subprocess because we don't want its garbage output
    p = subprocess.Popen(['gphoto2','--set-config','capturetarget=1'], stdout=subprocess.PIPE)
    p.wait()
    #out,err = p.communicate()
    #os.system('gphoto2 --set-config capturetarget=1')

# Find the right ports of the cameras
def findCameraPorts():
    p = subprocess.Popen(autoDetectCommand, stdout=subprocess.PIPE)
    out, err = p.communicate()
    ports = []
    
    # Search for the outputs
    for line in out.splitlines():
        if CAMERA_MODEL in line:
            ports.append(line.split("usb:")[-1].rstrip())
    
    if len(ports) == 0:
        print("No camera port found!!!")
        sys.exit(0)
    return ports

# Clear all files from camera. ###Might be a source of excessive printout
def clearCameraFiles():
    for i in range(num_of_ports):
        # We used to run this directly from here, but now we call subprocesses to deter excessive printouts
        #p = subprocess.Popen(clearCommand + ["--port", 'usb:'+ports[i]])
        p = subprocess.Popen(['python', DELETE_METHOD_FILE, ports[i]], stdout=subprocess.PIPE)
        out, err = p.communicate() # If we want true parallel, we put this in a second loop, and make p belong to a list of processes. But deletion should be fast, so no...

# Create a new folder to save files to
def createSaveFolder(save_location):
    try:
        os.makedirs(save_location)
    except:
        if (os.path.isdir(save_location) == False):
            print("Failed to create new directory: "+save_location)

# cd into the target directory (possibly a drive) first, so the Pi isn't startled.
def createSaveFolderSoftly(save_folder_base_addr, save_folder_name):
    original_pwd = os.getcwd()
    os.chdir(save_folder_base_addr)
    try:
        os.makedirs(save_folder_name)
        print("Create new directory "+save_folder_name+" in "+save_folder_base_addr)
    except:
        print("Failed to create new directory "+save_folder_name+" in "+save_folder_base_addr)

# Captures images on camera (without downloading) by running the script os_capture.py
def captureImages(dir = '', name = '', index = 0):
    global PHOTO_FAILS # long test
    # Create a list of subprocesses
    procs = range(num_of_ports)
    failed_procs = []
    resetCaptureTarget() # Moved this here
    if ((DEBUG_MODE == False) or (len(dir) == 0 or len(name) == 0)):
        # If not in debug mode, or if arguments not enough for debug mode, we only capture the image 
        for i in range(num_of_ports):
            # Each subprocess calls the capture python script with port as argument to specify which camera to use
            procs[i] = subprocess.Popen(['python', CAPTURE_METHOD_FILE, ports[i]], stdout=subprocess.PIPE)
    else:
        # In legitimate debug mode, pass in the path for the debug file as well. 
        for i in range(num_of_ports):
            procs[i] = subprocess.Popen(['python', CAPTURE_METHOD_FILE, ports[i], \
                                         dir+'/camera'+str(i)+'/'+name+str(i+1)+'.txt'], \
                                         stdout=subprocess.PIPE)
        '''if DEBUG_MODE:
        for i in range(len(ports)):
            print("Waiting for camera %d to finish" % i)
            procs[i].wait()
            print("Trimming logfile for camera %d", i)
            trim_file(dir_and_name+str(i+1)+".txt", KEEP_OLD_LOG_FILE)'''
    # Wait for capturing to finish
    for i in range(num_of_ports):
        #procs[i].wait()
        out,err = procs[i].communicate()
        print("Camera #%d: "%i + out)
        if "capt0000" in out:
            # This means the camera accidentally stored the image in RAM instead of card. We need to retake the picture.
            print("Camera #%d failed to store picture. Retaking in process." % i)
            PHOTO_FAILS += 1# long test
            failed_procs.append(i)
            procs[i] = subprocess.Popen(['python', CAPTURE_METHOD_FALLBACK_FILE, ports[i], \
                                         dir+'/camera'+str(i)+'/BACKUP_IMG_00{0:02}'.format(index)], \
                                         stdout=subprocess.PIPE)
    
    # Wait for the re-taking to complete, but with a timeout
    # Credit: https://www.gungorbudak.com/blog/2015/08/30/simple-way-of-pythons-subprocesspopen/
    unfinished_failed_procs = failed_procs[:] # make a copy
    for t in range(REDEMPTION_TIMEOUT * REDEMPTION_POLL_FREQ):
        sleep(REDEMPTION_POLL_INTERVAL)
        for i in unfinished_failed_procs:
            if procs[i].poll() is not None:
                out,err = procs[i].communicate()
                print("Camera #%d's redemption run: "%i + out)
                unfinished_failed_procs.remove(i)
        if len(unfinished_failed_procs) < 1:
            break
    for i in unfinished_failed_procs:
        procs[i].kill()
        print("Camera #{0} still isn't able to capture the image at angle #{1} (or it just didn't want to tell you), so we killed its process after waiting {2} seconds.".format(i, index, REDEMPTION_TIMEOUT))
    
    #for i in failed_procs:
    #    out,err = procs[i].communicate()
    #    print("Camera #%d's redemption run: "%i + out)
        #print("Camera #%d is supposed to finish, but if it's actually not, whatcha gonna do with it?" % i)
    #print("Capture method for the image called '"+name+"' is finished.")
    return failed_procs

# Gets images from each camera, and then rename them
def download_and_rename_files(dir_name_base = '', failed_records = []):
    d_procs = range(num_of_ports)
    for j in range(num_of_ports):
        d_procs[j] = subprocess.Popen(['python', DOWNLOAD_AND_RENAME_ALT_METHOD_FILE, \
                                        ports[j], dir_name_base+str(j), str(j), str(failed_records[j]), str(int(NUM_OF_PICS_PER_SHERD))], \
                                        stdout=subprocess.PIPE)
    # ***find a way to wait for them but still remain parallel here
    # or we should just halt the loop and wait for user input to continue.
    for j in range(num_of_ports):
        d_procs[j].wait()
        #out,err = d_procs[j].communicate() # ??? the right way ???
        #print(out)
    #print("Sherd %d finished" % SHERD_ID)
    print("sherd finished and saved");

# The full cycle for one sherd, including motor control, camera control, and file processing
# (No need to auto-focus because we want to fix the parameters, since the sherd position is fixed)
def one_sherd_photo_cycle(directory):
    global CYCLE_START # long test
    CYCLE_START = time.time() # long test

    d_procs = range(num_of_ports)
    failed_records = []
    for i in range(num_of_ports):
        failed_records.append([])

    # Create a main folder for this sherd, and subfolders for all the cameras.
    # The naming convention would change once we figure out how our client wants it to be.
    # main folder
    shot_date = datetime.now().strftime("%Y-%m-%d")
    
    #directory from app
    folder_name = directory
    
    save_location = IMAGE_STORAGE_BASE_ADDR + folder_name
    createSaveFolderSoftly(IMAGE_STORAGE_BASE_ADDR, folder_name)
    # subfolders
    save_location_subfolder_name_base = save_location+'/camera'
    for j in range(num_of_ports):
        createSaveFolderSoftly(save_location, 'camera'+str(j))
    
    angle_index = 0 # for naming the picture with the correct order (but not useful if not using --capture-image-and-download)
    next_angle_steps = 0 # for keeping track of how many steps are needed to reach the next capture time

    # Each iteration of this loop runs a step of the stepper motor.
    for i in range(FULL_CYCLE_STEPS):
        
        # check if user requested to cancel scan
	global _FINISH, BEGIN_DOWNLOAD; # long test
	if _FINISH:
	    _FINISH = False;
	    break;
        
        # If we have taken enough steps since the previous capture, then stop and take a picture.
        #resetCaptureTarget() # not sure if adding this here helps anything
        if (i >= next_angle_steps):
            
                    
            percentDone = (i*100)//FULL_CYCLE_STEPS
            percentDoneStr = None;
        
            if percentDone == 0:
                percentDoneStr = "000"
            elif percentDone < 10:
                percentDoneStr = "00" + str(percentDone)
            elif percentDone == 100:
                percentDoneStr = str(percentDone)
            else:
                percentDoneStr = "0" + str(percentDone)
            finalStr = percentDoneStr + "% Done"
            print(finalStr)
            conn.send(finalStr.encode())
            
            
            # Wait a little while for vibration stabilization
            sleep(SLEEP_TIME_BETWEEN_SHOTS)
            
            # Take pictures from all cameras
            shot_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") # keep in mind that this naming scheme could change
            file_name = shot_time+"_angle"+str(angle_index)+"_camera"
            #resetCaptureTarget() # Just to make sure it doesn't randomly switch to RAM again # Actually I'm moving this to the capture method directly
            failed_procs = captureImages(save_location, file_name, angle_index)
            for j in failed_procs:
                failed_records[j].append(angle_index)
            resetCaptureTarget() # not sure if adding this here will also help
            #print("Image on sherd #%d finished -- from the main loop" % angle_index)

            # Increment next angle step
            next_angle_steps += AVG_STEPS_PER_SHOT
            angle_index += 1

        if angle_index >= int(NUM_OF_PICS_PER_SHERD):
            # If it turns out that we have already finished the last shot,
            # we can download while returning to the initial holder position.
            # This means disintegrating the download_and_rename_files method, tho.
            conn.send("Downloading Files From Camera...")
            print("Downloading while returning to initial position...")
            BEGIN_DOWNLOAD = time.time() # long test
            for j in range(num_of_ports):
                d_procs[j] = subprocess.Popen(['python', DOWNLOAD_AND_RENAME_ALT_METHOD_FILE, \
                                        ports[j], save_location_subfolder_name_base+str(j), #
                                        str(j), str(failed_records[j]), str(int(NUM_OF_PICS_PER_SHERD))], \
                                        stdout=subprocess.PIPE)
            angle_index = 0
        
        # For each iteration, run one step of motor
        GPIO.output(MD_PUL, 1)
        sleep(DELAY)
        GPIO.output(MD_PUL, 0)
        sleep(DELAY)

    # After a full cycle, start downloading files
    #print("Downloading...")
    for j in range(num_of_ports):
        d_procs[j].wait()
    print("Sherd finished")
    global FINISH_DOWNLOAD, PHOTO_FAILS # long test
    FINISH_DOWNLOAD = time.time() # long test
    with open('/mnt/usb/ENGS90Photos/long_test.csv', mode='a') as long_test: # long test
            test_writer = csv.writer(long_test, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            test_writer.writerow([PHOTO_FAILS, CYCLE_START, BEGIN_DOWNLOAD, FINISH_DOWNLOAD])
    PHOTO_FAILS = 0 # long test
    #download_and_rename_files(save_location_subfolder_name_base, failed_records)


#TCP_IP = '127.0.0.1' #localhost
TCP_IP = ''
TCP_PORT = 5005
#BUFFER_SIZE = 20  # Normally 1024, but we want fast response

killGphoto2Process()
#resetCaptureTarget() # But it seems like the code randomly switches to RAM in the middle, so I moved it into the main loop
ports = findCameraPorts()
num_of_ports = len(ports)
print("Removing all previous files from cameras...")
clearCameraFiles()

global _FINISH;
_FINISH = False;

def doScan(saveDir):
	# TODO: call motor/camera code
	#print("directory:", str);
	one_sherd_photo_cycle(saveDir)
        clearCameraFiles()
    
	print('done')
	conn.send("done".encode());

def stopScan():
	global _FINISH;
	# TODO: call code to interrupt scan
	print("scan stopped");
	_FINISH = True;
	return;


#TCP_IP = '127.0.0.1' #localhost
TCP_IP = ''
TCP_PORT = 5005

#BUFFER_SIZE = 20  # Normally 1024, but we want fast response

#print('test0')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#print('test1')
s.bind((TCP_IP, TCP_PORT))
#print('test2')
s.listen(1)

print('waiting for connections')

conn, addr = s.accept()
print('Connection address:', addr)
time.sleep(1)
conn.send("Connected!".encode());

print("Sleep go connect drive")
sleep(10)
print("I'm waking up")

if mountDrive() == True:
    IMAGE_STORAGE_BASE_ADDR = "/mnt/usb/ENGS90Photos/"

while 1:
	data = conn.recv(1024)
	if (not data):
		break;
	print("received data:", data)
	input = data.decode('UTF-8','strict');
	print("data as string=", input)
	if(input == "cancel"):
		stopScan();
	else:
		scan = threading.Thread(target=doScan, args=(input,)).start();
	# conn.send(data)  # echo
conn.close()
GPIO.cleanup()
