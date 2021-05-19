import os
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

# Some usage example
# result = fetch_one("select id, name from squanch where name like %(pattern)s", pattern='big%')
# print(result)
# result_many = fetch("select * from squanch")
# print('many', result_many)
# for i in range(0, 4):
#     execute('insert into squanch(name) values (%(name)s)', name=f'random squanch {randint(0, 100)}')
# returning_result = fetch_one('insert into squanch(name) values (%(name)s) returning id', name=f'returning squanch {randint(100, 200)}')
# print(returning_result)
# for sq in result_many:
#     print(f'{sq["id"]} {sq["name"]}')
# return str(result_many)

__POOL = None


def __get_pool():
    global __POOL
    if not __POOL:
        db_url = os.environ.get('DATABASE_URL', 'postgres://fglsn:@localhost:5432/drivelog')
        __POOL = ThreadedConnectionPool(1, 10, db_url)
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
def get_db_cursor(): 
    with get_db_connection() as connection:
      cursor = connection.cursor(
                  cursor_factory=RealDictCursor)
      try:
          yield cursor 
          connection.commit() 
      finally: 
          cursor.close()


def fetch(query_text, **kwargs):
    with get_db_cursor() as cursor:
        cursor.execute(query_text, kwargs)
        return cursor.fetchall()


def fetch_one(query_text, **kwargs):
    with get_db_cursor() as cursor:
        cursor.execute(query_text, kwargs)
        return cursor.fetchone()


def execute(query_text, **kwargs):
    with get_db_cursor() as cursor:
        cursor.execute(query_text, kwargs)
