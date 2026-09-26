import csv
import mysql.connector
import re
import json

db_config = {
    'host': 'localhost',
    'port': 3305,
    'user': 'root',
    'password': 'Passwordmysql',
    'database': 'myecomerce'
}

def clean_price(price_str):
    if not price_str or not isinstance(price_str, str):
        return None
    # Remove everything except digits and decimal point
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return None

def main():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get target products
        cursor.execute("SELECT id, name FROM products WHERE category = 'Electronics' AND (price = 0 OR price IS NULL)")
        db_products = cursor.fetchall()
        db_product_map = {p['name']: p['id'] for p in db_products}
        
        updated_count = 0
        unmatched_names = []
        sample_updates = []
        
        csv_file = r'C:/Users/birad/Desktop/LLM - AI/Desc/All Electronics.csv'
        
        with open(csv_file, mode='r', encoding='utf-8', errors='replace') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('name')
                if name in db_product_map:
                    discount_price = row.get('discount_price', '').strip()
                    actual_price = row.get('actual_price', '').strip()
                    
                    price_str = discount_price if discount_price else actual_price
                    price = clean_price(price_str)
                    
                    if price is not None:
                        product_id = db_product_map[name]
                        cursor.execute("UPDATE products SET price = %s WHERE id = %s", (price, product_id))
                        updated_count += 1
                        if len(sample_updates) < 10:
                            sample_updates.append({"name": name, "price": price})
                        # Remove from map so we don't update twice or list as still 0/NULL
                        del db_product_map[name]
                else:
                    unmatched_names.append(name)
                    
        conn.commit()
        
        # Any items left in db_product_map are still 0/NULL
        still_zero_null_count = len(db_product_map)
        
        # Save output for parsing
        result = {
            "updated": updated_count,
            "still_zero_null": still_zero_null_count,
            "unmatched_sample": unmatched_names[:20],
            "unmatched_total": len(unmatched_names),
            "sample_updates": sample_updates
        }
        
        with open('update_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    main()
