from flask import Flask
import allinone

app = Flask(__name__)

@app.route('/')
def hello_world():
    return allinone

if __name__ == '__main__':
    app.run()
