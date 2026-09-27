# Деплой ABC Дневника на VM

## Быстрый старт

```bash
# 1. Скопируй архив на VM
scp abc-diary.tar.gz user@your-vm-ip:/home/user/

# 2. Подключись к VM
ssh user@your-vm-ip

# 3. Распакуй
cd ~
tar xzf abc-diary.tar.gz
cd abc-diary

# 4. Установи зависимости
pip3 install -r requirements.txt
pip3 install openai-whisper torch torchaudio numpy numba tiktoken

# 5. Запусти
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Systemd сервис (автозапуск)

```bash
sudo tee /etc/systemd/system/abc-diary.service << 'SYSTEMD'
[Unit]
Description=ABC Дневник
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/abc-diary
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable abc-diary
sudo systemctl start abc-diary
```

## Nginx (опционально)

```bash
sudo apt install nginx
sudo tee /etc/nginx/sites-available/abc-diary << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX

sudo ln -s /etc/nginx/sites-available/abc-diary /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

## Доступ

Открой в браузере: `http://your-vm-ip:8000`
