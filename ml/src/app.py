from flask import Flask, request, jsonify

from ml_service import predict_health

app = Flask(__name__)


# ============================================
# HOME ROUTE
# ============================================

@app.route("/")
def home():

    return {
        "message": "LivestockOS ML API Running"
    }


# ============================================
# PREDICTION ROUTE
# ============================================

@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    result = predict_health(data)

    return jsonify(result)


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":

    app.run(debug=True)