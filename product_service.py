class ProductService:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def get_cheap_products(self, price_threshold):
        connection = self.db_connection.connect()
        cursor = connection.cursor()
        query = "SELECT * FROM Products WHERE Price < ?"
        cursor.execute(query, (price_threshold,))
        rows = cursor.fetchall()

        products = []
        for row in rows:
            products.append({
                'product_name': row.product_name,
                'price': row.price
            })
        
        cursor.close()
        connection.close()
        return products
