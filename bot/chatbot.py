import re
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering
from flask import Flask, request, jsonify
from flask_cors import CORS
from db_connection import get_database_connection  # Veritabanı bağlantısı için modülünüz
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
 

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

    def check_greeting(self,user_input):
        greetings = ['merhaba','günaydın','iyi akşamlar','günaydin','selam','hey','iyi günler', 'hayırlı günler','selamunaleyküm','merhabalar','iyi geceler']
        user_input = user_input.lower() #küçük harfe çevirmeliyiz

        for greeting in greetings:
            if greeting in user_input:
                return f"Merhaba , size nasıl yardımcı olabilirim ?"
        return None

    def check_small_talk (self, user_input):
        small_talks = ['nasılsın','naber','ne haber','iyi misin','ne var ne yok']
        user_input = user_input.lower()

        for small_talk in small_talks:
            if small_talk in user_input:
                return f"Harikayım ! Teşekkür ederim. Size nasıl yardımcı olabilirim ?"
        return None

    def get_top_phones(self):
        top_phone_ids = [26,29,30]

        query = """
    SELECT 
        p.productID, 
        p.prName, 
        p.prPrice, 
        p.prColor, 
        sc.subcatName,
        (SELECT TOP 1 picUrl 
         FROM Pictures 
         WHERE Pictures.productID = p.productID 
         ORDER BY picUrl) AS picUrl
    FROM Products p
    LEFT JOIN Subcategories sc ON p.subcategoryID = sc.subcategoryID
    WHERE p.productID IN ({})
    """.format(",".join(map(str, top_phone_ids)))


        try:
            result = self.db.execute(query).fetchall()
            return result
        except Exception as e:
            print(f"En iyi telefonlar alınırken hata : {str(e)}")
            return []
  
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
            print(f"Veritabanındaki renkler : {len(result)}")
            return result
        except Exception as e:
            print(f"Renkleri alırken hata oluştu :{e}")
            return []
        
    def match_color_from_input(self, user_input):
        """Renkleri eşleştiriyoruz"""
        available_colors = [row[0] for row in self.get_available_colors()]
        normalized_input= ' '.join(user_input.lower().strip().split())
        print(f"Kullanıcı girdisi normalize edilen : {normalized_input}")
        best_match = process.extractOne(normalized_input, available_colors)
        if best_match and best_match[1] > 80:
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
        normalized_input=' '.join(user_input.lower().strip().split())
        print(f"Normalize edilen kulanıcı girdisi : {normalized_input}")
        best_match = process.extractOne(normalized_input, available_product_types)
        if best_match and best_match[1] > 60:
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
            print(f"Veritabanımızdaki feature sayısı : {len(result)}")
            return result
        except Exception as e:
            print(f"FullFeatureları alırken bir hata oluştu : {e}")
            return[]
    
    def match_fullFeature(self, user_input):
        available_fullFeatures = [row[0] for row in self.get_available_fullFeatures()]
        normalized_input = ' '.join(user_input.lower().strip().split())
        print(f"Kullanıcı girdisi normalize edilen: {normalized_input}")
    
    # En iyi eşleşmeyi bulma
        best_match = process.extractOne(normalized_input, available_fullFeatures)
    
        if best_match and best_match[1] > 70:  # Eşleşme skoru %60'tan büyükse
            feature = best_match[0]
            print(f"Eşleşen FullFeature: {feature}")
            return feature
        else:
            print("Eşleşen FullFeature bulunamadı.")
            return None
    
    def match_names(self,user_input):
        words = user_input.lower().strip().split()       
        matched_names = []
        query = " SELECT DISTINCT prName FROM Products WHERE prName IS NOT NULL"
        try :
            result = self.db.execute(query).fetchall()
            print(f"Bulunan product names : {len(result)}")
            product_names = [row[0].lower() for row in self.db.cursor.fetchall()]
            for word in words:
                if any(word in prName for prName in product_names):
                    matched_names.append(word)
            return matched_names
        except Exception as ex:
            print(f"Product name bulunamadı: {ex}")
            return []
                
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
        normalized_input = ' '.join(user_input.lower().strip().split())
        best_match = process.extractOne(normalized_input, available_prices)
        if best_match and best_match[1] > 80 :
            price = best_match[0]
            print(f"Eşleşen price : {price}")
            return price
        else:
            print("Eşleşen price yok. Skor : {best_match[1] if best_match else 'None'}")
            return None

    def extract_price_condition(self, user_input):
        match = re.search(r'(\d+)\s*TL?', user_input)

        if match:
            price = int(match.group(1))
            condition = None
            if fuzz.partial_ratio("ucuz",user_input.lower()) > 70:
                condition = "ucuz"
            elif fuzz.partial_ratio("pahalı",user_input.lower()) > 70:
                condition = "pahalı"
            
            if condition:
                return price, condition
        return None, None

    def filter_by_price (self, user_input, base_query, params):
        """
        :param user_input: String input alınacak örneğin "2000 Tl'den ucuz telefon istiyorum."
        """
        price, condition = self.extract_price_condition(user_input)

        if condition:  # Fiyat koşulu (ucuz veya pahalı) varsa
            if price:  # Eğer fiyat belirlenmişse, fiyat koşuluna göre filtreleme yap
                if condition == "ucuz":
                    base_query += " AND p.prPrice < ?"
                elif condition == "pahalı":
                    base_query += " AND p.prPrice > ?"
                params.append(price)
                print(f"Fiyat koşulu eklendi : {base_query}")  # Debug için
            else:  # Eğer fiyat yoksa, sadece condition'a göre en düşük veya en yüksek 3 ürünü al
                if condition == "ucuz":
                   base_query += " ORDER BY p.prPrice ASC"  # En ucuzdan en pahalıya doğru sırala
                elif condition == "pahalı":
                   base_query += " ORDER BY p.prPrice DESC"  # En pahalıdan en ucuza doğru sırala
                base_query += "OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY"  # Yalnızca ilk 3 ürünü al
                print(f"Fiyat koşulu olmadan en {condition} ürünler getirildi: {base_query}")  # Debug için      
        else:
            print("Fiyata göre filtreleme yapılamadı.")

        return base_query, params   

    def get_extreme_price_products(self, price_condition, subcategory_name, price=None):
        """
        Verilen price_condition'a göre (en pahalı ya da en ucuz) subcategory'ye ait ürünleri getirir.
        :param price_condition: 'ucuz' veya 'pahalı'
        :param subcategory_name: Subcategory ismi (örneğin: 'Telefon')
        :return: En pahalı veya en ucuz ürünler
        """
        conn = self.db.connect()  # Veritabanı bağlantısını al
        cursor = conn.cursor()

        # Koşula göre SQL sorgusunu belirleyelim
        if price_condition == 'ucuz':
            query = """
            SELECT TOP 3 p.productID, p.prName, p.prPrice, sc.subcatName
            FROM Products p
            JOIN Subcategories sc ON p.subcategoryID = sc.subcategoryID
            WHERE sc.subcatName = ?
            ORDER BY p.prPrice ASC

            """
        elif price_condition == 'pahalı':
            query = """
            SELECT TOP 3 p.productID, p.prName, p.prPrice, sc.subcatName
            FROM Products p
            JOIN Subcategories sc ON p.subcategoryID = sc.subcategoryID
            WHERE sc.subcatName = ?
            ORDER BY p.prPrice DESC  
            """
        else:
            print("geçersiz fiyat")
            return []
        try:
            cursor.execute(query, (subcategory_name,))
            result = cursor.fetchall()
            print(f"{price_condition.capitalize()} ürünler : {result}")  
            return result
        except Exception as e:
            print(f"Ürünleri alırken hata : {e}")
            return []
        finally:
            cursor.close()
            conn.close()        
       
    def process_comprehensive_query(self, user_input):
        filters = [part.strip() for part in user_input.split(',')]
        color, product_type, full_feature, price_condition, price_value = None, None, None, None, None

        for filter_text in filters:
            price, condition = self.extract_price_condition(filter_text)
            if price and condition:
               price_value, price_condition = price, condition
               continue

            matched_color = self.match_color_from_input(filter_text)
            if matched_color:
               color = matched_color
               continue

            matched_product_type = self.match_product_types(filter_text)
            if matched_product_type:
               product_type = matched_product_type
               continue

            matched_feature = self.match_fullFeature(filter_text)
            if matched_feature:
               full_feature = matched_feature
               continue

        base_query = """
        SELECT DISTINCT p.productID, p.prName, p.prPrice, p.prColor, sc.subcatName,
        (SELECT TOP 1 picUrl FROM Pictures WHERE Pictures.productID = p.productID ORDER BY picUrl) AS picUrl
        FROM Products p
        LEFT JOIN ProductFeatures pf ON p.productID = pf.productID
        LEFT JOIN Subcategories sc ON p.subcategoryID = sc.subcategoryID
        WHERE 1=1
        """
        params = []

        if price_condition == "ucuz":
          base_query += " AND p.prPrice < ?"
          params.append(price_value)
        elif price_condition == "pahalı":
            base_query += " AND p.prPrice > ?"
            params.append(price_value)

        if color:
           base_query += " AND LOWER(p.prColor) LIKE LOWER(?)"
           params.append(f"%{color}%")

        if product_type:
           base_query += " AND LOWER(sc.subcatName) LIKE LOWER(?)"
           params.append(f"%{product_type}%")

        if full_feature:
           base_query += " AND LOWER(pf.FullFeature) LIKE LOWER(?)"
           params.append(f"%{full_feature}%")

        try:
           conn = self.db
           cursor = conn.cursor()
           cursor.execute(base_query, params)
           rows = cursor.fetchall()
           return [
            {
                "name": row[1],
                "price": row[2],
                "color": row[3],
                "subcategory": row[4],
                "image_url": row[5],
            }
            for row in rows
        ]
        except Exception as e:
           print(f"Error querying products: {e}")
           return []

    def contains_kwords(self, user_input, keywords):
        normalized_input = user_input.lower().split()
        return all(any(keyword in word for word in normalized_input) for keyword in keywords)

    def check_feedback (self,user_input):
        feedback_keywords = ["değerlendirmek", "geri bildirim", "şikayet","öneri", "yorum", "feedback"]
        user_input = user_input.lower()
        for kw in feedback_keywords:
            if kw in user_input:
                help_message = """
                <ul>
                     <li> Şikayet ve önerileriniz için lütfen <a href="/Home/Contact"> buraya tıklayın</a>.</li>
                </ul>
                """
                return help_message
            
        return None

    def get_user_query(self, user_input):
        """
        Kullanıcının mesajını analiz eder.
        """

        tokens = [token.strip() for token in user_input.split(',')]
        color, product_type, full_feature, price, prName = None,None,None,None,None
        for token in tokens:
            color = self.match_color_from_input(token)
            product_type = self.match_product_types(token)
            full_feature = self.match_fullFeature(token)
            price = self.match_prices(token)
            prName = self.match_names(token)
        
        print(f"Elde edilen değerler : {color} , {product_type} , {full_feature} , {price}, {prName}")
        return color, product_type, full_feature, price, prName

    def fetch_products(self, color, product_type, full_feature, price, prName, user_input):
        """
        Kullanıcı kriterlerine göre veritabanından ürünleri getirir.
        """
        conn = get_database_connection()  # DB bağlantınızı sağlayan fonksiyon
        cursor = conn.cursor()

        # Dinamik SQL sorgusu
        base_query = """
        SELECT DISTINCT 
        p.productID as productID,
        p.prName AS prName, 
        p.prPrice AS prPrice ,
        p.prColor AS prColor,         
        sc.subcatName AS subcatName,
        (SELECT TOP 1 picUrl 
        FROM Pictures 
        WHERE Pictures.productID = p.productID 
        ORDER BY picUrl ) AS picUrl
        FROM Products p
        LEFT JOIN ProductFeatures pf ON p.productID = pf.productID
        LEFT JOIN ProductFeatureDefinitions pfd ON pf.productFeatureID = pfd.productFeatureID
        LEFT JOIN Subcategories sc ON p.subcategoryID = sc.subcategoryID
        LEFT JOIN Pictures pic ON p.productID = pic.productID
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
        
        matched_names = self.match_names(user_input)
        prName_conditions = []
        if prName:
            prName_conditions.append("LOWER(p.prName) LIKE LOWER(?)")
            params.append(f"%{prName}%")
        for name in matched_names:
            prName_conditions.append("LOWER(p.prName) LIKE LOWER(?)")
            params.append(f"%{prName}%")
        
        if prName_conditions:
            base_query += f" AND ({' OR '.join(prName_conditions)})"

        base_query, params = self.filter_by_price(user_input,base_query, params)

        print(f"Son halindeki sorgu :{base_query}")
        print(f"Parametreler: {params}")
        
        print(f"Çalıştırılan sorgu : {base_query}")
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        conn.close()
        print(f"Bulunan ürün sayısı : {len(rows)}")
        print(rows)
        
        return rows
  
    

    def process_user_input(self, user_input):

        feedback_response = self.check_feedback(user_input)
        if feedback_response:
            return[{"message" : feedback_response}]     

        greeting_response = self.check_greeting(user_input)
        if greeting_response:
            return[{"message": greeting_response}]        

        small_talk_response = self.check_small_talk(user_input)
        if small_talk_response:
            return[{"message": small_talk_response}]

        if self.contains_kwords(user_input, ["kargo", "takip"]):  
            help_message = """
            <ul>
                <li>Kargo ve takip bilgisi için: <a href="https://www.ptt.gov.tr/">PTT</a></li>
            </ul>
            """         
            return [{"message": help_message}]
        
        if self.contains_kwords(user_input, ["kargo", "bilgi"]):
            help_message = """
            <ul>
                <li>1000 TL ve üzeri alışverişlerinizde kargo bedavadır.</li>
                <li>1000 TL ve altı alışverişlerinizde kargo ücretimiz tüm Türkiye'de sabit ve 50 TL'dir.</li>                
                <li>13:00'a kadar verilen siparişler aynı gün kargolanır.</li>
                <li>Kargo şirketi olarak PTT ile anlaşmalıyız.</li>
                <li>Kargo ve takip bilgisi için: <a href="https://www.ptt.gov.tr/">PTT</a></li>
            </ul>
            """           
            return [{"message" : help_message}]

        if "en iyi telefonlar" in user_input.lower():
            top_phones = self.get_top_phones()  # En iyi telefonları getir
            if top_phones:
                return [{
                    "productID": row[0],
                    "name": row[1] if row[1] else "Ürün adı yok", 
                    "price": row[2] if row[2] else "0.00", 
                    "color": row[3] if row[3] else "Ürün rengi bilinmiyor",
                    "subcategory": row[4] if row[4] else "Ürün subcategory'si bilinmiyor",
                    "picUrl": row[5] if len(row) > 5 else None,
                } for row in top_phones]
            else:
                return [{"message": "Şu anda en iyi telefonlar listesi boş."}]

        
        color, product_type, full_feature, price, prName= self.get_user_query(user_input)
        print(f"Color: {color}, Product Type: {product_type}, Feature: {full_feature}, Price:{price}, Product Name:{prName}")  # Debug çıktısı
        products = self.fetch_products(color, product_type, full_feature, price, prName, user_input)
        
        if products:
            # Ürünleri JSON formatında döndür
            return [{
                "productID":row[0],
                "name": row[1] if row[1] else "Ürün adı yok", 
                "price": row[2] if row[2] else "0.00", 
                "color": row[3] if row[3] else "Ürün rengi bilinmiyor",
                "subcategory": row[4] if row[4] else "ürün subcategory'si bilinmiyor",
                "picUrl": row[5] if len(row)>5 else None,
            } for row in products]
        else:
            return [{"message": "Kriterlere uygun ürün bulunamadı."}]
            
    def process_user_input_for_price(self, user_input, subcategory_name):
        """
        Kullanıcının inputuna göre fiyat koşulunu belirleyip,
        o koşula göre en pahalı ya da en ucuz ürünleri getirir.
        :param user_input: Kullanıcıdan alınan input (örneğin: "65000 TL'den ucuz telefon")
        :param subcategory_name: Subcategory ismi (örneğin: 'Telefon')
        :return: En pahalı veya en ucuz ürünler
        """
        # Fiyat koşulunu çıkar
        price, price_condition = self.extract_price_condition(user_input)
        
        if price_condition:
            # Fiyat koşuluna göre ürünleri al
            products = self.get_extreme_price_products(price_condition, subcategory_name, price)
            
            if products:
                return products
            else:
                return [{"message": "Bu subcategory için ürün bulunamadı."}]
        else:
            return [{"message": "Fiyat koşulu belirlenemedi."}]
  
    
# Flask Uygulaması
app = Flask(__name__)
chatbot = ChatBot()
CORS(app)
app.config['DEBUG'] = True

@app.route('/')
def home():
    return "<h2>Flask API çalışıyor. Chatbot ile iletişime geçebilirsiniz.</h2>"

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    if not user_input:
        return jsonify({"error": "Mesaj boş olamaz."}), 400

    try:
        response = chatbot.process_user_input(user_input)
        return jsonify(response)
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"error": "Bir hata oluştu. Lütfen tekrar deneyin."}), 500

if __name__ == '__main__':
    app.run(host="127.0.0.1",port=5000,debug=True)