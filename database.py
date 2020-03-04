import numpy.random as random
import datetime
import time
from configparser import ConfigParser
import psycopg2
from psycopg2.extras import execute_values
from flask import current_app

SCHEMA = {
    'subjects': """
    CREATE TABLE subjects (
        subject_id SERIAL PRIMARY KEY,
        subject_gender CHAR(1) NOT NULL CHECK (subject_gender IN ('m','f')),
        subject_age SMALLINT NOT NULL CHECK (subject_age >= 18 AND subject_age <= 100),
        subject_fitness SMALLINT NOT NULL CHECK (subject_fitness >= 0 AND subject_fitness <= 7),
        subject_handedness CHAR(1) NOT NULL CHECK (subject_handedness IN ('r','l')),
        subject_impairment BOOLEAN NOT NULL,
        subject_wrist_circumference REAL NOT NULL CHECK (subject_wrist_circumference >= 10 AND subject_wrist_circumference <= 30),
        subject_forearm_circumference REAL NOT NULL CHECK (subject_forearm_circumference >= 10 AND subject_forearm_circumference <= 40)
    )
    """,
    'data': """ 
    CREATE TABLE data (
        subject_id INTEGER NOT NULL REFERENCES subjects (subject_id) ON DELETE CASCADE,
        gesture VARCHAR(32) NOT NULL,
        repetition SMALLINT NOT NULL CHECK (repetition >= 0 AND repetition <= 10),
        reading_count INTEGER NOT NULL CHECK (reading_count >= 0),
        timestamp TIME (6) NOT NULL,
        readings SMALLINT[][] NOT NULL, 
        PRIMARY KEY (subject_id, gesture, repetition, reading_count)
    )
    """,
    'calibration': """
    CREATE TABLE calibration (
        subject_id INTEGER NOT NULL REFERENCES subjects (subject_id) ON DELETE CASCADE,
        calibration_gesture VARCHAR(32) NOT NULL,
        calibration_iterations SMALLINT NOT NULL CHECK (calibration_iterations >= 0 and calibration_iterations <= 400),
        calibration_values SMALLINT[] NOT NULL,
        PRIMARY KEY (subject_id, calibration_gesture)
    )
    """,
}

# region INSERT handling


def _insert(sql: str, data, returning: bool = False) -> list:
    """ 
    Insert data into table.
    """
    conn = None
    returned = None
    try:
        conn = _connect()
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        # print(str((*data,)))
        cur.execute(sql, (*data,))

        # get the generated id back
        if returning:
            returned = cur.fetchall()

        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()

    return returned


def insert_subject(subject) -> int:
    """ 
    Insert a new subject into the subjects table. 
    """
    columns, values = subject.keys(), subject.values()
    returning = f""

    sql = f"INSERT INTO subjects({','.join(columns)}) VALUES ({','.join(['%s' for _ in values])}) RETURNING subject_id;"

    subject_id = _insert(sql, values, returning=True)[0][0]

    print(
        f"Inserted {values} for into 'subjects'. Received {subject_id} back.")
    return subject_id


def insert_calibration(calibration) -> None:
    """ 
    Insert a new calibration into the calibration table.
    """
    columns, values = calibration.keys(), calibration.values()

    sql = f"""INSERT INTO calibration({','.join(columns)}) VALUES ({','.join(['%s' for _ in values])}) 
    ON CONFLICT (subject_id, calibration_gesture) DO UPDATE 
    SET calibration_iterations = Excluded.calibration_iterations, calibration_values = Excluded.calibration_values
    ;"""

    _insert(sql, values)

    print(f"Inserted {values} for into 'calibration'.")
    return


def insert_data(data) -> None:
    """ 
    Insert new data point into the data table.
    """
    columns, values = data.keys(), data.values()

    sql = f"""INSERT INTO data({','.join(columns)}) VALUES ({','.join(['%s' for _ in values])}) 
    ON CONFLICT (subject_id, gesture, repetition, reading_count) DO NOTHING
    ;"""

    _insert(sql, values)

    #print(f"Inserted {values} for into 'data'.")
    return


def _insert_many(sql, values) -> None:
    """ 
    Insert lots of data into table.
    """
    conn = None
    try:
        conn = _connect()
        # create a new cursor
        cur = conn.cursor()
        # execute the sql statement
        execute_values(cur, sql, values)

        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()
    return


def insert_data_repetition(repetition_data) -> None:
    """
    Insert all data from repetition.
    """
    start = time.perf_counter()
    columns = repetition_data[0].keys()
    values = [(*x.values(),) for x in repetition_data]
    sql = f"""INSERT INTO data({','.join(columns)}) VALUES %s
    ON CONFLICT (subject_id, gesture, repetition, reading_count) DO NOTHING
    ;"""
    _insert_many(sql, values)
    elapsed = time.perf_counter() - start
    print(f'Inserted {len(values)} data points in {elapsed} seconds')
# endregion

# region DELETE handling


def _delete(table: str, condition: str, args) -> int:
    """ 
    Delete rows from table where condition matches.
    """
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        sql = f"DELETE FROM {table} WHERE {condition};"
        # execute the DELETE  statement
        cur.execute(sql, args)
        # get the number of updated rows
        rows_deleted = cur.rowcount
        print(f"Deleted {rows_deleted} row(s).")
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


def delete_subject(subject_id) -> int:
    """ 
    Delete subject with matching id from subjects table.
    """
    return _delete("subjects", "(subject_id = %s)", (subject_id,))


def delete_calibration(subject_id, gesture) -> int:
    """
    Delete calibration.
    """
    return _delete("calibration", "(subject_id = %s AND calibration_gesture = %s)",
                   (subject_id, gesture,))


def delete_data(subject_id, gesture, repetition) -> int:
    """
    Delete all subjects data for relevant gesture and repetition.
    """
    return _delete("data", "(subject_id = %s AND gesture = %s AND repetition = %s)",
                   (subject_id, gesture, repetition,))


def clear_existing_data(metadata) -> int:
    """
    Remove data with matching metadata.
    """
    rows_deleted = 0
    if exists('data', metadata):
        rows_deleted = delete_data(
            subject_id=metadata['subject_id'], gesture=metadata['gesture'],  repetition=metadata['repetition'])
        print(f"Deleted {rows_deleted} rows from data for {metadata}")
    return rows_deleted
# endregion

# region SELECT handling


def get_all(table) -> list:
    """ 
    Get all rows from table.
    """
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

def get_where(table, context) -> list:
    """ 
    Get all rows from table matching context.
    """
    columns, values = context.keys(), context.values()
    where = ' AND '.join(['='.join([column, '%s']) for column in columns])
    sql = f"SELECT * FROM {table} WHERE ({where});"
    result = None
    conn = None
    try:
        conn = _connect()
        # create a new cursor
        cur = conn.cursor()
        # execute the sql statement
        cur.execute(sql, (*values,))
        # get the result back
        result = cur.fetchall()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()

    return result

def exists(table, context) -> bool:
    """
    Checks if table contains any rows matching the context
    """
    columns, values = context.keys(), context.values()
    where = ' AND '.join(['='.join([column, '%s']) for column in columns])
    sql = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE ({where}));"
    exists = False
    conn = None
    try:
        conn = _connect()
        # create a new cursor
        cur = conn.cursor()
        # execute the sql statement
        cur.execute(sql, (*values,))
        # get the result back
        exists = cur.fetchone()[0]
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise error
    finally:
        if conn is not None:
            conn.close()

    return exists
# endregion

# region Utility


def _config(filename='database.ini', section='postgresql') -> dict:
    """ 
    Read and parse database configuration from file or flask config.
    """
    db = {}

    if current_app:
        db = current_app.config.get('DATABASE', {})
    else:
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(filename)

        # get section, default to postgresql
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]

    if not db:
        raise Exception('Database configuration not found')

    return db


def setup(schema=SCHEMA):
    """ 
    Create tables in the PostgreSQL database.
    """
    conn = None
    try:
        conn = _connect()
        cur = conn.cursor()
        # create table one by one
        for command in schema.values():
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


def _connect(config={}):
    """ 
    Connect to the database server.
    """
    if not config:
        config = _config()

    conn = None
    try:
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**config)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error
    return conn


def reset(table: str, cascade: bool = False) -> None:
    """ 
    Drop table and recreate.
    """
    if table in SCHEMA.keys():
        conn = None
        try:
            conn = _connect()
            cur = conn.cursor()
            sql = f"DROP TABLE IF EXISTS {table}{' CASCADE' if cascade else ''};"
            cur.execute(sql)
            conn.commit()
            cur.close()
            print(f"Dropped table '{table}'")

            cur = conn.cursor()
            cur.execute(SCHEMA[table])
            print(f"Recreated table '{table}'")
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    else:
        print(f"Error: '{table}' not in schema.")


def reset_all() -> None:
    """ 
    Drop all tables and recreate.
    """
    print('Resetting everything')

    reset('calibration')
    reset('data')
    reset('subjects', cascade=True)

    print('Reset done')
# endregion

#region Dummy data insertion
def _insert_dummy_subject():
    subject = {
        'subject_gender': 'm',
        'subject_age': 100,
        'subject_fitness': 1,
        'subject_handedness': 'r',
        'subject_impairment': 'n',
        'subject_wrist_circumference': 20,
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

def _insert_dummy_data_repetitions(sid, n=10) -> None:
    print('Generating data')
    
    for i in range(5):
        data = []
        for j in range(5):
            for k in range(n):
                data.append({
                    'subject_id': sid,
                    'gesture': f"dummy_gesture_{j}",
                    'repetition': i,
                    'reading_count': k,
                    'readings': [random.randint(5, 165) for _ in range(8)] + [random.randint(5, 165) for _ in range(7)],
                    'timestamp': time.strftime("%H:%M:%S.{}".format(repr(time.time()).split('.')[1]), time.localtime(time.time()))
                })
        insert_data_repetition(data)
    print('Data inserted')


def _insert_dummies(n=1):
    for _ in range(n):
        sid = _insert_dummy_subject()
        print(f"sid = {sid}")
        _insert_dummy_calibrations(sid)
        _insert_dummy_data_repetitions(sid)
# endregion

if __name__ == "__main__":
    setup()