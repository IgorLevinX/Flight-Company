from functions_utils import setup_logger, config_db
from flask import Flask, render_template, flash, redirect, url_for, session, request
from passlib.hash import sha256_crypt
import psycopg2
from psycopg2.extras import DictCursor
import secrets
import logging

# Using imported setup_logger function to create logger objects
setup_logger('write_log', 'INFO', 'app.log')
write_log = logging.getLogger('write_log')

# Using imported config_db function to create varaible with postgresql connection credentials and data
connection_data = config_db('database.ini', 'postgresql_creds')

# Initialzing Flask object and saving to 'app' variable
app = Flask(__name__)
# Configuring flask secret key to keep the users sessions secure
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Route and function for the home page of the app where users can register and login to the app
@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    # Condition when users logging to the app
    if request.form.get("login"):
        real_id = request.form['real_id_login']
        password = request.form['login_password']

        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # Quering using SELECT statement if logging user exist in users table in database
                    cursor.execute("SELECT * FROM users WHERE real_id = %(real_id)s", {'real_id': real_id})
                    user = cursor.fetchone()
                    if user:
                        # If the user is found checking if inserted passowrd is identical to the one in the database after decryption of it
                        if sha256_crypt.verify(password, user['password']):
                            # Creating a session dictionary for the user 
                            session['logged_in'] = True
                            session['user_id'] = user['id_ai']
                            session['is_admin'] = user['is_admin']
                            session['real_id'] = user['real_id']
                            flash(f"Hello {user['full_name']}")
                            write_log.info(f'User {real_id} has successfully logged in')
                            # Redirecting to the user to the menu page after the successful login
                            return redirect(url_for('menu'))
                        else:
                            flash("Invalid login, password incorrect")
                            write_log.error(f'Failed login attempt of {real_id} by inserting incorrect password')
                    else:
                        flash("Real ID not found")
                        write_log.error(f'Failed login attempt by using a non existing Real ID: {real_id}')
        
        # Catching the exception of when the connection to the database is lost
        except psycopg2.OperationalError as exception:
            flash("Failed to login, could not connect to server")
            write_log.error(f'Failed to login, could not connect to server: {exception}')
            return render_template('home.html')

    # Condition when new users registering to the app
    elif request.form.get("register"):
        full_name = request.form['full_name']
        password = request.form['register_password']
        confirm_password = request.form['confirm_password']
        real_id = request.form['real_id_register']

        # Checking if the full name of the user is at least two separate words (first name, last name)
        if len(full_name.split()) < 2:
            flash("Full name not entered or was entered in an incorrect format")
        # Checking if the passowrd and confirm passowrd are equal
        elif password != confirm_password:
            flash("Password do not match")
        else:
            # Encrypting the user desired passsowrd
            password = sha256_crypt.hash(str(password))
            # Checking if the user chose to be an admin user or a normal user
            is_admin = True if request.form.get('id_admin') else False
            try:
                # Connecting to postgresql database using connection data variable
                with psycopg2.connect(**connection_data) as connection:
                    with connection.cursor() as cursor:
                        try:
                            # Using INSERT statement to insert the new user to the users table in the database
                            cursor.execute("INSERT INTO users (full_name, password, real_id, is_admin) VALUES (%(full_name)s, %(password)s, %(real_id)s, %(is_admin)s) RETURNING id_ai", 
                                {'full_name': full_name, 'password': password, 'real_id': real_id, 'is_admin': is_admin})
                            connection.commit()
                        
                        # Exception thrown if there is a user with the same Real ID in the users table in the database
                        except psycopg2.errors.UniqueViolation:
                            write_log.error(f"User tried to register with existing Real ID of {real_id}")
                            flash(f"User with Real ID of {real_id} already exist")
                        else:
                            #cursor.execute("SELECT * FROM users WHERE real_id = %(real_id)s", {'real_id': real_id})
                            # If new user is created succefully checking if it's an admin or normal user and returning to the home page.
                            user = cursor.fetchone()[0]
                            if user:
                                if is_admin:
                                    write_log.info(f'Register of user {real_id} was successful as admin user')
                                else:
                                    write_log.info(f'Register of user {real_id} was successful')
                                flash('Register Successful')
                                return redirect(url_for('home'))
                            else:
                                write_log.error(f'Register of user {real_id} failed')
                                flash('Register Failed')

            # Catching the exception of when the connection to the database is lost
            except psycopg2.OperationalError as exception:
                flash("Failed to register, could not connect to server")
                write_log.error(f'Failed to register, could not connect to server: {exception}')
                return render_template('home.html')

    # Testing if user already logged on and have a running session. r
    # Redirecting to the menu page if there is a session   
    elif 'logged_in' in session and session['logged_in'] == True:
        flash(f"Hello {session['full_name']}")
        return redirect(url_for('menu'))

    return render_template('home.html')

# Fucntion for logging of a user by clearing the session dictionary object
def logout():
    write_log.info(f'User {session["real_id"]} logged out')
    session.clear()
    flash('You have been logged out')

# Route and function for redirecting to the menu page
@app.route('/menu', methods=['GET','POST'])
def menu():
    # If a user has a session enter the menu page
    if 'logged_in' in session and session['logged_in'] == True:
        # If the logout submit chosen call the logout function and redirect to home page
        if request.form.get("logout"):
            logout()
            return redirect(url_for('home'))

        return render_template('menu.html')
    # If a user trying to enter the menu page without logging in warn him and redirect him to the home page
    else:
        flash('Please, login before entering!')
        write_log.warning(f'There have been an attempt to enter menu before logging in')
        return redirect(url_for('home'))

# Route and function for the GET request for getting a logged on user private tickets or all of the users tickets
@app.route('/Tickets', methods=['GET'])
def get_tickets():
    show_tickets_table = None
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # Checking if the session of the logged on user is of and admin user
                if session['is_admin']:
                    # SELECT statement for getting all the tickets of all the users
                    cursor.execute('SELECT * FROM tickets')
                else:
                    # SELECT statement for getting the tickets of the logged on user only
                    cursor.execute('SELECT * FROM tickets WHERE user_id = %(user_id)s', {'user_id': session['user_id']})
                tickets = cursor.fetchall()
                if tickets:
                    # If there are tickets show them
                    show_tickets_table = True
                else:
                    flash(f'No tickets are avaliable')
    
    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
        write_log.error(f'Error: could not connect to database: {exception}')
        logout()
        return render_template('home.html')

    # Writing to log a different output based if a user an admin user or a normal user
    if session['is_admin']:
        write_log.info(f'User {session["real_id"]} queried get all users tickets')
    else:
        write_log.info(f'User {session["real_id"]} queried get all of his tickets')
    return render_template('menu.html', show_tickets_table=show_tickets_table, tickets=tickets)

# Route and function for the POST request for buying a ticket of a flight for the logged on user
@app.route('/Tickets', methods=['POST'])
def buy_tickets():
    # request function to get json object sent from client side
    request_json = request.get_json()
    flight_id = request_json['flight_id']
    
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # SELECT statement for getting a flight by its flight id
                cursor.execute('SELECT * FROM flights WHERE flight_id = %(flight_id)s', {'flight_id': flight_id})
                flight = cursor.fetchone()

                if flight:
                    # Checking if the number of remaining seats in a flight in bigger than zero
                    if flight['remaining_seats'] > 0:
                        # INSERT statement for adding the bought ticket to ticket table with the flight id and user id
                        cursor.execute('INSERT INTO tickets (user_id, flight_id) VALUES (%(user_id)s, %(flight_id)s) RETURNING ticket_id', {'user_id': session['user_id'], 'flight_id': flight_id})
                        connection.commit()
                        
                        # If INSERT statement is successful
                        if cursor.fetchone()[0]:
                            # UPDATE statement for decreasing the number of remaming seats in a flight by one if the user bought a ticket of the flight successfully
                            cursor.execute('UPDATE flights SET remaining_seats = %(remaining_seats)s WHERE flight_id = %(flight_id)s RETURNING remaining_seats',
                            {'flight_id': flight_id, 'remaining_seats': flight['remaining_seats']-1})
                            connection.commit()

                            write_log.info(f'User {session["real_id"]} bought ticket of flight {flight_id}. Number of remaining seats on flight {cursor.fetchone()[0]}')
                            flash(f'Ticket of flight {flight_id} was bought')
                            return redirect(url_for('menu'))
                        else:
                            # else condition when a user failed to buy a ticket
                            write_log.error(f'User {session["real_id"]} failed to buy ticket of flight {flight_id}')
                            flash(f'Failed to buy ticket of flight {flight_id}')
                    else:
                        # else condition when a user failed to buy a ticket becuase the remaining seats ran out
                        write_log.warning(f'User {session["real_id"]} tried to buy ticket of flight {flight_id} but no remaining seats are left')
                        flash(f'No remaining seats in flight {flight_id}')

                else:
                    # else condition when a flight was not found
                    flash(f'No flight with id {flight_id} was found')

    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
        write_log.error(f'Error: could not connect to database: {exception}')
        logout()
        return render_template('home.html')

    return render_template('menu.html', show_user_table=None)

# Route and function for the DELETE request for deleting a ticket a user bought
@app.route('/Tickets/<int:id>', methods=['DELETE'])
def delete_tickets(id):
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                if session['is_admin']:
                    # If user is admin use SELECT statement to find a ticket of any user by ticket id
                    cursor.execute('SELECT * FROM tickets WHERE ticket_id = %(id)s', {'id': id})
                else:
                    # Id user is a nrrmal user SELECT statement to find the logged on user itself tickets by ticket id
                    cursor.execute('SELECT * FROM tickets WHERE ticket_id = %(id)s AND user_id = %(user_id)s', {'id': id, 'user_id': session['user_id']})
                ticket = cursor.fetchone()
                if ticket:
                    # DELETE statement for deleting a ticket bought by a user by ticket id
                    cursor.execute('DELETE FROM tickets WHERE ticket_id = %(id)s RETURNING ticket_id', {'id': id})
                    connection.commit()

                    # SELECT statement for finding ticket by ticket id
                    cursor.execute('SELECT * FROM tickets WHERE ticket_id = %(id)s', {'id': id})
                    check_ticket = cursor.fetchone()
                    # Checking if the ticket not found becuase its deleted
                    if not check_ticket:
                        write_log.info(f'User {session["real_id"]} deleted ticket {ticket["ticket_id"]}')
                        flash(f'Ticket {id} was deleted')
                    else:
                        write_log.error(f'User {session["real_id"]} failed to delete ticket {ticket["ticket_id"]}')
                        flash(f'Failed to delete ticket {id}')
                else:
                    write_log.warning(f'Failed to find ticket {ticket["ticket_id"]} for user {session["real_id"]}')
                    flash(f'No ticket with id {id} was found')

    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
        write_log.error(f'Error: could not connect to database: {exception}')
        logout()
        return render_template('home.html')

    return render_template('menu.html', show_user_table=None)

# Route and function for the GET requests for finding all flights, flights by id or flights by country
@app.route('/Flights', defaults={'id': None, 'country': None}, methods=['GET'])
@app.route('/Flights/<int:id>', defaults={'country': None}, methods=['GET'])
@app.route('/Flights/<string:country>', defaults={'id': None}, methods=['GET'])
def get_flights(id=None,country=None):
    show_flight_table = None

    # If GET request by id was sent
    if id is not None:
        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # SELECT statement for getting flight by id with the origin country name and the destination country name
                    cursor.execute('''SELECT flights.flight_id, flights.timestamp, flights.remaining_seats, country_origin.name AS country_origin, country_dest.name AS country_dest FROM flights 
                    INNER JOIN countries AS country_origin ON country_origin.code_ai = flights.origin_country_id 
                    INNER JOIN countries AS country_dest ON country_dest.code_ai = flights.dest_country_id WHERE flights.flight_id = %(flight_id)s''', {'flight_id': id})
                    flights = cursor.fetchall()
                    # If flight found show it
                    if flights:
                        write_log.info(f'User {session["real_id"]} queried to get flight {id}')
                        show_flight_table = True
                    else:
                        flash(f'No flight with id {id} was found')
        
        # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
        except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')

    # If GET request by country was sent
    elif country is not None:
        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # SELECT statement for getting flight by country with the origin country name and the destination country name
                    cursor.execute('''SELECT flights.flight_id, flights.timestamp, flights.remaining_seats, country_origin.name AS country_origin, country_dest.name AS country_dest FROM flights
                    INNER JOIN countries AS country_origin ON country_origin.code_ai = flights.origin_country_id
                    INNER JOIN countries AS country_dest ON country_dest.code_ai = flights.dest_country_id 
                    WHERE country_origin.name = %(country)s OR country_dest.name = %(country)s''', {'country': country})
                    flights = cursor.fetchall()
                    # If flight found show it
                    if flights:
                        write_log.info(f'User {session["real_id"]} queried to get all flights by country {country}')
                        show_flight_table = True
                    else:
                        flash(f'No flights with country {country} exist')

        # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
        except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')

    # If GET request without id or country was sent
    else:
        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # SELECT statement for getting all flights with their origin country name and their destination country name
                    cursor.execute('''SELECT flights.flight_id, flights.timestamp, flights.remaining_seats, country_origin.name AS country_origin, country_dest.name AS country_dest FROM flights 
                    INNER JOIN countries AS country_origin ON country_origin.code_ai = flights.origin_country_id 
                    INNER JOIN countries AS country_dest ON country_dest.code_ai = flights.dest_country_id''')
                    flights = cursor.fetchall()
                    if flights:
                        # If flights found show them
                        write_log.info(f'User {session["real_id"]} queried to get all flights')
                        show_flight_table = True
                    else:
                        flash(f'No flights are avaliable')
        
        # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
        except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')

    return render_template('menu.html', show_flight_table=show_flight_table, flights=flights)

# Route and function for the POST request for adding flights
@app.route('/Flights', methods=['POST'])
def add_flights():
    request_json = request.get_json()
    origin_country = request_json['origin_country']
    dest_country = request_json['dest_country']
    timestamp = request_json['timestamp']
    remaining_seats = request_json['remaining_seats']

    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # Checking if the number of remaining seats entered for the flight is bigger than zero
                if int(remaining_seats) > 0:
                    
                    # SELECT statement for getting the countries name and ids of the entered countries by the user
                    cursor.execute('SELECT * FROM countries WHERE name = %(origin_country)s OR name = %(dest_country)s', {'origin_country': origin_country, 'dest_country': dest_country})
                    countries = cursor.fetchall()

                    # Checking if the two countries we found
                    if len(countries) == 2:
                        # Saving the country id to variables by comparing both country names given by the user with the those found in the database
                        # if the names found saving the respected id the the variable
                        origin_country_id = countries[0][0] if countries[0][1] == origin_country else countries[1][0]
                        dest_country_id = countries[0][0] if countries[0][1] == dest_country else countries[1][0]

                        try:
                            # INSERT statement for adding the new flight to the flights table in the database
                            cursor.execute('''INSERT INTO flights (timestamp, remaining_seats, origin_country_id, dest_country_id) 
                            VALUES (%(timestamp)s, %(remaining_seats)s, %(origin_country_id)s, %(dest_country_id)s) RETURNING flight_id''',
                            {'timestamp': timestamp, 'remaining_seats': remaining_seats, 'origin_country_id': origin_country_id, 'dest_country_id': dest_country_id})
                            connection.commit()
                        
                        except:
                            # Catching the exception if the commit of has failed
                            write_log.error(f'User {session["real_id"]} failed to add new flight')
                            flash('Failed to add flight')
                        else:
                            write_log.info(f'User {session["real_id"]} added new flight {cursor.fetchone()[0]} successfully')
                            flash('Flight was added successfully')

                        return redirect(url_for('menu'))
                    else:
                        # Conditions to check when one or both countries entered by the user were not found in the database
                        if countries[1] != origin_country:
                            flash(f'No country with name {origin_country} was found')
                        elif countries[1] != dest_country:
                            flash(f'No country with name {dest_country} was found')
                        else:
                            flash(f'No countries ith names {origin_country} and {dest_country} were found')
                            
                else:
                    flash('Enter a valid number of remaining seats')
    
    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')

    return render_template('menu.html', show_flight_table=None)

# Route and function for the PUT request for updating flights by id
@app.route('/Flights/<int:id>', methods=['PUT'])
def update_flights(id):
    request_json = request.get_json()
    
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # SELECT statement for getting flight by flight id
                cursor.execute('SELECT * FROM flights WHERE flight_id = %(id)s', {'id': id})
                flight = cursor.fetchone()
                if flight:
                    # Using the user entered values to create a dictionary with the vaules to update in the flight
                    flight_dict = {key:value for key,value in request_json.items() if request_json[key] != ''}
                    
                    # Checking if the length of the dictionary is at least two:
                    # the flight id and at least one more there is a reason to update the flight
                    if len(flight_dict) < 2:
                        flash('Enter at least one value to change in flight')
                        return render_template('menu.html', show_flight_table=None)

                    # Checking that the user wants to update the remaining seats of the flight
                    if 'remaining_seats' in flight_dict:
                        # Checking the the user enter a number greater than zeor for the remaining seats
                        if int(flight_dict['remaining_seats']) < 0:
                            flash('Enter a valid number of remaining seats')
                            return render_template('menu.html', show_flight_table=None)

                    # Checking that the user wants to update the origin country of the flight
                    if 'origin_country' in flight_dict:
                        # SELECT statement for finding and getting the country the wants
                        cursor.execute('SELECT * FROM countries WHERE name = %(origin_country)s', {'origin_country': flight_dict['origin_country']})
                        origin_country = cursor.fetchone()
                        # Checking that the country was found or not
                        if not origin_country:
                            flash(f'No country with name {flight_dict["origin_country"]} was found')
                            return render_template('menu.html', show_flight_table=None)
                        else:
                            # Creating a new key and value in the dictionary for the origin country id
                            flight_dict['origin_country_id'] = origin_country[0]
                            del flight_dict['origin_country']
                    
                    # Checking that the user wants to update the destination country of the flight
                    if 'dest_country' in flight_dict:
                        # SELECT statement for finding and getting the country the wants
                        cursor.execute('SELECT * FROM countries WHERE name = %(dest_country)s', {'dest_country': flight_dict['dest_country']})
                        dest_country = cursor.fetchone()
                        # Checking that the country was found or not
                        if not dest_country:
                            flash(f'No country with name {flight_dict["dest_country"]} was found')
                            return render_template('menu.html', show_flight_table=None)
                        else:
                            # Creating a new key and value in the dictionary for the destination country id
                            flight_dict['dest_country_id'] = dest_country[0]
                            del flight_dict['dest_country']
                    
                    # Checking that the user wants to update the timestamp of the flight
                    if 'timestamp' in flight_dict:
                        # Removing a character from timetamp input from the client side of the user to get a clean date for the database to uderstands
                        flight_dict['timestamp'] = flight_dict['timestamp'].replace('T',' ')

                    try:
                        # Creating the key and values that going to be inside the update query as a string
                        flight_update = (''.join([f'{key[0]} = %({key[0]})s, ' for key in flight_dict.items() if key[0] != 'flight_id']))[:-2]
                        # Creating the update query string
                        query = f'UPDATE flights SET {flight_update} WHERE flight_id = %(flight_id)s'
                        # UPDATE statement using the query string variable and dictionary with the user values to update the flight
                        cursor.execute(query, flight_dict)
                        connection.commit()

                    except:
                        # Catching an exception for when the commit faileds
                        write_log.error(f'User {session["real_id"]} failed to update flight {id}')
                        flash(f'Failed to update flight {id}')
                    else:
                        # Condition when the commit is succefully completed
                        write_log.info(f'User {session["real_id"]} updated flight {id} with new values for {[key for key in flight_dict.keys()]}')
                        flash(f'Flight {id} was updated successfully')
                    return render_template('menu.html', show_flight_table=None)
                        
                else:
                    write_log.warning(f'User {session["real_id"]} failed to update flight {id}')
                    flash(f'No flight with id {id} was found')

    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
        write_log.error(f'Error: could not connect to database: {exception}')
        logout()
        return render_template('home.html')        

    return render_template('menu.html', show_flight_table=None)

# Route and function for the DELETE request for deleting flights by id
@app.route('/Flights/<int:id>', methods=['DELETE'])
def delete_flights(id):
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # SELECT statement for getting flight by flight id
                cursor.execute('SELECT * FROM flights WHERE flight_id = %(id)s', {'id': id})
                flight = cursor.fetchone()
                if flight:
                    # DELETE statement for deleting a flight by its flight id
                    cursor.execute('DELETE FROM flights WHERE flight_id = %(id)s', {'id': id})
                    connection.commit()

                    # SELECT statement for finding flight by flight id
                    cursor.execute('SELECT * FROM flights WHERE flight_id = %(id)s', {'id': id})
                    check_flight = cursor.fetchone()
                    # Checking if the flight not found becuase it was deleted
                    if not check_flight:
                        write_log.info(f'User {session["real_id"]} deleted flight {id} successfully')
                        flash(f'Flight {id} was deleted')
                    else:
                        write_log.error(f'User {session["real_id"]} failed to delete flight {id}')
                        flash(f'Failed to delete flight {id}')
                else:
                    flash(f'No flight with id {id} was found')
    
    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
        write_log.error(f'Error: could not connect to database: {exception}')
        logout()
        return render_template('home.html')        

    return render_template('menu.html', show_flight_table=None)

# Route and function for the GET requests for finding all countries or country by id
@app.route('/Countries', defaults={'id': None}, methods=['GET'])
@app.route('/Countries/<int:id>', methods=['GET'])
def get_countries(id=None):
    show_countries_table = None

    # If GET request by id was sent
    if id is not None:
        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # SELECT statement for getting a country by country code_ai
                    cursor.execute('SELECT * FROM countries WHERE code_ai = %(id)s', {'id': id})
                    countries = cursor.fetchall()
                    # If country found show it
                    if countries:
                        write_log.info(f'User {session["real_id"]} queried to get country by id {id}')
                        show_countries_table = True
                    else:
                        flash(f'No country with id {id} was found')
        
        # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
        except psycopg2.OperationalError:
            flash("Logged out, could not connect to server")
            return render_template('home.html')

    else:
        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # SELECT statement for getting all countries
                    cursor.execute('SELECT * FROM countries')
                    countries = cursor.fetchall()
                    # If countries found show them
                    if countries:
                        write_log.info(f'User {session["real_id"]} queried to get all countries')
                        show_countries_table = True
                    else:
                        flash(f'No countries are avaliable')
        
        # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
        except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')

    return render_template('menu.html', show_countries_table=show_countries_table, countries=countries)

# Route and function for the POST request for adding countries
@app.route('/Countries', methods=['POST'])
def add_countries():
    request_json = request.get_json()
    country_name = request_json['country_name']

    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                try:
                    # INSERT statement for adding a country to the countries table in the database
                    cursor.execute('INSERT INTO countries (name) VALUES (%(country_name)s) RETURNING code_ai', {'country_name': country_name})
                    connection.commit()
                
                except psycopg2.errors.UniqueViolation:
                    # Exception if the user tried to add a country that already in the database
                    write_log.error(f'User {session["real_id"]} failed to add new country')
                    flash(f"Country with name {country_name} already exist")
                else:
                    write_log.info(f'User {session["real_id"]} added new country {cursor.fetchone()[0]} successfully')
                    flash(f'Country {country_name} has been added')
                    return redirect(url_for('menu'))

    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')

    return render_template('menu.html', show_countries_table=None)

# Route and function for the DELETE request for deleting countries by id
@app.route('/Countries/<int:id>', methods=['DELETE'])
def delete_countries(id):
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # SELECT statement for getting flight by country code_ai
                cursor.execute('SELECT * FROM countries WHERE code_ai = %(id)s', {'id': id})
                country = cursor.fetchone()
                if country:
                    # DELETE statement for deleting a country by its ntry code_ai
                    cursor.execute('DELETE FROM countries WHERE code_ai = %(id)s', {'id': id})
                    connection.commit()

                    # SELECT statement for finding country by country code_ai
                    cursor.execute('SELECT * FROM countries WHERE code_ai = %(id)s', {'id': id})
                    check_country = cursor.fetchone()
                    # Checking if the country not found becuase it was deleted
                    if not check_country:
                        write_log.info(f'User {session["real_id"]} deleted country {id} successfully')
                        flash(f'Country {id} was deleted')
                    else:
                        write_log.error(f'User {session["real_id"]} failed to delete country {id}')
                        flash(f'Failed to delete country {id}')
                else:
                    flash(f'No country with id {id} was found')
    
    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')
            
    return render_template('menu.html', show_user_table=None)

# Route and function for the GET requests for finding all users or user by id
@app.route('/Users', defaults={'id': None}, methods=['GET'])
@app.route('/Users/<int:id>', methods=['GET'])
def get_users(id=None):
    show_users_table = None

    # If GET request by id was sent
    if id is not None:
        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # SELECT statement for getting user by user id_ai
                    cursor.execute('SELECT * FROM users WHERE id_ai = %(id)s', {'id': id})
                    users = cursor.fetchall()
                    # If user found show him
                    if users:
                        write_log.info(f'User {session["real_id"]} queried to get user by id {id}')
                        show_users_table = True
                    else:
                        flash(f'No user with id {id} was found')
        
        # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
        except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')        
    
    # If GET request without id was sent
    else:
        try:
            # Connecting to postgresql database using connection data variable
            with psycopg2.connect(**connection_data) as connection:
                with connection.cursor(cursor_factory = DictCursor) as cursor:
                    # SELECT statement for getting all users
                    cursor.execute('SELECT * FROM users')
                    users = cursor.fetchall()
                    write_log.info(f'User {session["real_id"]} queried to get all users')
                    # If users found show them
                    if users:
                        show_users_table = True
                    else:
                        flash(f'No users are avaliable')

        # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
        except psycopg2.OperationalError as exception:
            write_log.error(f'Error: could not connect to database: {exception}')
            logout()
            return render_template('home.html')        

    return render_template('menu.html', show_users_table=show_users_table, users=users)

# Route and function for the PUT request for updating users by id
@app.route('/Users/<int:id>', methods=['PUT'])
def update_users(id):
    request_json = request.get_json()
    
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # SELECT statement for getting user by user id_ai
                cursor.execute('SELECT * FROM users WHERE id_ai = %(id)s', {'id': id})
                user = cursor.fetchone()
                if user:
                    # Using the user entered values to create a dictionary with the vaules to update in the other user
                    user_dict = {key:value for key,value in request_json.items() if request_json[key] != ''}
                    
                    # Checking if the length of the dictionary is at least two:
                    # the flight id and at least one more there is a reason to update the other user
                    if len(user_dict) < 2:
                        flash('Enter at least one value to change in user')
                        return render_template('menu.html', show_user_table=None)
                    
                    # Checking that the user wants to update the full name of the other user
                    if 'full_name' in user_dict:
                        # Checking if the full name of the user is at least two separate words (first name, last name)
                        if len(user_dict['full_name']) < 2:
                            flash(flash("new full name not enteded corectly or in incorrect format")) 
                            return render_template('menu.html', show_user_table=None)
                    
                    # Checking if both passowrd field in the client side were filed to change the password
                    if ('new_password' in user_dict and 'confirm_password' not in user_dict) or ('new_password' not in user_dict and 'confirm_password' in user_dict):
                        flash('To change password fill both password fields')
                        return render_template('menu.html', show_user_table=None)
                    # Checking if both password fields are equal to one another
                    elif 'new_password' in user_dict and 'confirm_password' in user_dict:
                        if user_dict['new_password'] != user_dict['confirm_password']:
                            flash("New passowrd fields do not match")
                            return render_template('menu.html', show_user_table=None)
                        else:
                            # Encrypting the new passwords for the other user then saving it in the dictionary and removing the two password the user entered in the client side
                            password = sha256_crypt.hash(str(user_dict['new_password']))
                            user_dict['password'] = password
                            del user_dict['new_password']
                            del user_dict['confirm_password']
                            
                    # Checking that the user wants to update the real id number of the other user
                    if 'real_id_number' in user_dict:
                        # SELECT statement for for checking if there is already a user with the new real id in the database
                        cursor.execute('SELECT * FROM users WHERE real_id = %(real_id)s', {'real_id': user_dict['real_id_number']})
                        real_id_number = cursor.fetchone()
                        if real_id_number:
                            flash(f"User with Real ID of {real_id_number} already exist")
                            return render_template('menu.html', show_user_table=None)

                    try:
                        # Creating the key and values that going to be inside the update query as a string
                        user_update = (''.join([f'{key[0]} = %({key[0]})s, ' for key in user_dict.items() if key[0] != 'id_ai']))[:-2]
                        # Creating the update query string
                        query = f'UPDATE users SET {user_update} WHERE id_ai = %(id_ai)s'
                        # UPDATE statement using the query string variable and dictionary with the user values to update the other user
                        cursor.execute(query, user_dict)
                        connection.commit()

                    except:
                         # Catching an exception for when the commit fields
                        write_log.error(f'User {session["real_id"]} failed to update user {id}')
                        flash(f'Failed to update user {id}')
                    else:
                        # Condition when the commit is succefully completed
                        write_log.info(f'User {session["real_id"]} updated user {id} with new values for {[key for key in user_dict.keys()]}')
                        flash(f'user {id} was updated successfully')
                    return render_template('menu.html', show_user_table=None)
                        
                else:
                    write_log.warning(f'User {session["real_id"]} failed to update user {id}')
                    flash(f'No user with id {id} was found')

    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
        write_log.error(f'Error: could not connect to database: {exception}')
        logout()
        return render_template('home.html')

    return render_template('menu.html', show_user_table=None)

# Route and function for the DELETE request for deleting users by id
@app.route('/Users/<int:id>', methods=['DELETE'])
def delete_users(id):
    try:
        # Connecting to postgresql database using connection data variable
        with psycopg2.connect(**connection_data) as connection:
            with connection.cursor(cursor_factory = DictCursor) as cursor:
                # SELECT statement for getting user by user id_ai
                cursor.execute('SELECT * FROM users WHERE id_ai = %(id)s', {'id': id})
                user = cursor.fetchone()
                if user:
                    # Checking if the logged on user does not try to delete his own user
                    if user['id_ai'] != session['user_id']:
                        # DELETE statement for deleting a user by user id_ai
                        cursor.execute('DELETE FROM users WHERE id_ai = %(id)s', {'id': id})
                        connection.commit()

                        # SELECT statement for finding user by user id_ai
                        cursor.execute('SELECT * FROM users WHERE id_ai = %(id)s', {'id': id})
                        check_user = cursor.fetchone()
                        # Checking if the user not found becuase it was deleted
                        if not check_user:
                            write_log.info(f'User {session["real_id"]} deleted user {id} successfully')
                            flash(f'User {id} was deleted')
                        else:
                            write_log.error(f'User {session["real_id"]} failed to delete user {id}')
                            flash(f'Failed to delete user {id}')
                    else:
                        flash("You can't delete your own user")
                else:
                    flash(f'No user with id {id} was found')

    # Catching the exception of when the connection to the database is lost and then logging of the user and redirecting to the home page
    except psycopg2.OperationalError as exception:
        write_log.error(f'Error: could not connect to database: {exception}')
        logout()
        return render_template('home.html')
        
    return render_template('menu.html', show_user_table=None)


# Checking if the program runs from the main file as the main function
if __name__ == '__main__':
    # Checking if the connection data to the database is a string and not a dictionary and so it will not connect and start the server
    if isinstance(connection_data, str):
      write_log.error(connection_data)
    else:
        try:
            # Connecting to postgresql database using connection data variable to test the connection
            psycopg2.connect(**connection_data)
        except psycopg2.OperationalError as exception:
            write_log.error(f'Failed to connect to database: {exception}')
        else:
            try:
                # If everything successful starting up the server
                write_log.info(f'Server strated successfully')
                app.run(debug=True, use_reloader=False)
            finally:
                write_log.info(f'Server Stopped')
