__author__ = 'robdefeo'
import sys

from flask import Flask

app = Flask(__name__)

from detect.container import Container
container = Container()
from detect.vocab import Vocab

vocab = Vocab(container=container)
vocab.generate()
vocab.load()

from detect.vocab import alias_data
from detect.views import mod_detect
app.register_blueprint(mod_detect)

if __name__ == "__main__":
    from detect.settings import PORT
    # Run a test server.
    app.run(host='0.0.0.0', port=PORT, debug=True)