import os
import re
import glob

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace hardcoded localhost in Field defaults with Field(...)
    # e.g., url: str = Field(default="http://localhost:...") -> url: str = Field(...)
    content = re.sub(
        r'(:\s*str\s*=\s*Field\(\s*)default="http://localhost:[^"]+"(\s*\))',
        r'\1...\2',
        content
    )
    # Also if there are description fields, we just remove the default
    content = re.sub(
        r'default="http://localhost:[^"]+",',
        r'... ,',
        content
    )

    # For os.getenv("...", "http://localhost:...")
    content = re.sub(
        r'os\.getenv\("([^"]+)", "http://localhost:[^"]+"\)',
        r'os.getenv("\1")',
        content
    )

    # For CONFIDENCE_THRESHOLD
    content = re.sub(
        r'CONFIDENCE_THRESHOLD:\s*float\s*=\s*Field\(default=[0-9.]+\)',
        r'CONFIDENCE_THRESHOLD: float = Field(...)',
        content
    )
    content = re.sub(
        r'confidence_threshold:\s*float\s*=\s*Field\(default=[0-9.]+\)',
        r'confidence_threshold: float = Field(...)',
        content
    )

    # For service_name duplicate env vars - we can just use ClassVar
    # but some files don't have ClassVar imported. Let's just remove the default 
    # and make it required, but that breaks startup if not in env.
    # Actually, we can use Field(..., alias="SERVICE_NAME")? No.
    # Let's add alias="SERVICE_NAME_xyz" to make it unique per service.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for filepath in glob.glob('services/**/config.py', recursive=True):
    process_file(filepath)

for filepath in glob.glob('services/**/jwt_verifier.py', recursive=True):
    process_file(filepath)
    
