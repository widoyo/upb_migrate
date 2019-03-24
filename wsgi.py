import bjoern as app
from main import app as my_app

if __name__ == '__main__':
    app.run(my_app, '0.0.0.0', 5000)
