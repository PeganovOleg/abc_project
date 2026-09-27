#!/bin/bash
# Установка ABC Дневника на VM

set -e

echo "🚀 Установка ABC Дневника..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен. Устанавливаю..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Создаём виртуальное окружение
echo "📦 Создаю виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Устанавливаю зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Устанавливаем Whisper
echo "🎤 Устанавливаю Whisper..."
pip install openai-whisper torch torchaudio numpy numba tiktoken tqdm

# Создаём .env
echo "⚙️ Настройка окружения..."
cat > .env << EOF
SECRET_KEY=your-s…tion-$(date +%s)
DATABASE_URL=sqlite:///./abc_diary.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
YANDEX_API_KEY=your-yandex-api-key-here
EOF

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Запуск сервера:"
echo "  source venv/bin/activate"
echo "  python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Или для фона:"
echo "  nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &"
echo ""
echo "Открой в браузере: http://$(hostname -I | awk '{print $1}'):8000"
