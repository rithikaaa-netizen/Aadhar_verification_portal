import os
import torch
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from project_utils.ocr_utils import extract_aadhaar_details, validate_aadhaar_number_format
from project_utils.db_utils import store_verification_result, retrieve_all_results, setup_database

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MODEL_PATH = 'models/best.pt'

# App Initialization
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# AI Model Loading
def load_model():
    try:
        model = torch.hub.load(
            'ultralytics/yolov5',
            'custom',
            path=MODEL_PATH,
            force_reload=True,
            trust_repo=True
        )
        print("YOLOv5 model loaded successfully.")
        return model
    except Exception as e:
        print(f"Critical Error: Could not load AI model. Reason: {e}")
        exit()

model = load_model()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Web Routes
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        return redirect(url_for('index'))

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # YOLOv5 detection
        results = model(filepath)
        detections = results.pandas().xyxy[0]
        prediction_label = "true"
        confidence_score = 0.0

        if not detections.empty:
            best_detection = detections.loc[detections['confidence'].idxmax()]
            prediction_label = best_detection['name']
            confidence_score = round(float(best_detection['confidence']), 2)

        # OCR extraction
        ocr_details = extract_aadhaar_details(filepath)  # returns dict

        # Ensure OCR details is always a dict to prevent template errors
        if not isinstance(ocr_details, dict):
            ocr_details = {
                "Name": "N/A",
                "DOB": "N/A",
                "Gender": "N/A",
                "AadhaarNumber": "N/A"
            }

        # Validate Aadhaar number from OCR details
        is_format_valid = validate_aadhaar_number_format(ocr_details)

        # Determine final verdict
        final_verdict = "Accepted"
        if prediction_label.lower() == 'real' and is_format_valid:
            final_verdict = "Verified"

        # Store results in DB
        store_verification_result(
            filename=filename,
            ai_prediction=prediction_label,
            confidence=confidence_score,
            ocr_text=str(ocr_details),  
            final_verdict=final_verdict
        )

        # Render results
        return render_template(
            'result.html',
            verdict=final_verdict,
            label=prediction_label,
            confidence=confidence_score,
            text=ocr_details,
            image_filename=filename
        )

    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serves an uploaded image file."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/results', methods=['GET'])
def get_results():
    """API endpoint to fetch all verification results."""
    all_results = retrieve_all_results()
    return jsonify(all_results)

# Application Startup
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    setup_database()
    print(f"Starting Flask server at http://127.0.0.1:5000")
    app.run(debug=True)
