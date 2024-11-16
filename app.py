from flask import Flask, request
from db_connection import DBConnection
from product_service import ProductService
from chatbot_logic import ChatBotLogic

app = Flask(__name__)

# Bağlantıyı kur
db_connection = DBConnection()
product_service = ProductService(db_connection)
chatbot = ChatBotLogic(product_service)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if user_message:
        response = chatbot.process_message(user_message)
        return {"response": response}, 200
    return {"response": "Mesaj boş."}, 400

if __name__ == "__main__":
    app.run(debug=True)
