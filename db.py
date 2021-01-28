from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

__POOL = None


def __get_pool():
    global __POOL
    if not __POOL:
        __POOL = ThreadedConnectionPool(1, 10, database='drivelog',
                                                user='fglsn',
                                                password='',
                                                host='localhost',
                                                port=5432)
    return __POOL


@contextmanager
def get_db_connection():
    pool = __get_pool()
    try: 
        connection = pool.getconn() 
        yield connection 
    finally: 
        pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False): 
    with get_db_connection() as connection:
      cursor = connection.cursor(
                  cursor_factory=RealDictCursor)
      try: 
          yield cursor 
          if commit: 
              connection.commit() 
      finally: 
          cursor.close()