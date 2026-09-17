import os

frontend_src = r"c:\Users\birad\Desktop\Ecommerce\AI-Product-Recommendation-System\frontend\src"

def replace_api_url():
    target = "https://ai-product-recommendation-system-by60.onrender.com"
    replacement = "http://localhost:5000"
    
    count = 0
    for root, dirs, files in os.walk(frontend_src):
        for file in files:
            if file.endswith(('.jsx', '.js')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if target in content:
                    content = content.replace(target, replacement)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated {file}")
                    count += 1
                    
    print(f"Total files updated: {count}")

if __name__ == "__main__":
    replace_api_url()
