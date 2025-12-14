from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_preference import UserPreference
from app.api.v1.schemas.user_preference import (
    UserPreferenceResponse,
    UserPreferenceCreate,
    UserPreferenceUpdate
)

router = APIRouter()

@router.get("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna preferências do usuário.
    """
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preferences:
        # Retorna preferências padrão se não existir
        return {
            "user_id": user_id,
            "preferred_categories": [],
            "preferred_personas": [],
            "relevance_weight": 0.4,
            "popularity_weight": 0.3,
            "quality_weight": 0.3,
            "content_length_preference": "medium",
            "update_frequency": "daily",
            "interaction_history": {}
        }
    
    return preferences

@router.post("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def create_user_preferences(
    user_id: str,
    preferences_data: UserPreferenceCreate,
    db: Session = Depends(get_db)
):
    """
    Cria preferências para um usuário.
    """
    # Verifica se já existe
    existing = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Preferências já existem para este usuário")
    
    preferences = UserPreference(
        user_id=user_id,
        **preferences_data.dict()
    )
    
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    
    return preferences

@router.put("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    user_id: str,
    preferences_data: UserPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza preferências do usuário.
    """
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preferences:
        # Cria se não existe
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)
    
    # Atualiza campos fornecidos
    update_data = preferences_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences

@router.post("/{user_id}/interaction")
async def record_user_interaction(
    user_id: str,
    article_id: int,
    interaction_type: str,  # 'view', 'like', 'share', 'time_spent'
    interaction_data: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """
    Registra interação do usuário para personalização futura.
    """
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preferences:
        # Cria preferências básicas se não existe
        preferences = UserPreference(
            user_id=user_id,
            interaction_history={}
        )
        db.add(preferences)
    
    # Atualiza histórico de interações
    if not preferences.interaction_history:
        preferences.interaction_history = {}
    
    article_key = str(article_id)
    if article_key not in preferences.interaction_history:
        preferences.interaction_history[article_key] = []
    
    interaction_record = {
        "type": interaction_type,
        "timestamp": datetime.now().isoformat(),
        "data": interaction_data or {}
    }
    
    preferences.interaction_history[article_key].append(interaction_record)
    
    # Mantém apenas as últimas 100 interações por artigo
    if len(preferences.interaction_history[article_key]) > 100:
        preferences.interaction_history[article_key] = preferences.interaction_history[article_key][-100:]
    
    db.commit()
    
    return {"message": "Interação registrada com sucesso"}

@router.get("/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna recomendações personalizadas baseadas no perfil do usuário.
    """
    from app.content.content_processor import ContentProcessor
    
    processor = ContentProcessor(db)
    
    # Busca preferências
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preferences:
        return {
            "message": "Configure suas preferências para receber recomendações personalizadas",
            "recommendations": [],
            "setup_required": True
        }
    
    # Gera recomendações
    recommendations = processor._generate_user_recommendations(preferences)
    
    # Busca conteúdo sugerido
    suggested_content = await processor.get_personalized_feed(
        user_id=user_id,
        limit=5
    )
    
    return {
        "recommendations": recommendations,
        "suggested_content": suggested_content.get('articles', [])[:3],
        "setup_required": False
    }