import cv2
import numpy as np
import cv2.aruco as aruco
import logging
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import csv
import sys


i=0
empty = []
cap = cv2.VideoCapture('crawler.mp4')
qrCodeDetector = cv2.QRCodeDetector()
print('Length: {}'.format(sys.argv))
print('Arg 1: {}'.format(sys.argv[1]))
print('Arg 2: {}'.format(sys.argv[2]))
while(True):
    ret,frame=cap.read()
    if frame is None:
        break;
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
        print('Marker Corners -> {}'.format(marker_corners[0]))
        print('Marker Center -> {}'.format(np.mean(marker_corners[0],
                                                           axis=0).tolist()))
        centers.append(np.mean(marker_corners[0],
                               axis=0).tolist())

    #print('Centers {}'.format(centers))
    #print('Differences x: {}, y: {}'.format(np.subtract(int(co[i][0]),int(centers[0][0])),np.subtract(int(co[i][1]),int(centers[0][1]))))
    if(len(centers)>0):
        empty.append([int(centers[0][0]),int(centers[0][1])]) 
    else:
        print('Don't see the marker')
    i=i+1
    if len(centers) > 0:
        cv2.circle(frame, (int(centers[0][0]),int(centers[0][1])),10,(255,0,0), -1)
    cv2.imshow("Video", frame)
    if cv2.waitKey(10) & 0xFF == ord('q'):
         break

cap.release()
cv2.destroyAllWindows()
centersArray = np.array(empty) 
with open("coordinates2.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(centersArray)