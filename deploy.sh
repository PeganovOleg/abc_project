#!/bin/bash
# Деплой ABC Дневника на свою VM

set -e

echo "🚀 Деплой ABC Дневника..."

# Проверка зависимостей
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не установлен"
    exit 1
fi

# Создаём директорию
APP_DIR="${HOME}/abc-diary"
mkdir -p "$APP_DIR"

echo "📁 Копируем файлы..."
# Здесь нужно скопировать файлы проекта
# scp -r . user@vm:/home/user/abc-diary/

echo "📦 Устанавливаем зависимости..."
cd "$APP_DIR"
pip3 install --user -r requirements.txt

# Установка Whisper
pip3 install --user openai-whisper torch torchaudio numpy numba tiktoken tqdm

echo "⚙️ Настройка systemd сервиса..."

# Создаём systemd сервис
cat > /tmp/abc-diary.service << EOF
[Unit]
Description=ABC Дневник
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PYTHONPATH=$HOME/.local/lib/python3.11/site-packages
Environment=DATABASE_URL=sqlite:///./abc_diary.db
Environment=SECRET_KEY=your-secret-key-change-this
Environment=PORT=8000
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "📋 Инструкция по установке:"
echo ""
echo "1. Скопируй файлы на VM:"
echo "   scp -r abc-diary/ user@your-vm-ip:/home/user/"
echo ""
echo "2. На VM выполни:"
echo "   sudo cp /tmp/abc-diary.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable abc-diary"
echo "   sudo systemctl start abc-diary"
echo ""
echo "3. Настрой nginx (опционально):"
echo "   sudo apt install nginx"
echo "   # Конфигурация reverse proxy на порт 8000"
echo ""
echo "4. Открой в браузере:"
echo "   http://your-vm-ip:8000"
echo ""
echo "✅ Готово!"
