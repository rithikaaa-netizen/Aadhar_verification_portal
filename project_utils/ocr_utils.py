import pytesseract
import cv2
import re
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
def preprocess_image(image_path: str):
    """Simple preprocessing: grayscale + thresholding"""
    img = cv2.imread(image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh
def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using Tesseract OCR"""
    img = preprocess_image(image_path)
    if img is None:
        return ""
    if img.shape[1] < 1000:
        scale = 1000 / img.shape[1]
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    text = pytesseract.image_to_string(img, lang="eng", config="--oem 3 --psm 6")
    return text.strip()
def extract_aadhaar_details(image_path: str) -> dict:
    """Extract Name, DOB, Gender, AadhaarNumber from Aadhaar card"""
    raw_text = extract_text_from_image(image_path)
    details = {"Name": "N/A", "DOB": "N/A", "Gender": "N/A", "AadhaarNumber": "N/A"}
    if not raw_text:
        return details
    # Aadhaar number
    aadhaar_match = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', raw_text)
    if aadhaar_match:
        details["AadhaarNumber"] = aadhaar_match.group().replace(" ", "")
    # Gender
    gender_match = re.search(r'\b(Male|Female|M|F)\b', raw_text, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group()
        if gender.upper() == "M":
            gender = "Male"
        elif gender.upper() == "F":
            gender = "Female"
        details["Gender"] = gender
    # DOB
    dob_match = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', raw_text)
    if dob_match:
        details["DOB"] = dob_match.group()
    # Simple Name
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    for line in lines:
        if all(k not in line.lower() for k in ["government", "india", "aadhaar"]):
            if len(line.split()) >= 1: 
                details["Name"] = line
                break
    return details
def validate_aadhaar_number_format(details: dict) -> bool:
    """Check if Aadhaar number is valid format (12 digits)"""
    aadhaar_number = details.get("AadhaarNumber", "").replace(" ", "")
    return bool(re.fullmatch(r'\d{12}', aadhaar_number))
