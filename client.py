import cv2
import numpy as np
import argparse
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import socket
import struct
import pickle
from threading import Thread
import copy
import csv
import sys
import requests
from datetime import datetime
import math

coordinateX=0
coordinateY=0
frameCounter=0
frameSender=0

class configureAWS:
	host = 'AWS-endpoint'
	rootCAPath = 'root-ca-cert.pem'
	certificatePath = 'd8721de362.cert.pem' #<----------Change hashcode here
	privateKeyPath = 'd8721de362.private.key'  #<----------Change hashcode here
	clientId = 'Subscriber'  #<----------Change subscriber device name here
	topic_rover = 'iot/rover'  #<----------Change topic name here
	useWebsocket = False
				
	def __init__(self):
		pass

	def get_aws_host(self):
		return self.host
	def set_aws_host(self, aws_host):
		self.host = aws_host	
		
	def get_root_file(self):
		return self.rootCAPath
	def set_root_file(self, root_file_path):
		self.rootCAPath = root_file_path
		
	def get_cert_file(self):
		return self.certificatePath
	def set_cert_file(self, cert_file_path):
		self.certificatePath = cert_file_path

	def get_priv_file(self):
		return self.privateKeyPath
	def set_priv_file(self, priv_file_path):
		self.privateKeyPath = priv_file_path		
		
	def get_thing_name(self):
		return self.clientId 
	def set_thing_name(self, thing_name):
		self.clientId = thing_name

	def get_topic(self, keyword):
		if keyword=="rover":
			return self.topic_rover
		if keyword=="target":
			return self.topic_target
		else:
			return 'default/topic'
	def set_topic(self, keyword):
		if keyword=="rover":
			self.topic_rover = keyword
		if keyword=="target":
			self.topic_target= keyword
	
def customCallback(client, userdata, message):
    global frameCounter
    frameCounter=frameCounter+1
    global frameSender
    frameSender=frameSender+1
    url = 'http://localhost:4567/rest/latency'
    payload = json.dumps({
        "step": "4",
        "frame": str(frameCounter),
        "timestamp": str(datetime.now().time())
    })
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    payload=json.loads(message.payload)
    coordinates=list(payload['rover'].split(','))
    coordinates[0]=coordinates[0].replace('(','')
    coordinates[1]=coordinates[1].replace(')','')
    global coordinateX
    coordinateX=int(coordinates[0])
    print('Coordinate X changed to: {}'.format(coordinateX))
    global coordinateY
    coordinateY=int(coordinates[1])
    print('Coordinate Y changed to: {}'.format(coordinateY))

def connect_aws():

	useWebsocket=False
	if useWebsocket and certificatePath and privateKeyPath:
		print("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
		exit(2)

	if not useWebsocket and (not certificatePath or not privateKeyPath):
		print("Missing credentials for authentication.")
		exit(2)

# Port defaults
	if useWebsocket:  # When no port override for WebSocket, default to 443
		port = 443
	if not useWebsocket:  # When no port override for non-WebSocket, default to 8883
		port = 8883	
	
	
	myAWSIoTMQTTClient = None
	if useWebsocket:
		myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
		myAWSIoTMQTTClient.configureEndpoint(host, port)
		myAWSIoTMQTTClient.configureCredentials(rootCAPath)
	else:
		myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
		myAWSIoTMQTTClient.configureEndpoint(host, port)
		myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

	# AWSIoTMQTTClient connection configuration
	myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
	myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
	myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
	myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
	myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
	#myAWSIoTMQTTClient.onMessage=messageHandler
# Connect and subscribe to AWS IoT
	myAWSIoTMQTTClient.connect()
	return myAWSIoTMQTTClient
					 
def awsSub_mode1():

    global myAWSConfig
    global host
    global rootCAPath
    global certificatePath
    global privateKeyPath
    global clientId
    global topic_rover
    global useWebsocket
    global frame
    #newFrame = None
    myAWSConfig=configureAWS()
    host = myAWSConfig.get_aws_host()
    rootCAPath = myAWSConfig.get_root_file()
    certificatePath = myAWSConfig.get_cert_file()
    privateKeyPath = myAWSConfig.get_priv_file()
    clientId = myAWSConfig.get_thing_name()
    topic_rover = myAWSConfig.get_topic("rover")
    useWebsocket=myAWSConfig.useWebsocket

    co = []
    with open('coordinates2.csv') as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        for row in csvReader:
            if len(row)>0:
                co.append(row)
    i=0
    j=0
    sumX=0
    sumY=0
    distance=0
    print("CO LENGTH "+str(len(co)))
    myAWSIoTMQTTClient=connect_aws()
    myAWSIoTMQTTClient.subscribe(topic_rover, 1, customCallback)	
    print("subscribed")
    cap = cv2.VideoCapture('crawler.mp4')
    oldFrame = None
    backUpFrame = None
    last=False
    differenceList=[]
    while(True):
        if last==False:
            ret,frame=cap.read()
            if (coordinateX != 0) & (coordinateY!=0):
                difference=int(math.sqrt(pow((int(co[i][0])-coordinateX),2)+pow((int(co[i][1])-coordinateY),2)))
                distance=distance+difference
                differenceList.append(difference)
            if oldFrame is not None and frame is None:
                last=True
            else:
                oldFrame=copy.copy(frame)
                backUpFrame=copy.copy(frame)
            cv2.circle(frame, (coordinateX,coordinateY),10,(255,0,0), -1)
            if frame is not None:
                cv2.imshow("Video", frame)
                i=i+1
                j=j+1
                if i>=len(co):
                    i=len(co)-1
        else:
            difference=int(math.sqrt(pow((int(co[i][0])-coordinateX),2)+pow((int(co[i][1])-coordinateY),2)))
            distance=distance+difference
            differenceList.append(difference)
            j=j+1
            if (int(co[i][0])-coordinateX)==0 & (int(co[i][1])-coordinateY)==0:
                break
            oldFrame=copy.copy(backUpFrame)
            cv2.circle(oldFrame, (coordinateX,coordinateY),10,(255,0,0), -1)
            cv2.imshow("Video", oldFrame)
        if i==(len(co)-1) & int(co[i][0])==coordinateX:
            break
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    print('DISTANCE: '+str(int(distance)))
    npArray = np.array(differenceList) 
    np.savetxt('distances.csv', [npArray], delimiter='\n', fmt='%d') 
    cap.release()
    cv2.destroyAllWindows()
    sys.exit()

def awsSub_mode2(width, height, target):

    global myAWSConfig
    global host
    global rootCAPath
    global certificatePath
    global privateKeyPath
    global clientId
    global topic_rover
    global useWebsocket
    global frame
    #newFrame = None
    myAWSConfig=configureAWS()
    host = myAWSConfig.get_aws_host()
    rootCAPath = myAWSConfig.get_root_file()
    certificatePath = myAWSConfig.get_cert_file()
    privateKeyPath = myAWSConfig.get_priv_file()
    clientId = myAWSConfig.get_thing_name()
    topic_rover = myAWSConfig.get_topic("rover")
    useWebsocket=myAWSConfig.useWebsocket

    url = 'http://localhost:4567/rest/latency'
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((target, 8022))
    connection = client_socket.makefile('wb')
    
    img_counter = 0
    frame_counter = 0
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    cap = cv2.VideoCapture('crawler.mp4')
    cap.set(3, (320/ int(width)));
    cap.set(4, (240/ int(height)));

    co = []
    with open('coordinates2.csv') as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        for row in csvReader:
            if len(row)>0:
                co.append(row)
    i=0
    j=0
    distance=0
    oldSender=-1
    myAWSIoTMQTTClient=connect_aws()
    myAWSIoTMQTTClient.subscribe(topic_rover, 1, customCallback)	
    print("subscribed")
    oldFrame = None
    backUpFrame = None
    last=False
    differenceList=[]
    oldX=-1
    oldY=-1
    while(True):
        print('X: {}'.format(coordinateX))
        print('Y: {}'.format(coordinateY))
        ret,frame=cap.read()
        if (coordinateX != 0) & (coordinateY!=0):
            difference=int(math.sqrt(pow((int(co[i][0])-coordinateX),2)+pow((int(co[i][1])-coordinateY),2)))
            distance=distance+difference
            differenceList.append(difference)
        cv2.circle(frame, (coordinateX,coordinateY),10,(255,0,0), -1)
        if frame is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            result, gray = cv2.imencode('.jpg', gray, encode_param)
            data = pickle.dumps(gray, 0)
            size = len(data)

            payload = json.dumps({
                "step": "1",
                "frame": str(i), 
                "timestamp": str(datetime.now().time())
            })
            headers = {'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload)
            #if (oldX != coordinateX) | (oldY != coordinateY):
            if oldSender != frameSender :
                client_socket.sendall(struct.pack(">L", size) + data)
                oldSender=copy.copy(frameSender)
                print('SENT FRAME NR: {}'.format(i))
            cv2.imshow("Video", frame)
            i=i+1
            j=j+1
            if i>=len(co):
                i=len(co)-1
        else:
            print('HERE IN ELSE')
            break
        if i==(len(co)-1) & int(co[i][0])==coordinateX:
            print('HERE IN if break')
            break
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    
    npArray = np.array(differenceList) 
    np.savetxt('distances.csv', [npArray], delimiter='\n', fmt='%d')  
    cap.release()
    cv2.destroyAllWindows()
    sys.exit()

def client(skip, width, height, target):

    
    url = 'http://localhost:4567/rest/latency'
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((target, 8022))
    #client_socket.connect(('192.168.0.50', 8022))
    #client_socket.connect(('192.168.2.108', 8022))
    #client_socket.connect(('3.66.170.243', 8022))
    connection = client_socket.makefile('wb')

    cam = cv2.VideoCapture('crawler.mp4')
    cam.set(3, (320/ int(width)));
    cam.set(4, (240/ int(height)));
    img_counter = 0
    frame_counter = 0
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    while True:
        ret, frame = cam.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_counter=frame_counter+1
        if frame_counter%int(skip) == 0:
            continue
        if frame is None:
            break
        result, frame = cv2.imencode('.jpg', frame, encode_param)
        data = pickle.dumps(frame, 0)
        size = len(data)

        payload = json.dumps({
            "step": "1",
            "frame": str(frame_counter), 
            "timestamp": str(datetime.now().time())
        })
        headers = {'Content-Type': 'application/json'}
        
        response = requests.request("POST", url, headers=headers, data=payload)
        client_socket.sendall(struct.pack(">L", size) + data)
        #step="1 - {}".format(frame_counter)
        
        #print(response.text)
        img_counter += 1

    cam.release()
    print('TASK 1 ENDING')
    sys.exit()
    print('TASK 1 ENDED')
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--skip", default=10000,required=False,help="skip every n-th frame")
    ap.add_argument("-m", "--mode", default=1,required=True,help="mode of sending video frames")
    ap.add_argument("-w", "--width", default=1,required=False,help="decrease width of frame n times")
    ap.add_argument("-hg", "--height", default=1,required=False,help="decrease height of frame n times")		
    ap.add_argument("-t", "--target", default="",required=True,help="ip address of target machine")		
		
		
    args = vars(ap.parse_args())
    skip = args["skip"]
    width = args["width"]
    height = args["height"]
    target = args["target"]	
    mode = args["mode"]
    
    if int(mode)==1:
        sendVideo=Thread(target=client,args=(skip,width,height,target))
        sendVideo.start()

        receiveCoordinates=Thread(target=awsSub_mode1)
        receiveCoordinates.start()
    elif int(mode)==2:
        sendVideo=Thread(target=awsSub_mode2,args=(width,height,target))
        sendVideo.start()
    

