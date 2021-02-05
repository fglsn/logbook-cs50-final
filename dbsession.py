from collections.abc import MutableMapping
from uuid import uuid4

from flask.sessions import SessionInterface
from flask.sessions import SessionMixin

from db import execute, fetch_one


class Session(SessionMixin, MutableMapping):
    def __init__(self, id, **kwargs):
        self.store = dict()
        self.id = id
        self.user_id = kwargs.get('user_id')
        self.modified = False
        kwargs.pop('user_id', None)
        self.update(dict(**kwargs))

    def __getitem__(self, key):
        if key == 'user_id':
            return self.user_id
        return self.store[key]

    def __setitem__(self, key, value):
        if key == 'user_id':
            self.modified = self.user_id != value
            self.user_id = value
            return
        if self.store[key] != value:
            self.modified = True
            self.store[key] = value

    def __delitem__(self, key):
        if key == 'user_id':
            if self.user_id is None:
                raise KeyError(f'Key {key} not found')
            self.user_id = None
            return
        del self.store[key]

    def __iter__(self):
        if self.user_id is not None:
            return iter(self.store + {'user_id': self.user_id})
        return iter(self.store)
    
    def __len__(self):
        return len(self.store) + 1 if self.user_id is not None else 0

    def clear(self):
        print(f'clear session {self.id}')
        self.store.clear()
        self.user_id = None
        self.id = str(uuid4())


class DbSessionInterface(SessionInterface):
    def open_session(self, app, request):
        session_id = request.cookies.get("session_id")
        print(f'opening session {session_id}')
        if session_id:
            db_session = fetch_one('SELECT user_id, created_at FROM sessions WHERE id = %(id)s', id=session_id)
            # todo: check created_at
            if db_session:
                return Session(id=session_id, user_id=db_session['user_id'])
        else:
            session_id = str(uuid4())
        return Session(id=session_id)

    def save_session(self, app, session, response):
        print(f'saving session {session["user_id"]} {session.id}')
        if session['user_id'] is not None:
            if session.modified:
                execute('''INSERT INTO sessions (id, user_id) VALUES(%(id)s, %(user_id)s) 
                            ON CONFLICT (id) 
                            DO UPDATE SET user_id = %(user_id)s''', id=session.id, user_id=session['user_id'])
            response.set_cookie('session_id', session.id)
        else:
            execute('DELETE FROM sessions WHERE id = %(id)s', id=session.id)
            response.set_cookie('session_id', '', expires=0)
