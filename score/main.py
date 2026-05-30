from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import os

# Base directory for this module (score/)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Create the Flask app and point Jinja to the local `h` templates folder
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "h"))

# Load trained model (use an absolute path to avoid cwd issues)
model_path = os.path.join(BASE_DIR, "interview_model.pkl")
model = joblib.load(model_path)


@app.route("/")
def home():
    return render_template("home.html")


# Prediction API
@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    features = np.array([[
        data["text_score"],
        data["audio_score"],
        data["video_score"],
        data["image_score"],
        data["filler_rate"],
        data["wpm"],
        data["eye_contact_pct"],
        data["posture_score"]
    ]])

    prediction = model.predict(features)[0]

    return jsonify({
        "predicted_score": round(float(prediction), 2)
    })


if __name__ == "__main__":
    app.run(debug=True)