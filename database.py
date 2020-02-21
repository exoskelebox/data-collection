import numpy.random as random
import datetime
from configparser import ConfigParser
import psycopg2

SCHEMA = {
    'subjects': """
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
    'data': """ 
    CREATE TABLE data (
        subject_id INTEGER NOT NULL REFERENCES subjects (subject_id) ON DELETE CASCADE,
        gesture VARCHAR(16) NOT NULL,
        repetition SMALLINT NOT NULL CHECK (repetition >= 0 AND repetition <= 10),
        reading_count INTEGER NOT NULL CHECK (reading_count >= 0),
        timestamp TIME (6) NOT NULL,
        readings SMALLINT[] NOT NULL, 
        PRIMARY KEY (subject_id, timestamp)
    )
    """,
    'calibration': """
    CREATE TABLE calibration (
        subject_id INTEGER NOT NULL REFERENCES subjects (subject_id) ON DELETE CASCADE,
        calibration_gesture VARCHAR(16) NOT NULL,
        calibration_iterations SMALLINT NOT NULL CHECK (calibration_iterations >= 0 and calibration_iterations <=125),
        calibration_values SMALLINT[] NOT NULL,
        PRIMARY KEY (subject_id, calibration_gesture)
    )
    """,
}

def _config(filename='database.ini', section='postgresql'):
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
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        # create table one by one
        for command in SCHEMA.values():
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


def _connect():
    """ Connect to the PostgreSQL database server """   
    conn = None         
    try:
        # read database configuration
        params = _config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error

def _insert(table: str, data: dict, returning:list=None):
    """ insert data into table """

    columns, values = data.keys(), tuple(data.values())
    _returning = ""
    if returning:
        _returning = f" RETURNING ({', '.join(returning)})"
    returned = None
    conn = None
    try:
        conn = _connect()
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(f"INSERT INTO {table}({','.join(columns)}) VALUES %s{_returning};", (values,))

        # get the generated id back
        if returning:
            returned = cur.fetchall()

        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
        print(f"Inserted {values} for into {table}. Received {returned} back.")
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()

    return returned

def insert_subject(subject):
    """ insert a new subject into the subjects table """
    subject_id = _insert(table='subjects', data=subject, returning= ['subject_id'])[0][0]
    return subject_id

def insert_calibration(calibration):
    """ insert a new calibration into the calibration table """
    result = _insert(table='calibration', data=calibration, returning=None)

def insert_data(data):
    """ insert new data into the data table"""
    result = _insert(table='data', data=data, returning=None)

def _delete(table: str, condition: str, args):
    """ delete rows from table where condition matches """
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        # execute the UPDATE  statement
        
        cur.execute(f"DELETE FROM {table} WHERE {condition}", args)
        # get the number of updated rows
        rows_deleted = cur.rowcount
        print(f"Deleted {rows_deleted} row(s).")
        sql = f"DELETE FROM {table} WHERE {condition}"
        print(f"SQL: '{sql}', Args: '{args}'")
        # Commit the changes to the database
        conn.commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error
    finally:
        if conn is not None:
            conn.close()
      
def delete_subject(subject_id):
    _delete("subjects", "(subject_id = %s)", (subject_id,))

def delete_calibration(subject_id, gesture):
    _delete("calibration", "(subject_id = %s AND calibration_gesture = %s)", (subject_id, gesture,))

def delete_data(subject_id, gesture, repetition):
    _delete("data", "(subject_id = %s AND gesture = %s AND repetition = %s)", (subject_id, gesture, repetition,))

def get_all(table):
    """ query all data from the table """
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table}")
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


def _insert_dummy_subject():
    subject = {
        'subject_gender': 'm',
        'subject_age': 100,
        'subject_fitness': 1,
        'subject_handedness': 'r',
        'subject_impairment': 'n',
        'subject_wrist_circumference': 20 ,
        'subject_forearm_circumference': 29,
    }
    subject_id = insert_subject(subject)
    return subject_id

def _insert_dummy_data(sid):
    data = {
        'subject_id': sid,
        'gesture': "dummy gesture", 
        'repetition': 1,
        'reading_count': 1,
        'timestamp': datetime.datetime.utcnow().strftime('%H:%M:%S.%f'),
        'readings': [random.randint(5, 155) for _ in range(15)],
    }
    insert_data(data)

def _insert_dummy_calibrations(sid):
    for i in range(2):
        calibration = {
            'subject_id': sid,
            'calibration_gesture': f"dummy gesture {i+1}",
            'calibration_iterations': random.randint(0, 125),
            'calibration_values': [random.randint(5, 155) for _ in range(8-i)],
        }
        insert_calibration(calibration)

def insert_dummies():
    sid =_insert_dummy_subject()
    print(f"sid = {sid}")
    _insert_dummy_calibrations(sid)
    _insert_dummy_data(sid)

def reset(table: str, cascade:bool=False):
    """ drop table and recreate """
    if table in SCHEMA.keys():
        conn = None
        try:
            conn = _connect()
            cur = conn.cursor()
            cur.execute(f"DROP TABLE IF EXISTS {table}{' CASCADE' if cascade else ''}")
            print(f"Dropped table '{table}'")
            cur.execute(SCHEMA[table])
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    else:
        print(f"Error: '{table}' does not exist")

def reset_all():
    print('resetting everything')
    reset('calibration')
    reset('data')
    reset('subjects', cascade=True)
    print('reset done')

if __name__ == '__main__':

    for table in SCHEMA.keys():
        get_all(table)

    #delete_data(17, 'dummy gesture', 1)
    #delete_calibration(17, 'dummy gesture 2')
    delete_subject(13)

    for table in SCHEMA.keys():
        get_all(table)

    print('done')
