FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём директорию для локальных пакетов
RUN mkdir -p /app/.pylocal

# Переменные окружения
ENV PYTHONPATH=/app/.pylocal/lib/python3.11/site-packages:$PYTHONPATH
ENV DATABASE_URL=sqlite:///./abc_diary.db
ENV SECRET_KEY=your-secret-key-change-in-production

# Открываем порт
EXPOSE 8000

# Запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
