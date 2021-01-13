
## Flight Comapny REST project using python Flask for server side, HTML with Jinja2 for client side and PostgreSQL for database 

### Project Summary
The project contain a main app.py file that starts the Flask server and has all the main functions and requests.
There is also function_utils files that contain extra functions for the app.py file.
Before starting the server you need to create the database and therefore there is the sql script file and the credentials file for connection
Also there are the template folder with the three HTML files with Jinj2 inside of it for functionallity and integration with the python files.

### Prequisites for project

#### Install the following programs:
- Python 3
- Pip 3
- PostgreSQL

#### Install Python 3 packages:
>$ pip install psycopg2-binary psycopg2 flask passlib

or

>$ pip3 install psycopg2-binary psycopg2 flask passlib


### App Instructions
#### Strating the app
Open the command line of each OS and start the app using python form the project directory:
>$ python app.py

or

>$ python3 app.py

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
