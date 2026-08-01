import glob
import re


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # default="localhost" -> ...
    content = re.sub(r'default="localhost[^"]*"', r"...", content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


for filepath in glob.glob("services/**/config.py", recursive=True):
    process_file(filepath)
