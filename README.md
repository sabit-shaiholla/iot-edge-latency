# Iot and Edge Computing - Latency Analysis
The goal of this project is to show you the latency and quality of service implications when choosing different edge and cloud nodes to work with in the IoT and Edge Computing.
Tech-stack: Python, OpenCV, Virtual Machines (Linux servers), Raspberry Pi, AWS EC2 and AWS Greengrass

The following is a list of key components needed for this project:
•	Reference.py – Python script that you run once on your local machine
•	Client.py – Python script running on your local machine
•	Server.py – Python script running on your processing machine
•	Raspberry Pi, AWS EC2 instance, VirtualBox VM – processing machines
•	AWS Greengrass – AWS IoT service based on MQTT, running on one of the processing machines – GGC needs to be set up and run
•	Edge Diagnostics Platform (JAR and config files) – Platform that will enables us to track latency
•	The video with Aruco marker
