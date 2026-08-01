import glob
import json

for filepath in glob.glob("services/**/frontend/package.json", recursive=True):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    if "scripts" not in data:
        data["scripts"] = {}
    data["scripts"]["lint"] = "tsc --noEmit"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Added lint to {filepath}")
