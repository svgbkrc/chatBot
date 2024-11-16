import pyodbc

# SQL Server veritabanı bağlantı ayarları
server = 'SEVGI'
database = 'Dbo_eTicaret'
driver = '{ODBC Driver 17 for SQL Server}'

def get_database_connection():
    try:
        # Windows Authentication kullanarak bağlantı
        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;')
        print("Veritabanı bağlantısı başarılı.")
        return conn
    except Exception as e:
        print("Veritabanına bağlanırken hata oluştu:", e)
        return None

# Bağlantıyı test etme
connection = get_database_connection()

if connection:
    try:
        # Cursor oluşturun ve basit bir sorgu çalıştırın
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        # Sorgunun sonucunu kontrol edin
        if result:
            print("Bağlantı kontrolü başarılı! Veritabanı ile iletişim kuruldu.")
        else:
            print("Bağlantı kontrolü başarısız!")

        # Cursor ve bağlantıyı kapatın
        cursor.close()
        connection.close()
    except Exception as e:
        print("Sorgu çalıştırılırken hata oluştu:", e)
else:
    print("Bağlantı kurulamadı.")
