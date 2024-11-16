from transformers import pipeline
from flask import Flask, request, jsonify
import pyodbc
from huggingface_hub import login
login("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")

class ChatBot:
    def __init__(self):
        # BERT tabanlı modelleri yükle
        self.nlp_qa = pipeline("question-answering", model="dbmdz/bert-large-cased-finetuned-squadv1")
        self.nlp_classify = pipeline("text-classification", model="dbmdz/bert-base-turkish-cased")

    def answer_question(self, question, context):
        """
        Kullanıcıdan gelen soruyu alır ve ilgili context ile BERT modelinden cevap döner.
        """
        try:
            result = self.nlp_qa(question=question, context=context)
            return result['answer']
        except Exception as e:
            print(f"Error answering question: {e}")
            return "Cevap bulunamadı."

    def analyze_user_request(self, user_input):
        """
        Kullanıcının isteğini analiz eder ve etiket döner.
        """
        try:
            result = self.nlp_classify(user_input)
            return result[0]['label'] if result else None
        except Exception as e:
            print(f"Error analyzing request: {e}")
            return None

    def get_db_connection(self):
        """
        Veritabanı bağlantısı kurar.
        """
        try:
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=SEVGI;'
                'DATABASE=Dbo_eTicaret;'
                'Trusted_Connection=yes;'
            )
            return conn
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return None

    def get_products_from_db(self, criteria):
        """
        Veritabanından kullanıcının kriterine göre ürünleri getirir.
        """
        conn = self.get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor()
        query = f"""
        SELECT ProductName, Price, ImageUrl, ProductUrl
        FROM Products
        WHERE LOWER(ProductName) LIKE ? OR LOWER(Description) LIKE ?
        ORDER BY Price ASC
        """
        
        # Parametrized query to avoid SQL injection
        cursor.execute(query, ('%' + criteria.lower() + '%', '%' + criteria.lower() + '%'))
        results = cursor.fetchall()
        conn.close()

        # Ürün bilgilerini döndür
        return [{"name": row[0], "price": row[1], "image": row[2], "url": row[3]} for row in results]


# Flask Uygulaması
app = Flask(__name__)
chatbot = ChatBot()

@app.route('/')
def home():
    return "<h2>Flask API is running</h2>"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    context = data.get('context', '')
    
    # Kullanıcı isteğini analiz et
    criteria = chatbot.analyze_user_request(user_input)
    criteria = criteria if criteria else 'telefon'
    
    # Veritabanından ürünleri getir
    products = chatbot.get_products_from_db(criteria)
    
    # JSON formatında ürünleri döndür
    return jsonify(products)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
