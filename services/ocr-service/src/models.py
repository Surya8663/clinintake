
from pydantic import BaseModel, Field


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
    words: list[OCRWord] = []

class OCRPage(BaseModel):
    page_number: int
    width: int
    height: int
    text: str
    words: list[OCRWord] = []
    lines: list[OCRLine] = []

class OCRResponse(BaseModel):
    document_id: str
    pages: list[OCRPage]
    full_text: str
    engine_used: str
