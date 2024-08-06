#jarvis code
import sys
import speech_recognition as sr
import pyttsx3 # provide engine that convert text to voice
import datetime
import os
import webbrowser
import  cv2
from requests import get
import socket
import wikipedia
import pywhatkit as k#this library for sending the whatsapp
import pyautogui#this library is used for the volume up and down or mute
import requests
import sys
from clap import mainclap

mainclap()
engine=pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
print(voices[0].id)
engine.setProperty('voices',voices[0].id)

def speak(audio):#text to speech    
    engine.say(audio)
    print(audio)
    engine.runAndWait()

def takecommand(): #to convert voice to text
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold=1 #pause for few second
        audio = r.listen(source)
    try:
        print("Recognization")
        query =r.recognize_google(audio,language='hn-in')
        print(f"user said:{query}")
    except Exception as e:
        speak("say that again please...")
        return "none"
    return query
def wish():
    hour = int (datetime.datetime.now().hour) #exit time

    if hour>=0 and hour<=12:
        speak("good morning karan sir")
    elif hour>=12 and hour<=15:
        speak("good afternoon karan sir")
    elif hour>=15 & hour<=19:
        speak("good Evening")
    elif hour>=19 and hour<=24:
        print("good night , sir")
    else:
        speak("good night sir")
    speak("I am jarvis sir . please tell me how can i help you ")


def get_ip_address(hostname):
    try:
        ip_ad= socket.gethostbyname(hostname)#return gethostbyname is a function that return the ip Address of any website
        return ip_ad# return the ip address of the website
    except socket.error as e :
        print(f"Error{e}")
        return None
def jarvis():

    while True:
        # if 1:
        query = takecommand().lower()
        # logic building for task
        if 'open desktop' in query:
            npath = "C:\\Users\\karan\\OneDrive\\Desktop"
            os.startfile(npath)
            speak("opening desktop sir ")
        elif 'open youtube' in query:
            spath = "https://www.youtube.com/"
            webbrowser.open(spath)
            speak("opening youtube sir... ")
        elif 'open word' in query:
            qpath = "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Word"
            os.startfile(qpath)
            # speak("sir do you want to write anything in word")
            # a=takecommand().lower()
            # if "write" in a :
            #     speak("sir what I write Please give me lines")
            #     b=takecommand().lower()
            #     pyautogui.write(b)
        elif 'open command prompt' in query:
            os.system("start cmd")
            speak("opening the command prompt...")
        elif 'open camera' in query:
            cap = cv2.VideoCapture(0)  # 0 is for internal camera and 1 for outer camera
            while True:
                ret, frame = cap.read()  # read a frame from camera
                cv2.imshow('camera', frame)  # display the frame
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()
            speak("opening the cammera sir ...")
        elif 'ip address' in query:
            speak("Sir do you want to write the website or want to give by voice")
            q = takecommand().lower()
            if "write" in q:
                ip = input("enter the webestie ")
                p = get_ip_address(ip)
                speak(p)
                print(p)
            elif "voice" in q:
                z = takecommand().lower()
                c = get_ip_address(z)
                speak(c)
            else:
                pass
        elif 'wikipedia' in query:
            a = takecommand()
            speak('according to wikipedia ')
            result = wikipedia.summary(a, sentences=3)
            speak(result)
            speak("done")
        elif 'open google' in query:
            speak("sir what Would I search on google")  # searches the question that user has said
            cm = takecommand().lower()
            webbrowser.open(f"{cm}")
            speak("done")

        elif 'send message' in query:
            speak("Please give the Appropriate number")
            n = input("enter a number")
            speak(n)
            speak("Please write the message that you want to send")
            message = input("enter the mesage ")
            ct = datetime.datetime.now()
            h = ct.hour
            m = ct.minute + 1
            k.sendwhatmsg(n, message, h, m)
            speak("done sir ")
        elif 'play song on youtube' in query:
            Y = takecommand().lower()
            print(Y)
            k.playonyt(Y)
            speak("done sir ")


        elif 'volume up' in query:
            pyautogui.press("volumeup")
        elif 'volume down' in query:
            pyautogui.press("volumedown")
        elif 'volumemute' in query or 'mute' in query:
            pyautogui.press("volumemute")
        elif 'no thanks' or 'no '  in query:
            speak("thank you for using me, have a good day")
            sys.exit()

        speak("sir do you have any other work ")

if __name__=='__main__':
    #speak("Hello , This is the AI version ")
    #takecommand()
    wish()
    jarvis()
