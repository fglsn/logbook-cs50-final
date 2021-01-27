from flask import Flask

app = Flask(__name__)

@app.route('/login')
def login():
    return 'Hello, this is login response for now'