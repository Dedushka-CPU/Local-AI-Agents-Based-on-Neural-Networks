import os
import queue
import sounddevice as sd
import json
import pyttsx3
from vosk import Model, KaldiRecognizer

class SpeechBot:
    def __init__(self, model_path="model"):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)

        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "Russian" in voice.name:
                self.engine.setProperty('voice', voice.id)
                break

        if not os.path.exists(model_path):
            print(f"Ошибка: Папка модели '{model_path}' не найдена!")
            exit(1)

        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.q = queue.Queue()

    def _callback(self, indata, frames, time, status):
        self.q.put(bytes(indata))

    def listen(self):
        print("Слушаю...")
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self._callback):
            while True:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        print(f"Вы сказали: {text}")
                        return text
                else:
                    pass

    def speak(self, text):
        if not text: return
        print(f"Бот: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

