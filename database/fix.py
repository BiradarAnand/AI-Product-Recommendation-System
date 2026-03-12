import csv

input_file = "ecommerce_products_300.csv"        # your current dataset
output_file = "products_fixed.csv" # new dataset

rows = []

with open(input_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        # assuming image URL is column index 8
        row[8] = f"https://picsum.photos/seed/product{i}/600"
        rows.append(row)

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print("✅ Image URLs fixed. New file created:", output_file)