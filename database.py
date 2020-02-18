import numpy.random as random
import datetime
from configparser import ConfigParser
import psycopg2


def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
 
    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
 
    return db

def setup():
    print(""" create tables in the PostgreSQL database""")
    commands = (
        """
        CREATE TABLE subjects (
            subject_id SERIAL PRIMARY KEY,
            subject_gender CHAR(1) NOT NULL CHECK (subject_gender IN ('m','f')),
            subject_age SMALLINT NOT NULL CHECK (subject_age >= 16 AND subject_age <= 100),
            subject_fitness SMALLINT NOT NULL CHECK (subject_fitness >= 0 AND subject_fitness <= 7),
            subject_handedness CHAR(1) NOT NULL CHECK (subject_handedness IN ('r','l')),
            subject_impairment BOOLEAN NOT NULL,
            subject_wrist_circumference REAL NOT NULL CHECK (subject_wrist_circumference >= 10 AND subject_wrist_circumference <= 25),
            subject_forearm_circumference REAL NOT NULL CHECK (subject_forearm_circumference >= 15 AND subject_forearm_circumference <= 30)
        )
        """,
        """ CREATE TABLE data (
                subject_id INTEGER NOT NULL,
                gesture VARCHAR(16) NOT NULL,
                repetition SMALLINT NOT NULL CHECK (repetition >= 0 AND repetition <= 10),
                reading_count INTEGER NOT NULL CHECK (reading_count >= 0),
                timestamp TIME (6) NOT NULL,
                readings SMALLINT[] NOT NULL, 
                PRIMARY KEY (subject_id, timestamp),
                FOREIGN KEY (subject_id)
                    REFERENCES subjects (subject_id)
        )
        """,
        """
        CREATE TABLE calibration (
                subject_id INTEGER NOT NULL,
                calibration_gesture VARCHAR(16) NOT NULL,
                calibration_iterations SMALLINT NOT NULL CHECK (calibration_iterations >= 0 and calibration_iterations <=125),
                calibration_values SMALLINT[] NOT NULL,
                PRIMARY KEY (subject_id, calibration_gesture),
                FOREIGN KEY (subject_id)
                    REFERENCES subjects (subject_id)
        )
        """,)
    conn = None
    try:
        # read the connection parameters
        params = config()
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # create table one by one
        for command in commands:
            cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
        print('Exoskelebox setup complete.')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
      
        # create a cursor
        cur = conn.cursor()
        
   # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
 
        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
       
       # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
 

def insert_subject(subject):
    """ insert a new subject into the subjects table """
    sql = """INSERT INTO subjects(subject_age, subject_gender, subject_fitness, subject_impairment, subject_handedness, subject_wrist_circumference, subject_forearm_circumference)
             VALUES{0} RETURNING subject_id;"""
    conn = None
    subject_id = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql.format(subject))
        # get the generated id back
        subject_id = cur.fetchone()[0]
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
        print("Inserted {0} for subject {1}".format(subject, subject_id))

    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()
 
    return subject_id

def insert_calibration(calibration):
    """ insert a new calibration into the calibration table """
    sql = """INSERT INTO calibration(subject_id, calibration_gesture, calibration_values, calibration_iterations)
             VALUES{0};"""
    conn = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql.format(calibration).replace('[', "'{").replace(']', "}'"))
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()

        print("Inserted {0} into calibration".format(calibration))
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def insert_data(data):
    """ insert new data into the data table"""
    sql = """INSERT INTO data(subject_id, gesture, repetition, reading_count, timestamp, readings)
             VALUES{0};"""
    conn = None
    try:
        # read database configuration
        params = config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql.format(data).replace('[', "'{").replace(']', "}'"))
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
        print("Inserted {0} into data".format(data))
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
 
def _insert_dummy_subject():
    subject_gender = 'm'
    subject_age = 100
    subject_fitness = 1 
    subject_handedness = 'r'
    subject_impairment = 'n'
    subject_wrist_circumference = 20 
    subject_forearm_circumference = 29

    sid = insert_subject((subject_gender, subject_age, subject_fitness, subject_handedness, subject_impairment, subject_wrist_circumference, subject_forearm_circumference,))
    return sid

def _insert_dummy_data(sid):
    subject_id = sid
    gesture = "dummy gesture" 
    repetition = 1
    reading_count = 1
    timestamp = datetime.datetime.utcnow().strftime('%H:%M:%S.%f')
    readings = [random.randint(5, 155) for _ in range(15)]

    insert_data((subject_id, gesture, repetition, reading_count, timestamp, readings,))

def _insert_dummy_calibration(sid):
    subject_id = sid
    for i in range(2):
        calibration_iterations = random.randint(0, 125)
        calibration_gesture = "dummy gesture %i" % (i+1)
        calibration_values = [random.randint(5, 155) for _ in range(8-i)]
        print(f'{(subject_id, calibration_gesture, calibration_iterations, calibration_values,)}')

        #calibration_values = str(calibration_values).replace('[', '{').replace(']', '}')
        print(f'{(subject_id, calibration_gesture, calibration_iterations, calibration_values,)}')
        
        insert_calibration((subject_id, calibration_gesture, calibration_iterations, calibration_values,))

def get_all(table):
    """ query data from the subjects table """
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT * FROM %s" % table)
        print("The number of entries: ", cur.rowcount)
        row = cur.fetchone()
 
        while row is not None:
            print(row)
            row = cur.fetchone()
 
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def insert_dummies():
    sid =_insert_dummy_subject()
    print(f"sid = {sid}")
    _insert_dummy_calibration(sid)
    _insert_dummy_data(sid)

if __name__ == '__main__':
    insert_dummies()
    get_all('subjects')
    get_all('calibration')
    get_all('data')
    print('done')
