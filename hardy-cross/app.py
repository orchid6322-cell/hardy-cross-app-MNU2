"""하디-크로스 관망해석 웹 UI."""

from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

from hardy_cross.engine import network_from_dict, solve
from hardy_cross.examples import example_dict
from hardy_cross.friction import Formula

app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/example")
def api_example():
    return jsonify(example_dict())


@app.post("/api/solve")
def api_solve():
    data = request.get_json(force=True)
    try:
        network = network_from_dict(data)
        result = solve(
            network,
            tolerance=float(data.get("tolerance", 1e-6)),
            max_iter=int(data.get("max_iter", 80)),
        )
        payload = result.to_dict()
        payload["nodes"] = data.get("nodes", [])
        payload["loops"] = data.get("loops", [])
        return jsonify(payload)
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/formulas")
def api_formulas():
    return jsonify(
        [
            {"id": Formula.HAZEN_WILLIAMS.value, "label": "Hazen-Williams (n = 1.852)"},
            {"id": Formula.DARCY_WEISBACH.value, "label": "Darcy-Weisbach (n = 2)"},
        ]
    )


if __name__ == "__main__":
    print("하디-크로스 관망해석: http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=True)
