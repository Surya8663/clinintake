from pydantic import BaseModel, Field
from typing import List, Optional

class BoundingBox(BaseModel):
    x_min: int = Field(..., description="X minimum coordinate (left)")
    y_min: int = Field(..., description="Y minimum coordinate (top)")
    x_max: int = Field(..., description="X maximum coordinate (right)")
    y_max: int = Field(..., description="Y maximum coordinate (bottom)")

class OCRWord(BaseModel):
    text: str
    confidence: float
    bbox: BoundingBox
    page_number: int

class OCRLine(BaseModel):
    line_text: str
    bbox: BoundingBox
    words: List[OCRWord] = []

class OCRPage(BaseModel):
    page_number: int
    width: int
    height: int
    text: str
    words: List[OCRWord] = []
    lines: List[OCRLine] = []

class OCRResponse(BaseModel):
    document_id: str
    pages: List[OCRPage]
    full_text: str
    engine_used: str
