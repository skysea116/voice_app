from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import base64
import tempfile
import os
import io
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)  # Разрешаем запросы со всех доменов

print("🚀 Сервер речи запускается...")
print("✅ Используем Google Speech Recognition API")

@app.route('/')
def home():
    return """
    <h1>🎤 Голосовой Сервер</h1>
    <p>Сервер для распознавания речи работает!</p>
    <p>Используйте endpoint: POST /process</p>
    """

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "speech-recognition",
        "version": "1.0",
        "provider": "Google Speech API"
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "message": "Сервер работает!",
        "instructions": "Отправьте POST запрос на /process с аудио в base64"
    })

@app.route('/process', methods=['POST'])
def process():
    try:
        # Получаем данные
        data = request.json
        if not data:
            return jsonify({"error": "Нет данных", "success": False}), 400
        
        audio_b64 = data.get('audio')
        if not audio_b64:
            return jsonify({"error": "Нет аудио данных", "success": False}), 400
        
        print("📥 Получено аудио, размер:", len(audio_b64), "символов")
        
        # Декодируем base64
        audio_bytes = base64.b64decode(audio_b64)
        
        # Конвертируем WebM в WAV (если нужно)
        try:
            # Пытаемся открыть как WebM/MP3/OGG
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        except:
            # Если не получается, пробуем как WAV напрямую
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_bytes)
                temp_file = f.name
            
            audio = AudioSegment.from_wav(temp_file)
            os.unlink(temp_file)
        
        # Конвертируем в WAV 16kHz mono
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            audio.export(f.name, format="wav")
            temp_file = f.name
        
        # Распознаем речь через Google Web Speech API
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(temp_file) as source:
            # Убираем шум
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            try:
                # Пробуем распознать через Google (бесплатно)
                text = recognizer.recognize_google(audio_data, language='ru-RU')
                print("✅ Распознано:", text[:50] + "..." if len(text) > 50 else text)
                
            except sr.UnknownValueError:
                return jsonify({
                    "success": False,
                    "error": "Речь не распознана",
                    "text": ""
                })
            
            except sr.RequestError as e:
                return jsonify({
                    "success": False,
                    "error": f"Ошибка сервиса Google: {str(e)}",
                    "text": ""
                })
        
        # Удаляем временный файл
        os.unlink(temp_file)
        
        # Коррекция для трахеостомии
        corrections = {
            'шш': 'ш', 'сс': 'с', 'хх': 'х', 'жж': 'ж',
            'щщ': 'щ', 'чч': 'ч', 'цц': 'ц',
            'вх': 'в', 'гх': 'г', 'дх': 'д',
            'пх': 'п', 'тх': 'т', 'кх': 'к'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # Делаем первую букву заглавной
        if text:
            text = text[0].upper() + text[1:]
        
        return jsonify({
            "success": True,
            "text": text,
            "confidence": "high",
            "language": "ru-RU"
        })
        
    except Exception as e:
        print("❌ Ошибка:", str(e))
        return jsonify({
            "success": False,
            "error": str(e),
            "text": ""
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌍 Сервер запущен на порту: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)