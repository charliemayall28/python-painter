from flask import Flask
from flask import request, jsonify
from flask_cors import CORS, cross_origin
from pathlib import Path
import json
from maker import Maker

ROOT = Path(__file__).parent
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config["CORS_HEADERS"] = "Content-Type"


@app.route("/submit", methods=["POST"])
@cross_origin()
def submit():
    """
    This function is called when the user submits a new program.
    It returns the result of the program.
    """
    data = request.get_json()
    maker = Maker()
    maker.loadArrayJSON(data)
    commandString = maker.dump()
    with open(ROOT / "test.json", "w") as w:
        json.dump(data, w)

    return jsonify({"commands": commandString})


# run a server
if __name__ == "__main__":
    app.run(port=5000)
