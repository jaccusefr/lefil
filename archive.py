import json, os

D = "archive"

def main():
    data = json.load(open("data.json", encoding="utf-8"))
    os.makedirs(D, exist_ok=True)
    by = {}
    for i in data["items"]:
        by.setdefault(i["date"][:7], []).append(i)
    for m, items in sorted(by.items()):
        path = f"{D}/{m}.jsonl"
        seen = set()
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line:
                    try: seen.add(json.loads(line)["link"])
                    except Exception: pass
        new = sorted((i for i in items if i["link"] not in seen), key=lambda i: i["date"])
        if new:
            with open(path, "a", encoding="utf-8") as f:
                for i in new:
                    f.write(json.dumps(i, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(m, ":", len(new), "nouveaux articles")
    months = sorted((f[:-6] for f in os.listdir(D) if f.endswith(".jsonl")), reverse=True)
    json.dump({"months": months}, open(f"{D}/index.json", "w"))

if __name__ == "__main__":
    main()
