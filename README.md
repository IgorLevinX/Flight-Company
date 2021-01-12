
## Flight Comapny REST project using python Flask for server side, HTML with Jinj for client side and PostgreSQL for database 

### Project Summary
The project contain a main app.py file that starts the Flask server and has all the main functions and requests.
There is also function_utils files that contain extra functions for the app.py file.
Before starting the server you need to create the database and therefore there is the sql script file and the credentials file for connection
Also there are the template folder with the three HTML files with Jinj2 inside of it for functionallity and integration with the python files.

### App Tested with Ubuntu, Debian and Windows 10 Pro

#### Install Docker on ubuntu:
https://docs.docker.com/engine/install/ubuntu/

#### Install Docker on Debian:
https://docs.docker.com/engine/install/debian/

#### Install Docker on Windows 10 Pro with Docker Desktop:
https://docs.docker.com/docker-for-windows/install/

#### Install Python3 on Ubuntu and Debian:
>$ sudo apt-get update
>$ sudo apt-get install python3 python3-pip python3-tk

#### Install Python3 on Windows 10 Pro:
Download the Python3 installer from the official python site:

https://www.python.org/downloads/

While installing choose to install pip and all optional features.

#### Checking python3 and docker installtions:
Open the command line of each OS:
>$ docker version (On Ubuntu, Debian and Windows)

>$ python --version (On Windows)

>$ python3 --version (On Ubuntu, Debian)

#### Install Docker SDK for Python3:
Installing docker sdk for python3 is done by the python pip package installer for python.
Checking if pip3 installed:
>$ pip3 --version

Installing the docker sdk:

>$ pip3 install docker

### App Instructions
#### Strating the app
Open the command line of each OS and start the app using python3:
>$ python3 Docker-App.py
#### Using the app
The app has for text boxes to enter the following informtaion in the next format:
- Image Name (Examples: nginx, nginx:latest etc...)

- Container Name (Examples: mynginx, mynginx:latest etc...)

- Ports (Examples: 80:8080,3306:5000, etc...)

  For ports the format is on the left is the container port and on the right is the host server port.

- Environment (Examples: MYSQL_RANDOM_ROOT_PASSWORD=yes and etc...)

  For envirnoment option for envirnoment variables you can use any option you want inside it.

After filling the the text boxes for what needed the user chooses the desired docker command to run by click the radio button with the same name.

After that the user clicks the **Submit** button to start the operation.

* The **Get** option in the container and image sections is not based on docker command by the same name and used to get a conatainer or image by its name or all container or images if name not used.
