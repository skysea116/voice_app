from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
import base64
import tempfile
import os
import io
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Голосовой Сервер</title></head>
    <body>
        <h1>🎤 Голосовой Сервер</h1>
        <p>Сервер работает! Используйте POST /process</p>
    </body>
    </html>
    """

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "speech-recognition",
        "endpoints": ["/health", "/process"]
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
            return jsonify({"error": "Нет аудио", "success": False}), 400
        
        # Декодируем base64
        audio_bytes = base64.b64decode(audio_b64)
        
        # Сохраняем в временный файл
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            # Конвертируем в WAV
            audio = AudioSegment.from_file(temp_path)
            wav_path = temp_path.replace('.webm', '.wav')
            audio.export(wav_path, format="wav")
            
            # Распознаем речь
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data, language='ru-RU')
            
            # Коррекция для трахеостомии
            corrections = {
                'шш': 'ш', 'сс': 'с', 'хх': 'х',
                'аа': 'а', 'оо': 'о', 'уу': 'у'
            }
            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)
            
            if text:
                text = text[0].upper() + text[1:]
            
            return jsonify({
                "success": True,
                "text": text
            })
            
        except sr.UnknownValueError:
            return jsonify({
                "success": False,
                "error": "Речь не распознана",
                "text": ""
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "text": ""
            })
        finally:
            # Удаляем временные файлы
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)
                
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Общая ошибка: {str(e)}",
            "text": ""
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Сервер запускается на порту {port}")
    
    # Проверяем, какие WSGI серверы доступны
    try:
        from waitress import serve
        print("✅ Используем Waitress")
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        try:
            import gunicorn
            print("✅ Используем Gunicorn")
            # Gunicorn запустится через командную строку
        except ImportError:
            print("⚠️  Используем встроенный сервер Flask")
            app.run(host='0.0.0.0', port=port, debug=False)