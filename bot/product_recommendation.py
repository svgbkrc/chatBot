import pyodbc

class ProductRecommendation:
    def __init__(self):
        # SQL Server bağlantı dizesi
        self.connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=SEVGI;Database=e-Ticaaret;Trusted_Connection=yes;'

    def get_products_based_on_features(self, features):
        """
        Kullanıcının istediği özelliklere göre ürünleri veritabanından çeker.
        """
        conn = pyodbc.connect(self.connection_string)
        cursor = conn.cursor()

        # Kullanıcının istediği türde ucuz telefonları seçme
        if features.get('fiyat') == 'ucuz' and features.get('kamera'):
            query = """
                SELECT * FROM Products 
                WHERE category = 'Telefon' 
                AND price < (SELECT AVG(price) FROM Products WHERE category = 'Elektronik' AND Subcategories=) 
                AND camera_quality = 'yüksek'
            """
        else:
            query = "SELECT * FROM Products WHERE category = 'Telefon' AND camera_quality = 'yüksek'"

        cursor.execute(query)
        rows = cursor.fetchall()

        products = []
        for row in rows:
            products.append({
                'name': row.name,
                'price': row.price,
                'camera_quality': row.camera_quality
            })

        return products
