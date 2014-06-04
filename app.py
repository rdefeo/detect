import preProcess
import vocab
from flask import Flask, jsonify, request
from bson.objectid import ObjectId

app = Flask(__name__)

data = {}
@app.route('/vocab/generate/', methods = ['POST'])
def vocab_generate():
  vocab.generate()
  resp = jsonify({
    "status": "ok"
  })
  resp.status_code = 200
  return resp

@app.route('/vocab/load/', methods = ['POST'])
def vocab_load():
  data = vocab.load()
  resp = jsonify({
    "status": "ok"
  })
  resp.status_code = 200
  return resp

@app.route('/', methods = ['GET'])
def api_root():
  q = request.args.get("q")
  sessionID = request.args.get("sessionID")
  detectionID = ObjectId()

  print "app=detection,module=app,function=get,detectionId=%s,sessionID=%s,q=%s" % (detectionID, sessionID, q)
  if not q or not sessionID:
    resp = jsonify({
      "status": "error",
      "message": "missing param(s)"
    })
    resp.status_code = 412
    return resp
  else:
    preprocessResult = preProcess.tag(q)
    resp = jsonify(preprocessResult)
    resp.status_code = 200
    return resp

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
    # print "app=detection,port=%d,mode=%s,action=started", port, app.settings.env)