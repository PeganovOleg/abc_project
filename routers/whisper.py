from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import tempfile
import os

router = APIRouter(prefix="/api/whisper")

# Загружаем модель при первом использовании (ленивая загрузка)
model = None

def get_model():
    global model
    if model is None:
        try:
            import whisper
            # tiny: ~39M, base: ~74M, small: ~244M, medium: ~769M, large: ~1550M
            model = whisper.load_model("tiny")
        except Exception as e:
            raise HTTPException(500, f"Ошибка загрузки Whisper: {str(e)}")
    return model

@router.post("/recognize")
async def recognize_whisper(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    
    audio_bytes = await file.read()
    
    # Ограничение размера — макс 10 МБ
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(413, "Аудиофайл слишком большой. Максимум 10 МБ.")
    
    # Сохраняем во временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    
    try:
        # Распознаём
        model = get_model()
        result = model.transcribe(tmp_path, language="ru")
        
        return {"text": result["text"], "success": True, "model": "whisper-tiny"}
    except Exception as e:
        raise HTTPException(500, f"Ошибка распознавания: {str(e)}")
    finally:
        os.unlink(tmp_path)
