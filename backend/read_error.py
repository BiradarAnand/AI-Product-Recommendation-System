import re

with open("error.html", encoding="utf-8") as f:
    html = f.read()

text = re.sub(r"<[^>]+>", " ", html)
text = re.sub(r"\s+", " ", text)

# Write the last 3000 chars to a separate txt file
with open("error_clean.txt", "w", encoding="utf-8") as out:
    out.write(text[-3000:])

print("Done — check error_clean.txt")
