from speach_bot import SpeechBot
from ai_bot import AIBot


class MainBot:
    def __init__(self):
        self.speech = SpeechBot(model_path="model")
        self.ai = AIBot(model_name="deepseek-r1:8b")

    def run(self):
        self.speech.speak("Привет! Я тебя слушаю.")

        while True:
            user_text = self.speech.listen()
            if not user_text or "не удалось распознать" in user_text.lower():
                continue

            if "стоп" in user_text.lower() or "выход" in user_text.lower():
                self.speech.speak("До связи!")
                break

            ai_response = self.ai.get_answer(user_text)
            self.speech.speak(ai_response)

