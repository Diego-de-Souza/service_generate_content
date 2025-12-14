from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.source import Source
from app.api.v1.schemas.source import SourceResponse, SourceCreate, SourceUpdate

router = APIRouter()

@router.get("/", response_model=List[SourceResponse])
async def list_sources(
    active_only: bool = Query(True, description="Apenas fontes ativas"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    db: Session = Depends(get_db)
):
    """
    Lista todas as fontes configuradas.
    """
    query = db.query(Source)
    
    if active_only:
        query = query.filter(Source.is_active == True)
    
    if category:
        query = query.filter(Source.category_focus.op('?')(category))
    
    sources = query.all()
    return sources

@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna fonte específica por ID.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")
    
    return source

@router.post("/", response_model=SourceResponse)
async def create_source(
    source_data: SourceCreate,
    db: Session = Depends(get_db)
):
    """
    Cria nova fonte de conteúdo.
    """
    # Verifica se domínio já existe
    existing = db.query(Source).filter(Source.domain == source_data.domain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domínio já cadastrado")
    
    source = Source(**source_data.dict())
    db.add(source)
    db.commit()
    db.refresh(source)
    
    return source

@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza fonte existente.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")
    
    # Atualiza campos fornecidos
    update_data = source_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
    
    db.commit()
    db.refresh(source)
    
    return source

@router.delete("/{source_id}")
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove fonte (soft delete - apenas desativa).
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")
    
    source.is_active = False
    db.commit()
    
    return {"message": "Fonte desativada com sucesso"}

@router.post("/{source_id}/test")
async def test_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Testa configuração da fonte fazendo um scraping de exemplo.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")
    
    try:
        from app.scrapers.factory import ScraperFactory
        
        scraper = ScraperFactory.create_scraper(source)
        
        async with scraper:
            # Testa apenas alguns itens
            data = await scraper.scrape()
            
        return {
            "status": "success",
            "items_found": len(data),
            "sample_titles": [item.get('title', 'Sem título')[:100] for item in data[:3]],
            "message": "Fonte configurada corretamente"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao testar fonte: {str(e)}"
        }