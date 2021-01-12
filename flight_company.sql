CREATE DATABASE flight_company;

\connect flight_company;

CREATE TABLE IF NOT EXISTS countries (
	code_ai INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
	name VARCHAR(100) UNIQUE NOT NULL
);

 CREATE TABLE IF NOT EXISTS flights (
	 flight_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	 timestamp timestamp NOT NULL,
	 remaining_seats INT NOT NULL,
	 origin_country_id INT,
	 dest_country_id INT,
	 FOREIGN KEY (origin_country_id) REFERENCES countries(code_ai)
	 ON UPDATE CASCADE
	 ON DELETE CASCADE,
	 FOREIGN KEY (dest_country_id) REFERENCES countries(code_ai)
	 ON UPDATE CASCADE
	 ON DELETE CASCADE
 );

CREATE TABLE IF NOT EXISTS users (
	id_ai INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
	full_name VARCHAR(100) NOT NULL,
	password VARCHAR(255) NOT NULL,
	real_id VARCHAR(10) UNIQUE NOT NULL,
	is_admin BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
	 ticket_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	 user_id INT,
	 flight_id INT,
	 FOREIGN KEY (user_id) REFERENCES users(id_ai)
	 ON UPDATE CASCADE
	 ON DELETE CASCADE,
	 FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
	 ON UPDATE CASCADE
	 ON DELETE CASCADE
 );

