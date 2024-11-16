import re
from product_service import ProductService

class ChatBotLogic:
    def __init__(self, product_service):
        self.product_service = product_service

    def process_message(self, message):
        # Mesajda "ucuz" kelimesi varsa, fiyat analizi yap
        if 'ucuz' in message.lower():
            price_threshold = self.get_average_price()
            products = self.product_service.get_cheap_products(price_threshold)
            return self.format_product_list(products)

        return "Üzgünüm, bu konuda yardımcı olamıyorum."

    def get_average_price(self):
        # Ortalama fiyat hesaplama fonksiyonu (basit bir örnek)
        return 1000  # Burada fiyatları veritabanından alarak dinamik hale getirebilirsiniz

    def format_product_list(self, products):
        if not products:
            return "Maalesef uygun fiyatlı ürün bulunmamaktadır."
        response = "İşte ucuz telefonlar:\n"
        for product in products:
            response += f"- {product['product_name']} : {product['price']} TL\n"
        return response
