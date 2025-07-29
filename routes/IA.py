from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from requests import Session
from sqlalchemy import text
from core.IA_mode_config import enviar_mensaje_ia, enviar_mensaje_ia_random
from core.dependencies import get_current_user
from db.database import SessionLocal
from models.user import User


router = APIRouter(prefix="/IA", tags=["IA"])


def get_db():
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import HTTPException
from sqlalchemy import text

@router.get("/chatQuery")
async def message_ia(message: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = enviar_mensaje_ia(mensaje=message, user_id=current_user.id)

    try:
        query = response.get("query")
        template_message = response.get("message", "")

        if not query:
            return template_message

        result = db.execute(text(query)).all()

        secondary_message = f"""
        Responde a la siguiente pregunta del usuario utilizando únicamente la información disponible en los resultados proporcionados.

        Pregunta del usuario:
        {message}

        Resultados de la base de datos:
        {result}

        Instrucciones:
        1. Analiza el significado e intención de la pregunta de forma semántica.
        2. Si en los resultados hay un dato que responde de forma directa y precisa a la pregunta, devuelve solo esa respuesta en español, de forma clara y profesional.
        3. Si no hay un resultado que responda directamente, presenta los datos disponibles en un formato útil y ordenado, indicando que no hay una coincidencia exacta pero mostrando lo más relevante.
        4. Nunca inventes datos. Solo responde en base a los resultados mostrados.
        5. Si los valores numericos no tienen decimales o son .0 solo retorna el numero entero
        6. Si la respuesta es numérica (por ejemplo precios), incluye la palabra adecuada como “córdobas”, “unidades”, “ventas”, etc., según el contexto.
        """
        response_secondary = enviar_mensaje_ia(mensaje=secondary_message, user_id=current_user.id)

        return response_secondary 
    except Exception as e:
        return response

@router.get("/chat")
async def message_ia(message: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return enviar_mensaje_ia_random(message)    
