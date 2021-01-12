# Extra functions for main app.py file
import logging
from configparser import ConfigParser

# Function to create a logger object to log program events with time and message.
# The function creates a stream logger for logging to console and if given to a file.
def setup_logger(logger_name, log_level, log_file=None):
    logger = logging.getLogger(logger_name)
    # Creating the custom logging message format
    formatter = logging.Formatter('%(asctime)s : %(message)s', '%Y-%m-%d %H:%M:%S')
    # Setting the log level by getting the attribute value form the log level name
    logger.setLevel(getattr(logging, log_level))
    # Creating the a stream handler for the log to print on the console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    # If specified creating also a file handler to write the logs to a file
    if log_file:
      file_handler = logging.FileHandler(log_file)
      file_handler.setFormatter(formatter)
      logger.addHandler(file_handler)
      logger.addHandler(stream_handler)  
    else:
      logger.addHandler(stream_handler)  

# Function to read sql config file to use on creation of sql connection in python
def config_db(filename, section):
  # Creating a ConfigParser obejct and giving him the filename of my connection file 
  parser = ConfigParser()
  parser.read(filename)
  db = {}
  # if the file has the section parameter inside him
  if parser.has_section(section):
      params = parser.items(section)
      # Looping over the data inside the file and saving it to the db dictionary vairiable
      for param in params:
          db[param[0]] = param[1]
  else:
      return f'Section {section} not found in the {filename} file'
  # Returning the db dictionary vairiable 
  return db
