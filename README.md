# ScannerApp

Created for the very-specific purpose of communicating via android with a raspberry pi running a scanner. "theApp" repository includes the android-side code, and the server code (server_cam_long_test.py) for the pi, and the code to automatically run the agisoft software on a model (agisoft-automation.py). 

To test the server without running the cameras or motor, use server.py instead of server_cam_long_test.py.

Also note, due to time constraints, and the need to shift focus onto the app development, the team was unable to produce a background removal code which would work well in all cases. It works in many cases, but in particular, it fairs worse with pots which are similar in color to the white or black on the checkerboard. However, in these cases, the team was able to manually remove the background successfully. 

So, if the user finds a model where the background removal produces undesirable results, please run agisoft-pre-bg-removal.py, manually remove the background as desired, then run agisoft-post-bg-removal.py.

## Updates 6/21/2019

Bug fixes that will hopefully correct the NetworkOnMainThreadException

There are now three versions of the .apk:

* app-debug-old.apk : this is a backup of the .apk file from the previous update. This version threw the NetworkOnMainThreadException.
* app-debug-rebuilt.apk : all of the code is the same as the previous update, but the apk was rebuilt. This version of the apk has been included because it is possible that during development, the code was pushed but the updated .apk file was not.
* app-debug-new.apk : this .apk implements new code, using the suggestions from http://simpledeveloper.com/network-on-main-thread-error-solution/ 

Jess recommends first downloading the app-debug-rebuilt.apk (see "Installing and Running apk on the Android" for instructions), and seeing if this version fixes the NetworkOnMainThreadException error. If it does not, then try the app-debug-new.apk

Since Jess doesn't have an android device or pi while she is off-campus, she could not test any of these builds on her own device before pushing. So if problems persist, please send logs to her.

## Importing to Android Studio

Create new project with the name "ScannerApp" and min sdk 15. Call the main activity "MainActivity". Then copy files from this repo into the created project.

## Installing and Running apk on the Android

### With Android Studio (aka read this section if you are developing)

* Build the app in android studio, using the instructions above. 
* Ensure your device is in developer mode. 
* Connect your device via usb. 
* Press "run" in android studio. 
* Select your device from the list of devices. If your device is not there, check the device to ensure you've entrusted this computer on the device.

### Without Android Studio, on a Phone Which Has Already Run the Most Recent Version of the App (aka read this section if you are Joe, Julia, Zoe, or Fan)

Search for "ScannerApp" in the google search bar. Most recent version of the app will show up there.

### Without Android Studio on a New Device

* download the app-debug.apk from the repo to your computer
* allow 3rd party apps to run on the device (an option in "Security" tab of "Settings")
* get a file manager for the phone, so that the .apk can be accessed
* when connecting the android phone to the computer with the .apk, go to android notifications (swipe down from top of screen)
* select the notification that says "USB Charging Only", then choose to use USB to "Transfer Files"
* you will now be able to see the contents of the android phone on the computer. Drag and drop the apk from the computer to the android (I typically move it to the "Downloads" folder
* search for "app-debug.apk" in the file explorer, and choose to install it. If you get a warning about trusting the app, choose to trust it

## Installing and Running server.py on Pi (or other computer)

You must have python installed on the pi.
From the command, run "python.exe <path_to_server.py>"

No non-default libraries are used for server portion of the pi code, so no imports are necessary before use. For imports necessary to run motor and camera, consult the documentation for those portions of the code.

## How to Connect

* run server.py
* enter server address and port into the specified textboxes on the android app, and hit "connect" button
  * pi address can be found by googling "my ip address" and probably in the computer properties somewhere.
  * port number is 5005
* if connect is successful, input information about sherd for the scan, and press "start scan"

## How to run the agisoft code

* Open the pro version of Agisoft photoscan (otherwise, the files cannot be saved)
* Import photos of sherd to be modeled
* Select "Tools" -> "Run script", and then select the python script to run
* Save project when the script is complete

## Troubleshooting

The raspberry pi and android phone must be connected to the internet via the same router. This means they must be connected to the same wifi network, and, if it is a large network with multiple routers, they must be on the same router. A phone hotspot can also be used as a router should no other small networks be available

A good way to check if they are on the same router is to check that the first few sections of the IP address are the same (If the IP address is 127.0.0.1 or something similar, you are looking at your local IP address, which is not the correct IP address for this check. To find your non-local IP, it can be found in your computer's settings, or simply by googling "what is my IP address")


Client-side:

EHOSTUNREACH - this is a network issue. The solution to this problem is still not quite understood, but in the past, restarting either the pi or the phone until a connection can be made has worked.

TIMEOUT - either the server isn't running, or the IP address was inputted incorrectly

ECONNRESET - server on the pi was closed while the phone was still connected


Server-side:

socket error - address already in use - we have observed this error message when restarting the server immediately after it was closed. Waiting a few minutes before attempting to restart the server again fixes the issue


## Features Implemented

### Client-Side
* connect to device running server.py via android phone running ScannerApp.apk
* enter various information about the sherd, and use that information to determine what directory location to send to the scanner as string that can be used by command line/etc.
* shows all messages it receives as toast, for debug purposes
* "start scan" button becomes "cancel scan" button when scan is in progress, and reverts back to a "start scan" button upon scan completion
* "start scan" button is disabled until the app connects to the server or an error is thrown.
* user may begin inputting information for next sherd while current scan is taking place
* save most recent inputs from edittexts/etc, and prepopulate these fields with these values upon opening app, so that user does not have to re-enter information that will not change often
* progress bar for current scan

### Server-Side
* prints all messages it receives, for debug purposes
* upon "start scan" command, server starts a new thread to run the scanner code in.
* sends message to app upon completion of scan
* listens for a "cancel" command from the phone, quickly ending scan if requested. 
* integrate with the rest of the pi's scanner code

## TO DO:

### Client-Side
* allow user to input size of the sherd, and send this information to the server along with the directory
* more thorough validation of inputs

### Server-Side
* parse the slightly more complicated messages that the client-side TODO items would require
* give pi a constant address (or at least some way to determine its address without a monitor/keyboard/etc)