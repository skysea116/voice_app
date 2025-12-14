from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
import io
from pydub import AudioSegment
import requests
import tempfile

app = Flask(__name__)
CORS(app)

print("🚀 Сервер запускается...")
print("✅ Используем альтернативный метод распознавания")

def convert_audio_format(audio_bytes):
    """Конвертируем аудио в правильный формат"""
    try:
        # Пробуем определить формат и конвертировать
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        # Конвертируем в WAV, моно, 16kHz
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav", parameters=["-acodec", "pcm_s16le"])
        return wav_io.getvalue()
    except Exception as e:
        print(f"Ошибка конвертации: {e}")
        # Возвращаем оригинал
        return audio_bytes

def recognize_speech_simple(audio_bytes):
    """Упрощенное распознавание речи"""
    # Вместо сложных библиотек используем простой подход
    # Здесь можно подключить любой API
    
    # Временно возвращаем тестовый текст
    # В реальном приложении подключите Google Cloud Speech-to-Text
    # или другой сервис распознавания
    
    return "Это тестовый распознанный текст. Для реального распознавания подключите API."

@app.route('/')
def home():
    return """
    <h1>🎤 Голосовой Сервер</h1>
    <p>Сервер работает! Используйте POST /process</p>
    <p>Для реального распознавания подключите Google Speech-to-Text API</p>
    """

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "speech-server",
        "version": "2.0",
        "instructions": "Используйте POST /process с аудио в base64"
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "message": "Сервер работает нормально!",
        "next_step": "Отправьте аудио на /process"
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
        
        # Конвертируем в нужный формат
        converted_audio = convert_audio_format(audio_bytes)
        
        # Распознаем речь (упрощенная версия)
        text = recognize_speech_simple(converted_audio)
        
        # Коррекция для трахеостомии
        corrections = {
            'шш': 'ш', 'сс': 'с', 'хх': 'х',
            'вх': 'в', 'пх': 'п', 'тх': 'т'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # Делаем первую букву заглавной
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]
        
        return jsonify({
            "success": True,
            "text": text,
            "note": "Используйте Google Speech API для точного распознавания"
        })
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "text": ""
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌍 Сервер запущен на порту: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)