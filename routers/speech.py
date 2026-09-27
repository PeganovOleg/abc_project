from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Setting
from auth import get_current_user
import httpx

router = APIRouter(prefix="/api/speech")

@router.post("/recognize")
async def recognize(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    api_key = db.query(Setting).filter(Setting.key == "yandex_api_key").first()
    if not api_key or not api_key.value:
        raise HTTPException(400, "API-ключ Яндекс не настроен. Обратитесь к администратору.")

    audio_bytes = await file.read()
    
    # Ограничение размера — макс 25 МБ (лимит Яндекса)
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(413, "Аудиофайл слишком большой. Максимум 25 МБ (~7 минут).")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize",
                headers={
                    "Authorization": f"Api-Key {api_key.value}",
                    "Content-Type": "audio/webm",
                },
                params={
                    "lang": "ru-RU",
                    "format": "oggopus",
                },
                content=audio_bytes,
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            
            if "result" in data:
                return {"text": data["result"], "success": True, "model": "yandex"}
            else:
                return {"text": "", "success": True, "model": "yandex"}
                
    except httpx.HTTPStatusError as e:
        err_text = e.response.text[:200] if hasattr(e.response, 'text') else str(e)
        raise HTTPException(502, f"Ошибка SpeechKit HTTP {e.response.status_code}: {err_text}")
    except Exception as e:
        raise HTTPException(502, f"Ошибка запроса: {str(e)}")
