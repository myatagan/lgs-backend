from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_model import generate_questions

app = Flask(__name__)

# 🔥 CORS tamamen açık, Live Server ile %100 uyumlu
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 🔹 DERS → KONU sözlüğü
subjects = {
  "Mat": [
    "1. Ünite: Çarpanlar ve Katlar",
    "1. Ünite: Üslü İfadeler",
    "2. Ünite: Kareköklü İfadeler",
    "2. Ünite: Veri Analizi ",
    "3. Ünite: Basit Olayların Olma Olasılığı ",
    "3. Ünite: Cebirsel İfadeler ve Özdeşlikler",
    "4. Ünite: Doğrusal Denklemler",
    "4. Ünite: Eşitsizlikler",
    "5. Ünite: Üçgenler",
    "5. Ünite: Eşliklik ve Benzerlik",
    "6. Ünite: Dönüşümler Geometrisi",
    "6. Ünite: Geometrik Cisimler",
  ],
  "Fen": [
    "1. Ünite: Mevsimler ve İklim",
    "2. Ünite: DNA ve Genetik Kod",
    "3. Ünite: Basınç",
    "4. Ünite: Madde ve Endüstri",
    "5. Ünite: Basit Makineler",
    "6. Ünite: Enerji Dönüşümleri ve Çevre Bilimi",
    "7. Ünite: Elektrik Yükleri ve Elektrik Enerjisi",
  ],
  "Tur": [
    "1. Ünite: Fiilimsiler",
    "2. Ünite: Cümlenin Öğeleri",
    "3. Ünite: Fiil Çatısı",
    "4. Ünite: Sözcükte Anlam",
    "5. Ünite: Cümlede Anlam",
    "6. Ünite: Cümle Çeşitleri",
    "7. Ünite: Yazım Kuralları",
    "8. Ünite: Paragraf",
    "9. Ünite: Noktalama işaretleri",
    "10. Ünite: Anlatım Bozuklukları",
  ],
  "Sos": [
    "1. Ünite: Bir Kahraman Doğuyor",
    "2. Ünite: Milli Uyanış-Bağımsızlık Yolunda Atılan Adımlar",
    "3. Ünite: Milli Bir Destan - Ya İstiklal Ya Ölüm",
    "4. Ünite: Atatürkçülük ve Çağdaşlaşan Türkiye",
    "5. Ünite: Demokratikleşme Çabaları",
    "6. Ünite: Atatürk Dönemi Türk Dış Politikası",
    "7. Ünite: Atatürk'ün Ölümü ve Sonrası",
  ],
  "Ing": [
    "1. Ünite: Friendship",
    "2. Ünite: Teen Life",
    "3. Ünite: In The Kitchen",
    "4. Ünite: On The Phone",
    "5. Ünite: The Internet",
    "6. Ünite: Adventures",
    "7. Ünite: Tourism",
    "8. Ünite: Chores",
    "9. Ünite: Science",
    "10. Ünite: Natural Forces",
  ],
  "Dkab": [
    "1. Ünite: Kader İnancı",
    "2. Ünite: Zekat ve Sadaka",
    "3. Ünite: Din ve Hayat",
    "4. Ünite: Hz. Muhammed'in Örnekliği",
    "5. Ünite: Kur'an-ı Kerim ve Özellikleri",
  ]
}

# -----------------------------------------------------------
# 1) Tüm dersleri döndüren endpoint
# -----------------------------------------------------------
@app.route('/lessons', methods=['GET'])
def get_lessons():
    return jsonify(list(subjects.keys()))

# -----------------------------------------------------------
# 2) Seçilen derse göre konuları döndüren endpoint
# -----------------------------------------------------------
@app.route('/topics', methods=['POST'])
def get_topics():
    data = request.json
    lesson = data.get("lesson")

    if lesson in subjects:
        return jsonify(subjects[lesson])
    else:
        return jsonify([])

# -----------------------------------------------------------
# 3) AI ile test soruları üreten endpoint
# -----------------------------------------------------------
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    
    print("📥 Gelen veri:", data)   # DEBUG

    try:
        questions = generate_questions(
            data["lesson"],
            data["topic"],
            data["difficulty"],
            data["count"]
        )
        
        print("📤 Üretilen soru (ilk 200 karakter):", str(questions)[:200])  # DEBUG
        
        return jsonify({"questions": questions})
    
    except Exception as e:
        print("❌ VERİ TABANI HATASI:", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

