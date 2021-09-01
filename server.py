import cv2
import numpy as np
import cv2.aruco as aruco
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import socket
import pickle
import struct ## new
import requests
from datetime import datetime

class configureAWS:
	host = 'AWS-endpoint'  #<------Change AWS Endpoint value here
	rootCAPath = 'root-ca-cert.pem'
	certificatePath = '24cca14936.cert.pem'  #<----------Change hashcode here
	privateKeyPath = '24cca14936.private.key'  #<----------Change hashcode here
	clientId = 'Publisher' #<----------Change publisher device name here
	topic_rover = 'iotEdge/rover'   #<----------Change topic name here
	useWebsocket=False


					
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
		else:
			return 'default/topic'
	def set_topic(self, keyword):
		if keyword=="rover":
			self.topic_rover = keyword


myAWSConfig=configureAWS()
host = myAWSConfig.get_aws_host()
rootCAPath = myAWSConfig.get_root_file()
certificatePath = myAWSConfig.get_cert_file()
privateKeyPath = myAWSConfig.get_priv_file()
clientId = myAWSConfig.get_thing_name()
topic_rover = myAWSConfig.get_topic("rover")
useWebsocket=myAWSConfig.useWebsocket

def connect_aws():

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

	# Connect and subscribe to AWS IoT
	myAWSIoTMQTTClient.connect()
	return myAWSIoTMQTTClient
					
myAWSIoTMQTTClient=connect_aws()

qrCodeDetector = cv2.QRCodeDetector()
HOST=''
PORT=8022

url="http://192.168.2.103:4567/rest/latency"

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

s.bind((HOST,PORT))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn,addr=s.accept()
frameCounter=0
data = b""
payload_size = struct.calcsize(">L")
print("payload_size: {}".format(payload_size))
oldCenters=0
while(True):
    done = False
    ddd=0
    frameCounter=frameCounter+1
    while len(data) < payload_size:
        print("Recv: {}".format(len(data)))
        data += conn.recv(4096)
        if(len(data)<1):
            print('No more data')
            ddd=ddd+1
            break
    if(ddd==3):
        print('Should be done')
        #mes_rover=json.dumps({'rover': '{}'.format((-1,-1))})
        #myAWSIoTMQTTClient.publish(topic_rover, mes_rover, 1)
        break
    payload=json.dumps({
        'step':'2',
        'frame': str(frameCounter),
        'timestamp':str(datetime.now().time())
    })
    headers={'Content-Type':'application/json'}
    response=requests.request('POST',url,headers=headers,data=payload)
    print(response)
    print("Done Recv: {}".format(len(data)))
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    print("msg_size: {}".format(msg_size))
    while len(data) < msg_size:
        data += conn.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]

    frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
    gray = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Decoding the frame for QR Code data
    # Detect the Aruco Markers
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    parameters = aruco.DetectorParameters_create()
    parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX

    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray,
                                                          aruco_dict, parameters=parameters
                                                          )
    centers = list()
    # Calculate the centers
    for marker_corners in corners:
        #print('Marker Corners -> {}'.format(marker_corners[0]))
        #print('Marker Center -> {}'.format(np.mean(marker_corners[0],axis=0).tolist()))
        centers.append(np.mean(marker_corners[0],axis=0).tolist())

    #print('Centers {}'.format(centers))
    if len(centers) > 0:
        oldCenters=centers
        mes_rover=json.dumps({'rover': '{}'.format((int(centers[0][0]),int(centers[0][1])))})
        url = 'http://192.168.2.103:4567/rest/latency'
        payload = json.dumps({
            "step": "3",
            "frame": str(frameCounter),
            "timestamp": str(datetime.now().time())
        })
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        #print(response.text)
        myAWSIoTMQTTClient.publish(topic_rover, mes_rover, 1)
        
    else:
        mes_rover=json.dumps({'rover': '{}'.format((int(oldCenters[0][0]),int(oldCenters[0][1])))})
        myAWSIoTMQTTClient.publish(topic_rover, mes_rover, 1)
    if cv2.waitKey(10) & 0xFF == ord('q'):
         break


cv2.destroyAllWindows()
