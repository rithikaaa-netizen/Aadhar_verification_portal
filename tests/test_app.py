import pytest
from Aadhar_card_fraud_detection_main.app import app
from project_utils.ocr_utils import validate_aadhaar_number_format
@pytest.fixture
def client():
    with app.test_client() as client:
        yield client
def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Aadhaar Verification System" in response.data
@pytest.mark.parametrize("input_text, expected", [
    # Positive cases
    ("My Aadhaar number is 1234 5678 9012.", True),
    ("Here is the number: 123456789012, thanks.", True),
    ("Some random text then 9876 5432 1098 and more text.", True),
    ("987654321098 at the start", True),
    
    # Negative cases
    ("This number is too short: 1234 5678 901", False),
    ("This number is too long: 1234 5678 9012 3", False),
    ("12345678901", False),
    ("Contains letters 1234 5678 901a", False),
    ("No number here.", False),
    ("", False)
])
def test_validate_aadhaar_number_format(input_text, expected):
    assert validate_aadhaar_number_format(input_text) == expected