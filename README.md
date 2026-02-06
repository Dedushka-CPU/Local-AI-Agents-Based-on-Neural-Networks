# Local-AI-Agents-Based-on-Neural-Networks

Схема работы:
1)Микрофон $\rightarrow$ захватывает звук через sounddevice.
2)Vosk $\rightarrow$ анализирует байты звука и сопоставляет их с локальной моделью (папка model), выдает строку текста.
3)Python (MainBot) $\rightarrow$ получает строку и отправляет её через HTTP-запрос в Ollama.
4)Ollama $\rightarrow$ запускает нейросеть и выдает ответ.
5)Pyttsx3 $\rightarrow$ получает текст ответа и ревращает его в звук.(Временно отказывается работать , в отпуске)
