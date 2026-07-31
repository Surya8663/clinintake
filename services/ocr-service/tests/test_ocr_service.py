import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from src.main import app

client = TestClient(app)

def test_ocr_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ocr_image_upload_spatial_bbox():
    # Create sample synthetic test image
    img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Patient: Jane Doe", fill=(0, 0, 0))
    d.text((10, 50), "Diagnosis: Hypertension", fill=(0, 0, 0))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    response = client.post(
        "/ocr/process",
        files={"file": ("test_clinical_doc.png", img_byte_arr, "image/png")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert len(data["pages"]) == 1
    
    page = data["pages"][0]
    assert page["width"] == 400
    assert page["height"] == 200
    assert len(page["words"]) > 0
    
    # Verify real spatial bounding boxes exist
    first_word = page["words"][0]
    assert "bbox" in first_word
    bbox = first_word["bbox"]
    assert "x_min" in bbox and "y_min" in bbox and "x_max" in bbox and "y_max" in bbox
    assert bbox["x_max"] >= bbox["x_min"]
    assert bbox["y_max"] >= bbox["y_min"]
