import requests
import json

class AIBot:
    def __init__(self, model_name="deepseek-r1:8b"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model_name

    def get_answer(self, prompt):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(self.url, json=payload)
            response_data = response.json()
            return response_data.get("response", "Я не знаю, что ответить.")
        except Exception as e:
            return f"Ошибка подключения к Ollama: {e}"