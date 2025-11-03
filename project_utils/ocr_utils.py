import pytesseract
import cv2
import re
import numpy as np

# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess_image(image_path: str):
    """Optimized preprocessing for Aadhaar cards"""
    img = cv2.imread(image_path)
    if img is None:
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Enhance contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.8, beta=10)

    # Adaptive threshold to handle uneven brightness
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 31, 12
    )

    # Slight morphological closing to connect broken digits
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return cleaned

def extract_text_from_image(image_path: str) -> str:
    """Extracts text using English + Hindi OCR and cleaning"""
    img = preprocess_image(image_path)
    if img is None:
        return ""

    # Resize for better OCR accuracy
    if img.shape[1] < 1300:
        scale = 1300 / img.shape[1]
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # OCR configuration
    config = (
        "--oem 3 --psm 6 "
        "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 /-:"
    )

    # Use English + Hindi (helps with bilingual cards)
    text = pytesseract.image_to_string(img, lang="eng+hin", config=config)

    # Basic cleaning: remove symbols, merge spaces
    text = re.sub(r'[^A-Za-z0-9:/\-\n ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_aadhaar_details(image_path: str) -> dict:
    """Extract Name, DOB, Gender, AadhaarNumber from Aadhaar card"""
    raw_text = extract_text_from_image(image_path)
    details = {"Name": "N/A", "DOB": "N/A", "Gender": "N/A", "AadhaarNumber": "N/A"}

    if not raw_text:
        return details

    # Aadhaar number (robust pattern)
    aadhaar_match = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', raw_text)
    if aadhaar_match:
        details["AadhaarNumber"] = aadhaar_match.group().replace(" ", "")

    # DOB or Year of Birth
    dob_match = re.search(r'(DOB[: ]*|Date[: ]*of[: ]*Birth[: ]*)(\d{2}[/-]\d{2}[/-]\d{4})', raw_text, re.IGNORECASE)
    if dob_match:
        details["DOB"] = dob_match.group(2)
    else:
        fallback_dob = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', raw_text)
        if fallback_dob:
            details["DOB"] = fallback_dob.group()

    # Gender
    gender_match = re.search(r'\b(MALE|FEMALE|M|F)\b', raw_text, re.IGNORECASE)
    if gender_match:
        g = gender_match.group().upper()
        details["Gender"] = "Male" if g in ["M", "MALE"] else "Female"

    # Name detection (line before DOB or Gender)
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    for i, line in enumerate(lines):
        if any(x in line.lower() for x in ["dob", "birth", "male", "female"]):
            if i > 0:
                name_candidate = lines[i - 1].strip()
                if not any(k in name_candidate.lower() for k in ["india", "aadhaar", "uidai", "government"]):
                    details["Name"] = name_candidate
            break

    return details

def validate_aadhaar_number_format(details: dict) -> bool:
    """Validate Aadhaar number format (12 digits)"""
    aadhaar_number = details.get("AadhaarNumber", "").replace(" ", "")
    return bool(re.fullmatch(r'\d{12}', aadhaar_number))

if __name__ == "__main__":
    image_path = "Screenshot 2025-10-21 190415.png"  # update this if needed
    print("=== OCR Raw Text ===")
    print(extract_text_from_image(image_path))

    details = extract_aadhaar_details(image_path)
    print("\n=== Extracted Details ===")
    print(details)
    print("\nValid Aadhaar format:", validate_aadhaar_number_format(details))
