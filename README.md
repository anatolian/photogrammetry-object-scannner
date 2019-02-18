# ScannerApp

Created for the very-specific purpose of communicating via android with a raspberry pi running a scanner. The code to run the scanner is provided in the "pottery8990" repository. "theApp" repository includes only the android-side code, and the server code (server.py) that is on the pi, and does not include any other code from the scanner, such as the code controlling the cameras or motors. 

## Importing to Android Studio

Create new project with the name "ScannerApp" and min sdk 15. Call the main activity "MainActivity". Then copy files from this repo into the created project.

## Installing and Running apk on the Android

The app isn't on the google play store at the moment. To debug the app, put the android phone/tablet in developer mode, and run from android studio. This will open the app. 

Alternatively, to download the app without android studio, you can do the following:
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

No non-default libraries are used for this portion of the pi code, so no imports are necessary before use.

## How to Connect

* run server.py
* enter server address and port into the specified textboxes on the android app, and hit "connect" button
  * pi address can be found by googling "my ip address" and probably in the computer properties somewhere.
  * port number is 5005
* if connect is successful, input information about sherd for the scan, and press "start scan"

## Troubleshooting

The raspberry pi and android phone must be connected to the internet via the same router. This means they must be connected to the same wifi network, and, if it is a large network with multiple routers, they must be on the same router. A phone hotspot can also be used as a router should no other small networks be available

A good way to check if they are on the same router is to check that the first few sections of the IP address are the same (If the IP address is 127.0.0.1 or something similar, you are looking at your local IP address, which is not the correct IP address for this check. To find your non-local IP, it can be found in your computer's settings, or simply by googling "what is my IP address")

Also, for unknown reasons, the app was not able to connect to the server for about two days, despite the fact that none of the code had changed since the last time it worked. After that though, the code started working again, despite nothing being changed during the debugging process over those past two days. The reason for this bug is unknown and has caused quite a bit of frustration for the developer, but hopefully the cause and/or solution will be discovered soon. It has nothing to do with the code though, since that didn't change.


## Features Implemented

### Client-Side
* connect to device running server.py via android phone running ScannerApp.apk
* enter various information about the sherd, and use that information to determine what directory location to send to the scanner as string that can be used by command line/etc.
* shows all messages it receives as toast, for debug purposes
* "start scan" button becomes "cancel scan" button when scan is in progress, and reverts back to a "start scan" button upon scan completion
* "start scan" button is disabled until the app connects to the server or an error is thrown.
* user may begin inputting information for next sherd while current scan is taking place
* save most recent inputs from edittexts/etc, and prepopulate these fields with these values upon opening app, so that user does not have to re-enter information that will not change often

### Server-Side
* prints all messages it receives, for debug purposes
* upon "start scan" command, server starts a new thread to run the scanner code in.
* sends message to app upon completion of scan
* listens for a "cancel" command from the phone, quickly ending scan if requested. 
* NOTE: For now, the "scanner" thread merely runs a counter, but hopefully the scanner code is easy to integrate

## TO DO:

### Client-Side
* allow user to input size of the sherd, and send this information to the server along with the directory
* more thorough validation of inputs
* estimated progress bar for current scan?

### Server-Side
* parse the slightly more complicated messages that the client-side TODO items would require
* integrate with the rest of the pi's scanner code
* give pi a constant address (or at least some way to determine its address without a monitor/keyboard/etc)