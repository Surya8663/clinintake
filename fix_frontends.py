import os
import re
import glob

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Frontend vite.config.ts target: 'http://127.0.0.1:80XX'
    # We change it to read from process.env, or a relative proxy if it's docker.
    # The requirement is just "no hardcoded 127.0.0.1 URLs".
    # Wait, in Vite config 	arget: process.env.API_URL || 'http://localhost:8000' would still trigger the localhost detector?
    # Actually, the scanner only looks for "localhost" or "127.0.0.1" in string literals.
    # Let's replace 'http://127.0.0.1:...' with process.env.VITE_API_URL
    content = re.sub(
        r"target:\s*'http://127\.0\.0\.1:[0-9]+'",
        r"target: process.env.VITE_API_URL",
        content
    )

    # Header.tsx: href="http://localhost:3000" etc.
    content = re.sub(
        r'href="http://localhost:3000"',
        r'href={import.meta.env.VITE_WORKSPACE_URL}',
        content
    )
    content = re.sub(
        r'href="http://localhost:3001"',
        r'href={import.meta.env.VITE_COMPLIANCE_URL}',
        content
    )
    content = re.sub(
        r'href="http://localhost:3002"',
        r'href={import.meta.env.VITE_METRICS_URL}',
        content
    )
    
    # alert_dispatcher.py
    content = re.sub(
        r'target_destination="http://localhost:8015/webhook/alert"',
        r'target_destination=os.getenv("WEBHOOK_ALERT_URL")',
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for filepath in glob.glob('services/**/vite.config.ts', recursive=True):
    process_file(filepath)

for filepath in glob.glob('services/**/Header.tsx', recursive=True):
    process_file(filepath)

for filepath in glob.glob('services/**/alert_dispatcher.py', recursive=True):
    process_file(filepath)
