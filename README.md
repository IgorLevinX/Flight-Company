## Flight Company REST Project

### Project Summary
The project contain a main app.py file that starts the Flask server and has all the main functions and requests.
There is also function_utils files that contain extra functions for the app.py file.
Before starting the server you need to create the database for it and therefore you can run the sql script file and the app.py will use the credentials file for connection.
The client side for the project is located in the templates folder with the three HTML files with Jinja2 inside of it for functionallity and integration with the python files.

### Project Components
- Python Flask for server side
- HTML with Jinja2 for client side
- PostgreSQL for database

### Prequisites for project

#### Install the following programs:
- Python 3
- Pip 3
- PostgreSQL

#### Install Python 3 packages:
>pip install psycopg2-binary psycopg2 flask passlib

or

>pip3 install psycopg2-binary psycopg2 flask passlib


### App Instructions

#### Importing the sql script
To import the sql import enter the PostgreSQL with an admin user
One way to import is to run the following command from the PostgreSQL command line:
>\i \<path to sql script\>\flight_company.sql

#### Configuring the database.ini credentials file
For the app.py to connect to the database it uses a configuration file with the credentials for the connection:

- user - The username with the permission to read and write to the database
- password - The user password to connect to the database
- host - The IP or Hostname of the server to coonect (Default 127.0.0.1 for the local host)
- port - The port the database listening to (Default 5432 or 5433)
- database - database name to connect (flight_company in this project)

#### Strating the app
Open the command line and start the app using python from the project directory:
>python app.py

or

> python3 app.py

#### Using the app
- When the server starts browse to the following URL: http://127.0.0.1:5000/
- On home page of the project you will have two option: Login or Register
  - Login - In the login option the user can enter his real id number and password and if correct he will be redirected to the menu page of the project
  - Register - In the register option the needs to fill the required information in the input boxes and choose if he is an admin user or not. 
    If all the was filled correctly a user will be created to use in the login option.
- After a successful login the user will be redirected to the menu page.
- The menu page have to showing option one for normal user and one for admin user
- Normal user menu page:
  - In this page the user has the follwoing options
