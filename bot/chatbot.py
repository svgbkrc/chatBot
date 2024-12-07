import re
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering
from flask import Flask, request, jsonify
from flask_cors import CORS
from db_connection import get_database_connection  # Veritabanı bağlantısı için modülünüz
from fuzzywuzzy import process
 

class ChatBot:
    
    def __init__(self):
        """
        Chatbot'un başlatılması ve modellerin yüklenmesi.
        """
        #Veritabanı bağlantısı ekleyelim
        self.db = get_database_connection()
        # Soru-cevap için BERT tabanlı model
        self.nlp_qa = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

        # Metin sınıflandırma için Türkçe model
        self.nlp_classify = pipeline("text-classification", model="dbmdz/bert-base-turkish-cased")
        
        # Türkçe soru-cevap için başka bir model (isteğe bağlı kullanabilirsiniz)
        self.tokenizer = AutoTokenizer.from_pretrained("lserinol/bert-turkish-question-answering")
        self.model = AutoModelForQuestionAnswering.from_pretrained("lserinol/bert-turkish-question-answering")

    def answer_question(self, question, context):
        """
        Soru-cevap modelini kullanarak cevap döndürür.
        """
        try:
            result = self.nlp_qa(question=question, context=context)
            return result['answer']
        except Exception as e:
            print(f"Error answering question: {e}")
            return "Cevap bulunamadı."

    def analyze_user_request(self, user_input):
        """
        Kullanıcı isteğini analiz ederek sınıflandırma yapar.
        """
        try:
            result = self.nlp_classify(user_input)
            return result[0]['label'] if result else None
        except Exception as e:
            print(f"Error analyzing request: {e}")
            return None
    
    def get_available_colors(self):
        """
        Veritabanında tanımlı renkler döncevej
        """
        query="SELECT DISTINCT LOWER(prColor) AS color FROM Products WHERE prColor IS NOT NULL"
        try:
            result = self.db.execute(query).fetchall()
            print(f"Veritabanındaki renkler : {result}")
            return result
        except Exception as e:
            print(f"Renkleri alırken hata oluştu :{e}")
            return []
        
    def match_color_from_input(self, user_input):
        """Renkleri eşleştiriyoruz"""
        available_colors = [row[0] for row in self.get_available_colors()]
        normalized_input= ' '.join(user_input.lower().split())
        print(f"Kullanıcı girdisi normalize edilen : {normalized_input}")
        best_match = process.extractOne(normalized_input, available_colors)
        if best_match and best_match[1] > 60:
            color = best_match[0]
            print(f"Eşleşen renk :{color}")
            return color
        else:
            print("Eşleşen renk bulunamadı.")
            return None
            
    def get_available_product_types(self):
        """ Database de varolan productTypes yani subcategoriesleri alıyoruz."""
        
        query = "SELECT DISTINCT LOWER(subcatName) AS product_type FROM Subcategories WHERE subcatName IS NOT NULL"
        try:
            result = self.db.execute(query).fetchall()
            print(f"Subcategories sayısı : {len(result)}")
            return result
        except Exception as e:
            print(f"Subcategories alınırken hata oluştu : {e}")
            return []
    
    def match_product_types(self, user_input):
        """Subcategorileri eşleştiriyoruz."""
        available_product_types = [row[0] for row in self.get_available_product_types()]
        normalized_input=' '.join(user_input.lower().split())
        print(f"Normalize edilen kulanıcı girdisi : {normalized_input}")
        best_match = process.extractOne(normalized_input, available_product_types)
        if best_match and best_match[1] > 50:
            product_type=best_match[0]
            print(f"Eşleşen subcategory : {product_type}")
            return product_type
        else:
            print("Eşelşen subcategory bulunamadı.")
            return None
    
    def get_available_fullFeatures(self):
        """ Veritabanında tanımlı fullFeatureları almak için"""
        query = "SELECT DISTINCT LOWER(FullFeature) AS feature FROM ProductFeatures WHERE FullFeature IS NOT NULL"
        try:
            result = self.db.execute(query).fetchall()
            print(f"Veritabanımızdaki featurelar : {result}")
            return result
        except Exception as e:
            print(f"FullFeatureları alırken bir hata oluştu : {e}")
            return[]
    
    def match_fullFeature(self, user_input):
        available_fullFeatures = [row[0] for row in self.get_available_fullFeatures()]
        normalized_input = ' '.join(user_input.lower().split())
        print(f"Kullanıcı girdisi normalize edilen: {normalized_input}")
    
    # En iyi eşleşmeyi bulma
        best_match = process.extractOne(normalized_input, available_fullFeatures)
    
        if best_match and best_match[1] > 50:  # Eşleşme skoru %60'tan büyükse
            feature = best_match[0]
            print(f"Eşleşen FullFeature: {feature}")
            return feature
        else:
            print("Eşleşen FullFeature bulunamadı.")
            return None
    
    def get_available_prices(self):
        query = "SELECT prPrice FROM Products WHERE prPrice IS NOT NULL"
        try:
            result = self.db.execute(query).fetchall()
            print(f"Bulunan fiyat sayısı : {len(result)}")
            return result
        except Exception as e:
            print(f"Priceları alrıken sorun oluştu : {e}")
            return []

    def match_prices(self,user_input):
        available_prices = [row[0] for row in self.get_available_prices()]
        normalized_input = ' '.join(user_input.lower().split())
        best_match = process.extractOne(normalized_input, available_prices)
        if best_match and best_match[1] > 60 :
            price = best_match[0]
            print(f"Eşleşen price : {price}")
            return price
        else:
            print("Eşleşen price yok.")
            return None

    def filter_by_price (self, user_input, base_query, params):
        """
        :param user_input: String input alınacak örneğin "2000 Tl'den ucuz telefon istiyorum."
        """
        match = re.search(r'(\d+)\s*TL.*?(ucuz|pahalı)', user_input, re.IGNORECASE)
   
        if match :
            price = int(match.group(1))
            comparison = match.group(2).lower()
           
            if comparison =="ucuz":
                base_query += " AND p.prPrice < ?"
                params.append(price)
            elif comparison == "pahalı":
                base_query = " AND p.prPrice > ?"
                params.append(price)

            print(f"Yeni giriş : {base_query}")
            return base_query , params
        else:
            print("Fiyata göre filtreleme yapılamadı.")
            return base_query,params                 
 
    def get_user_query(self, user_input):
        """
        Kullanıcının mesajını analiz eder.
        """
        color = self.match_color_from_input(user_input)
        product_type = self.match_product_types(user_input)
        full_feature = self.match_fullFeature(user_input)
        price = self.match_prices(user_input)
        
        print(f"Elde edilen değerler : {color} , {product_type} , {full_feature} , {price}")
        return color, product_type, full_feature, price

    def fetch_products(self, color, product_type, full_feature, price ,user_input):
        """
        Kullanıcı kriterlerine göre veritabanından ürünleri getirir.
        """
        conn = get_database_connection()  # DB bağlantınızı sağlayan fonksiyon
        cursor = conn.cursor()

        # Dinamik SQL sorgusu
        base_query = """
        SELECT p.prName AS prName, 
        p.prPrice,
        p.prColor AS prColor, 
        pf.featureName AS featureName,
        pf.featureValue AS featureValue, 
        sc.subcatName AS subcatName,
        pf.FullFeature AS FullFeature
        FROM Products p
        LEFT JOIN ProductFeatures pf ON p.productID = pf.productID
        LEFT JOIN ProductFeatureDefinitions pfd ON pf.productFeatureID = pfd.productFeatureID
        LEFT JOIN Subcategories sc ON p.subcategoryID = sc.subcategoryID
        WHERE 1=1
        """
        params = []

        # Filtreler ekleyelim        
        if color:
            base_query += f" AND LOWER(p.prColor) LIKE LOWER(?)"
            params.append(f"%{color}%")
        if product_type:
            base_query += f" AND LOWER(sc.subcatName) LIKE LOWER(?)"
            params.append(f"%{product_type}%")
        if full_feature:
            base_query += f" AND LOWER(pf.FullFeature) LIKE LOWER(?)"
            params.append(f"%{full_feature}%")
        if price:
            base_query += f" AND p.prPrice LIKE ?"
            params.append(f"%{price}%")
        base_query, params = self.filter_by_price(user_input,base_query, params)

        base_query += """
        GROUP BY p.productID, p.prPrice, p.prColor, p.prName, sc.subcatName, pf.featureName, pf.featureValue, pf.FullFeature
        """

        print(f"Çalıştırılan sorgu : {base_query}")
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        conn.close()
        print(f"Bulunan ürün sayısı : {len(rows)}")
        
        return rows
 
    def process_user_input(self, user_input):
        color, product_type, full_feature, price = self.get_user_query(user_input)
        print(f"Color: {color}, Product Type: {product_type}, Feature: {full_feature}, Price:{price}")  # Debug çıktısı
        products = self.fetch_products(color, product_type, full_feature, price, user_input)
        
        if products:
            # Ürünleri JSON formatında döndür
            return [{
                "name": row[0], 
                "price": row[1], 
                "color": row[2],
                "feature": row[3],
                "feature_value": row[4],
                "subcategory": row[5],
                "full_feature": row[6]
            } for row in products]
        else:
            return [{"message": "Kriterlere uygun ürün bulunamadı."}]
        

 
    

# Flask Uygulaması
app = Flask(__name__)
chatbot = ChatBot()
CORS(app)

@app.route('/')
def home():
    return "<h2>Flask API çalışıyor. Chatbot ile iletişime geçebilirsiniz.</h2>"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        #User inputu allaım
        user_input = request.json.get('message', '')
        print(f"Kullanıcı girisi : {user_input}")
        if not user_input:
            return jsonify({"error": "Lütfen istediğiniz ürün özelliklerini yazınız."}), 400
        
        result = chatbot.process_user_input(user_input)
        
        if result:
            return jsonify({"products": result}), 200
        else:
            return jsonify({"message":" aradığınız kriterlere uygun bir ürün bulunamadı."}), 404
    except Exception as e:
        print(f"Hata oluştu : {e}")
        return jsonify({"message": "Bir hata oluştu , lütfen tekrar deneyiniz."}), 500
   

if __name__ == '__main__':
    app.run(host="127.0.0.1",port=5000)