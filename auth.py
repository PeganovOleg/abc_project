from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
import os, secrets, string
import bcrypt

SECRET_KEY = os.getenv("SECRET_KEY", "changeme-super-secret-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

def hash_password(password: str) -> str:
    """Хеширование пароля с использованием bcrypt"""
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Проверка пароля"""
    try:
        plain_bytes = plain.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_current_user(request: Request, db: Session):
    from models import User
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401)
    return user

def generate_password(length=10) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_username(full_name: str, db: Session) -> str:
    from models import User
    import transliterate
    base = full_name.lower().split()[0] if full_name else "user"
    try:
        base = transliterate.translit(base, 'ru', reversed=True)
    except Exception:
        pass
    base = ''.join(c for c in base if c.isalnum())[:12] or "user"
    username = base
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base}{counter}"
        counter += 1
    return username
