import re
import subprocess
import webbrowser
import os
import json

from speach_bot import SpeechBot
from ai_bot import AIBot


class MainBot:
    MODE_AI = "ai"
    MODE_APPS = "apps"

    def __init__(self):
        self.speech = SpeechBot(model_path="model")
        self.ai = AIBot(model_name="deepseek-r1:8b")
        self.mode = self.MODE_AI

        self.app_map = {
            "ютуб музыка": "https://music.youtube.com/",
            "музыка ютуб": "https://music.youtube.com/",
            "youtube music": "https://music.youtube.com/",
            "музика ютуб": "https://music.youtube.com/",
            "ютуб": "https://www.youtube.com/",
            "youtube": "https://www.youtube.com/",
            "телеграм": "https://web.telegram.org/",
            "tg": "https://web.telegram.org/",
            "блокнот": "notepad.exe",
            "калькулятор": "calc.exe",
            "проводник": "explorer.exe",
            "хром": "chrome.exe",
            "гугл хром": "chrome.exe",
            "google chrome": "chrome.exe",
        }

        self.close_tab_patterns = [
            "закрой вкладк",
            "закрыть вкладк",
            "закрой таб",
            "закрыть таб",
        ]
        self.minimize_patterns = [
            "сверни",
            "свернуть",
            "сворачива",
            "минимиз",
        ]
        self.recycle_patterns = [
            "корзин",
            "коризну",
        ]

        self._noise_words = {
            "пожалуйста",
            "давай",
            "ну",
            "короче",
            "быстро",
            "сейчас",
            "мне",
            "пж",
            "плиз",
        }

        self._re_help = re.compile(r"\b(помощь|команд[ыа]?|что ты умеешь|что можешь)\b", re.IGNORECASE)
        self._re_start_ollama = re.compile(r"\b(запусти|включи|старт)\b.*\b(оллам[ауые]?|сервер)\b", re.IGNORECASE)
        self._re_switch_apps = re.compile(r"\b(режим)\b.*\b(прилож)\b|\bприложения\b", re.IGNORECASE)
        self._re_switch_ai = re.compile(r"\b(режим)\b.*\b(ии|ai)\b|\b(назад|вернись)\b", re.IGNORECASE)
        self._re_clear_bin = re.compile(r"\b(очисти|очистить|очищ)\b.*\b(корзин|коризн)\b", re.IGNORECASE)
        self._re_close_tab = re.compile(r"\b(закрой|закрыть)\b.*\b(вкладк|таб)\b", re.IGNORECASE)
        self._re_close_window = re.compile(r"\b(закрой|закрыть)\b.*\b(окно|его|её|это)\b", re.IGNORECASE)
        self._re_minimize_all = re.compile(r"\b(сверни|свернуть|сворачива|минимиз)\b.*\b(все|всё)\b", re.IGNORECASE)
        self._re_minimize = re.compile(r"\b(сверни|свернуть|сворачива|минимиз)\b", re.IGNORECASE)
        self._re_alt_tab_next = re.compile(r"\b(следующее|другое)\b.*\b(окно)\b|\b(переключи)\b.*\b(окно)\b", re.IGNORECASE)
        self._re_alt_tab_prev = re.compile(r"\b(предыдущее|предыдущ)\b.*\b(окно)\b", re.IGNORECASE)
        self._re_open = re.compile(r"\b(открой|открыть|запусти|запустить|включи)\b\s+(.*)$", re.IGNORECASE)
        self._re_youtube_music = re.compile(r"\b(музык|песн|трек)\b.*\b(ютуб|youtube)\b", re.IGNORECASE)

    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def _normalize_for_commands(self, text: str) -> str:
        t = self._norm(text)
        parts = [p for p in t.split(" ") if p and p not in self._noise_words]
        return " ".join(parts)

    def _extract_json(self, s: str) -> dict | None:
        if not s:
            return None
        m = re.search(r"\{[\s\S]*\}", s)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    def _ai_route_command(self, raw_text: str) -> dict | None:
        prompt = (
            "Ты классификатор голосовых команд для Windows. "
            "Верни СТРОГО один JSON без пояснений. "
            "action может быть одним из: "
            "help, start_ollama, switch_ai, switch_apps, open, youtube_music_search, "
            "close_tab, close_window, minimize, minimize_all, alt_tab_next, alt_tab_prev, clear_recycle_bin, unknown. "
            "Если action=open — добавь поле target (что открыть). "
            "Если action=youtube_music_search — добавь поле query (что включить). "
            f"Команда пользователя: {raw_text}"
        )
        try:
            ans = self.ai.get_answer(prompt)
        except Exception:
            return None
        return self._extract_json(ans)

    def _route_command(self, raw_text: str) -> dict:
        low = self._normalize_for_commands(raw_text)

        if self._re_help.search(low):
            return {"action": "help"}
        if self._re_start_ollama.search(low):
            return {"action": "start_ollama"}
        if self._re_switch_ai.search(low):
            return {"action": "switch_ai"}
        if self._re_switch_apps.search(low):
            return {"action": "switch_apps"}
        if self._re_clear_bin.search(low):
            return {"action": "clear_recycle_bin"}
        if self._re_close_tab.search(low):
            return {"action": "close_tab"}
        if self._re_close_window.search(low):
            return {"action": "close_window"}
        if self._re_alt_tab_prev.search(low):
            return {"action": "alt_tab_prev"}
        if self._re_alt_tab_next.search(low):
            return {"action": "alt_tab_next"}
        if self._re_minimize_all.search(low):
            return {"action": "minimize_all"}
        if self._re_minimize.search(low):
            return {"action": "minimize"}
        if self._re_youtube_music.search(low):
            cleaned = re.sub(r"(включи|запусти|открой|на ютубе|на youtube|в ютубе|в youtube)", "", raw_text, flags=re.IGNORECASE).strip()
            query = cleaned if cleaned else "музыка"
            return {"action": "youtube_music_search", "query": query}

        m = self._re_open.search(raw_text)
        if m:
            target = (m.group(2) or "").strip()
            if target:
                return {"action": "open", "target": target}

        ai_guess = self._ai_route_command(raw_text)
        if isinstance(ai_guess, dict) and "action" in ai_guess:
            return ai_guess
        return {"action": "unknown", "text": raw_text}

    def _try_hotkey(self, *keys: str) -> bool:
        """
        Нажимает горячие клавиши через `pyautogui`.
        """
        try:
            import pyautogui  
        except Exception:
            return False

        pyautogui.hotkey(*keys)
        return True

    def _clear_recycle_bin(self) -> str:
        
        try:
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "Clear-RecycleBin -Force -ErrorAction SilentlyContinue",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            return "Корзина очищена."
        except Exception as e:
            return f"Ошибка очистки корзины: {e}"

    def _find_chrome_exe(self) -> str | None:
        pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        pf86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        candidates = [
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _start_ollama(self) -> str:
        try:
            creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            subprocess.Popen(
                ["cmd", "/c", "start", "Ollama", "ollama", "serve"],
                creationflags=creationflags,
            )
            return "Запускаю Ollama. Подожди несколько секунд, пока она поднимется."
        except Exception as e:
            return f"Не удалось запустить Ollama: {e}"

    def _build_youtube_search(self, query: str, music: bool = False) -> str:
        from urllib.parse import quote_plus

        base = "https://music.youtube.com/search?q=" if music else "https://www.youtube.com/results?search_query="
        return base + quote_plus(query)

    def _help_text(self) -> str:
        return (
            "Я умею работать в двух режимах. "
            "В режиме ИИ я отвечаю на вопросы через модель Ollama. "
            "В режиме приложений я могу открывать сайты и программы, "
            "запускать YouTube или YouTube Music по запросу, "
            "закрывать вкладку, сворачивать окно и очищать корзину. "
            "Скажи, например: 'открой хром', 'открой блокнот', "
            "'включи музыку Цой пачка сигарет на ютубе', "
            "'очисти корзину', 'закрой вкладку', 'сверни окно', "
            "'режим приложений' или 'режим ИИ'. "
            "Чтобы запустить саму Ollama, скажи: 'запусти олламу'."
        )

    def _open_app(self, exe_or_cmd: str) -> str:
        exe = exe_or_cmd.strip()
        if not exe:
            return "Не понял приложение."

        if exe.lower() in {"chrome.exe", "chrome"}:
            found = self._find_chrome_exe()
            if found:
                try:
                    os.startfile(found) 
                    return f"Открыл Chrome."
                except Exception:
                    pass

            try:
                os.startfile("chrome.exe")  
                return "Открыл Chrome."
            except Exception:
                pass

        try:
            os.startfile(exe)  
            return f"Открыл: {exe}"
        except Exception:
            try:
                subprocess.Popen(["cmd", "/c", "start", '""', exe], shell=False)
                return f"Открыл: {exe}"
            except Exception as e:
                return f"Ошибка открытия приложения: {e}"

    def _open_target(self, raw_target: str) -> str:
        target = self._norm(raw_target)
        if not target:
            return "Не понял, что нужно открыть."

        if target.startswith("http://") or target.startswith("https://") or target.startswith("www."):
            webbrowser.open(raw_target, new=1)
            return f"Открыл ссылку: {raw_target}"

        for key, value in self.app_map.items():
            if key in target:
                if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
                    webbrowser.open(value, new=1)
                    return f"Открыл сайт: {value}"

                return self._open_app(value)

        try:
            os.startfile(raw_target)  
            return f"Открыл: {raw_target}"
        except Exception:
            return f"Не знаю, как открыть: {raw_target}"

    def _extract_open_target(self, text: str) -> str:
        m = re.search(r"(открой|запусти|открыть)\s+(.*)$", text, flags=re.IGNORECASE)
        return m.group(2).strip() if m else ""

    def run(self):
        self.speech.speak("Привет! Я тебя слушаю.")

        while True:
            user_text = self.speech.listen()
            if not user_text or "не удалось распознать" in user_text.lower():
                continue

            text = user_text.strip()
            low = self._normalize_for_commands(text)

            if "стоп" in low or "выход" in low or "пока" in low:
                self.speech.speak("До связи!")
                break

            cmd = self._route_command(text)
            action = cmd.get("action", "unknown")

            if action == "help":
                self.speech.speak(self._help_text())
                continue
            if action == "start_ollama":
                self.speech.speak(self._start_ollama())
                continue

            if self.mode == self.MODE_AI:
                if action == "switch_apps" or action == "open":
                    self.mode = self.MODE_APPS
                    target = cmd.get("target") or self._extract_open_target(text) or text
                    resp = self._open_target(target)
                    self.speech.speak(resp)
                elif action == "switch_ai":
                    self.speech.speak("Я уже в режиме ИИ.")
                else:
                    print(f">>Запрос в ИИ:", low)
                    ai_response = self.ai.get_answer(text)
                    self.speech.speak(ai_response)
            else:  # MODE_APPS
                if action == "switch_ai":
                    self.mode = self.MODE_AI
                    self.speech.speak("Переход в режим ИИ.")
                    continue

                if action == "clear_recycle_bin":
                    self.speech.speak(self._clear_recycle_bin())
                    continue

                if action == "minimize_all":
                    ok = self._try_hotkey("win", "d")
                    if ok:
                        self.speech.speak("Свернул все окна.")
                    else:
                        self.speech.speak("Не могу свернуть все окна: установи `pyautogui` для горячих клавиш.")
                    continue
                if action == "minimize":
                    ok = self._try_hotkey("win", "down")
                    if ok:
                        self.speech.speak("Свернул.")
                    else:
                        self.speech.speak("Не могу свернуть: установи `pyautogui` для горячих клавиш.")
                    continue

                if action == "close_tab":
                    ok = self._try_hotkey("ctrl", "w")
                    if ok:
                        self.speech.speak("Вкладка закрыта.")
                    else:
                        self.speech.speak("Не могу закрыть вкладку: установи `pyautogui` для горячих клавиш.")
                    continue

                if action == "close_window":
                    ok = self._try_hotkey("alt", "f4")
                    if ok:
                        self.speech.speak("Окно закрыто.")
                    else:
                        self.speech.speak("Не могу закрыть окно: установи `pyautogui` для горячих клавиш.")
                    continue

                if action == "alt_tab_next":
                    ok = self._try_hotkey("alt", "tab")
                    if ok:
                        self.speech.speak("Переключаюсь на следующее окно.")
                    else:
                        self.speech.speak("Не могу переключить окно: установи `pyautogui` для горячих клавиш.")
                    continue
                if action == "alt_tab_prev":
                    ok = self._try_hotkey("shift", "alt", "tab")
                    if ok:
                        self.speech.speak("Переключаюсь на предыдущее окно.")
                    else:
                        self.speech.speak("Не могу переключить окно: установи `pyautogui` для горячих клавиш.")
                    continue

                if action == "youtube_music_search":
                    query = cmd.get("query") or "музыка"
                    url = self._build_youtube_search(str(query), music=True)
                    webbrowser.open(url, new=1)
                    resp = f"Ищу на YouTube Music: {query}"
                elif action == "open":
                    target = cmd.get("target") or self._extract_open_target(text) or text
                    resp = self._open_target(target)
                else:
                    resp = self._open_target(text)

                self.speech.speak(resp)

