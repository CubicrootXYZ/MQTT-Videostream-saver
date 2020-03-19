import numpy as np
import cv2, shutil
import os, time
from datetime import datetime
from datetime import timedelta
import os.path
from os import path
import paho.mqtt.client as mqtt
from telethon import TelegramClient
import _thread as thread


# Video class handles the videostream
#   uri: uri where the stream is located
#   folder: folder where the files are saved to, make sure to have a final /
#   extended_structure: enables folder structure with year -> month -> day
class Video: 
    def __init__(self, uri, folder, alert_text="❌ Motion detected", extended_structure=True):
        self.uri = uri
        self.folder = str(folder)
        self.ex_struc = extended_structure
        self.current_file = ""
        self.alertActive = False
        self.lock = thread.allocate_lock()
        self.recording = False
        self.alert_text = alert_text
    
    # Makes sure that the folders are ready and there is no same file
    #   returns: full path to the file 
    def prepareFile(self):
        now = datetime.now()
        current_file = now.strftime("%Y-%m-%d_%H-%M-%S")+".mp4"

        # make sure the folders are there for the extended structure
        if self.ex_struc == True: 
            year = now.strftime("%Y")
            month = now.strftime("%m")
            day = now.strftime("%d")
            full_path = self.folder+year+"/"+month+"/"+day
            if path.exists(full_path):
                 if os.path.isfile(full_path+current_file):
                    try:
                        os.remove(full_path+current_file)
                    except Exception as e:
                        print(e)
                        return False
            else:
                try:
                    os.makedirs(full_path)
                except Exception as e:
                        print(e)
                        return False
        # make sure there is no same file
        else: 
            if os.path.isfile(self.folder+current_file):
                try:
                    os.remove(self.folder+current_file)
                except Exception as e: 
                    print(e)
                    return False
            full_path = self.folder

        return full_path+"/"+current_file

    # Starts recording a video, stops after given time, also alerts
    #   time: time in seconds to record
    def startRecordingTime(self, time):
        try:
            cap = cv2.VideoCapture(self.uri)
        except Exception as e:
            print(e)
            return False

        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) 
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        file_path = self.prepareFile()
        if file_path != False:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            try:
                out = cv2.VideoWriter(file_path,fourcc, 20.0, (int(width),int(height)))
            except Exception as e:
                print(e) 
            time_now = datetime.now()
            frames = 0
            sendAlert = 0
            while(cap.isOpened()):
                frames+=1
                ret, frame = cap.read()
                if frames%20 == 0:
                    delta = (datetime.now()-time_now)/timedelta(seconds=1)
                    print(delta)
                    if  delta >= int(time):
                        #send alert image if not already done and end writing video file
                        if sendAlert == 0:
                            name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".jpg"
                            cv2.imwrite("/tmp/"+name, frame) 
                            sendAlert = 1
                            try:
                                self.alert.send(self.alert_text, open("/tmp/"+name, 'rb'))
                                os.remove("/tmp/"+name)
                            except Exception as e:
                                print(e)
                        break
               
                # Send alert image after 3 seconds
                if frames == 60 and self.alertActive == True and sendAlert == 0:
                    name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".jpg"
                    cv2.imwrite("/tmp/"+name, frame) 
                    sendAlert = 1
                    try:
                        self.alert.send(self.alert_text, open("/tmp/"+name, 'rb'))
                        os.remove("/tmp/"+name)
                    except Exception as e:
                        print(e)
                    

                if ret == True:
                    #frame = cv2.flip(frame,1)
                    out.write(frame)
                else:
                    print("Failure in writing")
                    break
        else:
            return False

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        thread.start_new_thread(self.cleanUp, ())
        return file_path
    
    # Starts recording until it is stopped manually, also alerts
    def startRecordingManually(self):
        if self.lock.locked():
            self.lock.release()
        if self.recording == False:
            try:
                thread.start_new_thread(self.startRecordingManuallyRec, ())
                self.recording = True
            except Exception as e:
                print(e)
                return False
        return True

    # Extra method for recording for multithreading
    def startRecordingManuallyRec(self):
        try:
            cap = cv2.VideoCapture(self.uri)
        except Exception as e:
            print(e)
            return False

        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) 
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        file_path = self.prepareFile()
        if file_path != False:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            try:
                out = cv2.VideoWriter(file_path,fourcc, 20.0, (int(width),int(height)))
            except Exception as e:
                print(e) 
            time_now = datetime.now()
            frames = 0
            sendAlert = 0
            while(cap.isOpened()):
                frames+=1
                ret, frame = cap.read()

                # Stop recording if lock is locked
                if  self.lock.locked():
                    #send alert image if not already done and end writing video file
                    if sendAlert == 0:
                            name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".jpg"
                            cv2.imwrite("/tmp/"+name, frame) 
                            sendAlert = 1
                            try:
                                self.alert.send("Alert", open("/tmp/"+name, 'rb'))
                                os.remove("/tmp/"+name)
                            except Exception as e:
                                print(e)
                    break
               
                # Send alert image after 3 seconds
                if frames == 60 and self.alertActive == True and sendAlert == 0:
                    name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".jpg"
                    cv2.imwrite("/tmp/"+name, frame) 
                    sendAlert = 1
                    try:
                        self.alert.send("Alert", open("/tmp/"+name, 'rb'))
                        os.remove("/tmp/"+name)
                    except Exception as e:
                        print(e)
                    

                if ret == True:
                    #frame = cv2.flip(frame,1)
                    out.write(frame)
                else:
                    print("Failure in writing")
                    break

                if frames > 100000:
                    break
        else:
            return False

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        self.lock.release()
        return file_path

    # Stops a manual recording
    def stopRecordingManually(self):
        self.lock.acquire()
        self.recording = False
        thread.start_new_thread(self.cleanUp, ())
    
    # Set an alert
    #   alert: alert class
    def setAlert(self, alert):
        self.alertActive = True
        self.alert = alert

    def cleanUp(self):
        days=180
        critical_time = datetime.now()-timedelta(days=days)
        super_critical_time = critical_time-timedelta(days=32)
        year=super_critical_time.strftime("%Y")
        month = super_critical_time.strftime("%m")
        i = 0
        while i < 12:
            time = super_critical_time-timedelta(i*365/12)
            month = time.strftime("%m")
            try:
                shutil.rmtree(self.folder+str(year)+"/"+month)
            except Exception as e:
                print(e)
            i+=1


# Telegram alert class
#   api_id:
#   api_hash:
#   bot_hash: data for connection to Telegram API
class TelegramAlert:
    def __init__(self, api_id, api_hash, bot_hash, user):
        self.bot = TelegramClient('bot', api_id, api_hash)
        self.bot_hash = bot_hash
        self.user = user
    
    # Send an message and image to Telegram
    #   message: text message
    #   img: image file (open(file, 'rb'))
    def send(self, message, img):
        self.bot.start(bot_token=self.bot_hash)
        self.bot.loop.run_until_complete(self.sendmsg(message, img))

    # Actual sending method due to async operation
    async def sendmsg(self, msg, img):
        await self.bot.send_message(self.user, msg, file=img)
        
# MQTT Handler
#   server: MQTT Server adress
#   port: MQTT server port
#   channel: top channel to listen to, please use sth like devices/cam1/#
#   video: video class for handling video stream
#   alert: alert class for handling alerts
class MQTTHandler():
    def __init__(self, server, port, channel, video, alert):
        self.channel=channel
        self.video=video
        self.video.setAlert(alert)
        self.client = mqtt.Client()
        self.client.on_connect=self.on_connect
        self.client.on_message=self.on_message
        self.client.connect(server, port, 60)
        self.client.loop_forever()  
        self.alert_active = True
    
    def on_connect(self, mqttc, obj, flags, rc):
        print("Connected with result code " + str(rc))
        self.client.subscribe(self.channel, 0)
        print(self.channel)

    def on_message(self, mqttc, obj, msg):
        if "timed" in msg.topic and self.alert_active == True:
            print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
            try:
                self.video.startRecordingTime(str(msg.payload, 'utf-8'))
            except Exception as e:
                print(e)
        elif "startrecording" in msg.topic and self.alert_active == True:
            try:
                self.video.startRecordingManually()
            except Exception as e:
                print(e)
        elif "stoprecording" in msg.topic:
            try:
                self.video.stopRecordingManually()
            except Exception as e:
                print(e)
        else:
            print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

        if "active" in msg.topic:
            if str(msg.payload, 'utf-8') in ["active", "true", "on", "activate"]:
                self.alert_active = True
            elif str(msg.payload, 'utf-8') in ["deactivate", "off", "false", "deactive"]:
                self.alert_active = False
                print("Deactive")


video = Video("Videostream URI", "absolute path to save directory", alert_text="❌ Motion detected")
alert= TelegramAlert(APIID, "api_hash", "bot_hash", "username")
run = MQTTHandler("MQTT IP", MQTT_PORT, "mqtt_channel_to_listen/#", video, alert)