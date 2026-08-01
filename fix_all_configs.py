import glob
import re


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if "default=" in line and any(k in line.lower() for k in ["secret", "key", "password", "url", "id", "database", "kafka", "qdrant", "lyzr", "ehr"]):
            line = re.sub(r'default="[^"]*"', "...", line)
            line = re.sub(r"default='[^']*'", "...", line)
        new_lines.append(line)

    new_content = "\n".join(new_lines)
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filepath}")


for filepath in glob.glob("services/**/config.py", recursive=True):
    process_file(filepath)
