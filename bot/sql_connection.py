import pandas as pd
from sqlalchemy import create_engine
import re


# Connection string
connection_string = 'mssql+pyodbc://localhost/Dbo_eTicaret?driver=ODBC+Driver+17+for+SQL+Server'

# Create engine
engine = create_engine(connection_string)

# SQL query
query = 'SELECT * FROM Products'  # Modify as per your query

# Execute query and get result in a DataFrame
df = pd.read_sql(query, engine)

# Display results
print(df)


def get_user_query(user_input):
    # Kullanıcıdan gelen isteği basit bir şekilde analiz etme
    color_match = re.search(r'\b(kırmızı|mavi|yeşil|sarı|beyaz|uzay gri|rose|pembe|siyah|beyaz|kahverengi)\b', user_input, re.IGNORECASE)
    product_type_match = re.search(r'\b(elbise|bilgisayar|telefon)\b', user_input, re.IGNORECASE)
    ram_match = re.search(r'\b(\d{2})\s*GB\b', user_input, re.IGNORECASE)
    
    color = color_match.group(0) if color_match else None
    product_type = product_type_match.group(0) if product_type_match else None
    ram = ram_match.group(1) if ram_match else None
    
    return color, product_type, ram

# Kullanıcıdan gelen örnek input
user_input = "kırmızı bir elbise istiyorum"

# Kullanıcıdan gelen input ile sorgu bilgilerini çıkarma
color, product_type, ram = get_user_query(user_input)

print(f"Renk: {color}, Ürün Tipi: {product_type}, RAM: {ram}")

def fetch_products(color, product_type, ram):
    base_query = """
    SELECT p.productName, p.productPrice, p.productColor, pf.*
    FROM Products p
    JOIN ProductFeatures pf ON p.productID = pf.productID
    WHERE 1=1
    """
    
    # Kullanıcıdan gelen renge göre sorguyu filtreleme
    if color:
        base_query += f" AND p.productColor LIKE '%{color}%'"
    
    # Kullanıcıdan gelen ürün tipine göre sorguyu filtreleme
    if product_type:
        base_query += f" AND p.productName LIKE '%{product_type}%'"
    
    # RAM kapasitesine göre sorguyu filtreleme
    if ram:
        base_query += f" AND pf.ramSize = {ram}"

    cursor.execute(base_query)
    rows = cursor.fetchall()
    
    return rows

# Veritabanından ürünleri çekme
products = fetch_products(color, product_type, ram)

# Sonuçları yazdırma
for product in products:
    print(product)

