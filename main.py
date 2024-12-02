from bot.chatbot import ChatBot
from bot.product_recommendation import ProductRecommendation

def main():
    # Chatbot ve ürün öneri sistemini başlat
    chatbot = ChatBot()
    product_recommendation = ProductRecommendation()

    # Kullanıcıdan gelen girdi
    user_input = "Merhaba, ben kamerası iyi ama ucuz bir telefon istiyorum."

    # Chatbot'un kullanıcının sorusunu anlaması ve cevap vermesi
    context = "Burada birkaç telefon önerisi var: Samsung Galaxy S23, Apple iPhone 14 Pro, Xiaomi Mi 11. Bu telefonlar, yüksek çözünürlüklü kameralarıyla bilinir."
    answer = chatbot.answer_question(user_input, context)
    
    print(f"Chatbot: {answer}")

    # Kullanıcının isteğini analiz etme (örneğin, ucuz telefon önerisi)
    user_features = extract_features(user_input)
    recommended_products = product_recommendation.get_products_based_on_features(user_features)

    # Ürün önerilerini döndür
    if recommended_products:
        print("Önerilen Ürünler:")
        for product in recommended_products:
            print(f"- {product['name']} - {product['price']} TL")
    else:
        print("Üzgünüz, istediğiniz kriterlere uyan ürün bulunamadı.")

# Kullanıcının özelliklerini analiz etme
def extract_features(user_input):
    """
    Kullanıcıdan gelen girdi üzerinde anahtar kelimeleri arayarak özellikleri çıkarır.
    """
    keywords = {
        'kamera': ['iyi', 'yüksek', 'kaliteli'],
        'fiyat': ['ucuz', 'pahalı', 'fiyat'],
    }

    features = {}

    # Kamera özelliği kontrolü
    for keyword in keywords['kamera']:
        if keyword in user_input:
            features['kamera'] = True
            break
    
    # Fiyat özelliği kontrolü
    for keyword in keywords['fiyat']:
        if keyword in user_input:
            features['fiyat'] = 'ucuz' if 'ucuz' in user_input else 'pahalı'
            break
    
    return features

if __name__ == "__main__":
    main()



