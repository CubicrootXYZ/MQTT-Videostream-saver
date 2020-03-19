# MQTT Videostream saver

This is a simple Python script to save a videostream to a file when a MQTT channel is triggered. It also alerts you on Telegram with a picture attached.

## Installation

Install Python3 and all the needed packages. 

Copy the script, change the settings at the bottom. 

Run it. 

## Settings

You need to add Telegram credentials, your Videostream URI, a save path and MQTT stuff to the script. 

__Please always use a `/#` at the end of the MQTT channel, else it will NOT subscribe into all subchannels and will not work.__

MQTT Subchannels used: 

* `timed` send a integer here and the programm will start recording for that amount of seconds.
* `startrecording` send anything here and the programm will start recording.
* `stoprecording` send anything here and the programm will stop recording.
* `active` send active, true, on, activate here to activate the script or deactivate, off, false, deactive to stop it.