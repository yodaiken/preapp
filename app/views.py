from . import app

@app.route('/')
def hp():
    return 'Hello, world!', 200, {'Content-Type': 'text/plain'}