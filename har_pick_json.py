import json
import re

HAR_FILE = "network.har"

def is_json(mime: str) -> bool:
    mime = (mime or "").lower()
    return "application/json" in mime or mime.endswith("+json")

def main():
    with open(HAR_FILE, "r", encoding="utf-8") as f:
        har = json.load(f)

    entries = har.get("log", {}).get("entries", [])
    hits = []

    for e in entries:
        req = e.get("request", {})
        res = e.get("response", {})
        url = req.get("url", "")
        status = res.get("status", 0)

        mime = ""
        content = (res.get("content") or {})
        mime = content.get("mimeType", "")

        if status == 200 and is_json(mime):
            hits.append(url)

    print("=== 200 JSON candidates ===")
    for u in hits[:50]:
        print(u)

    print(f"\nTotal 200 JSON: {len(hits)}")

if __name__ == "__main__":
    main()
