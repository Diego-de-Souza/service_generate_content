# Guia da API - Geek Content Processor (Stateless)

## Visão Geral

A API do Geek Content Processor permite processar conteúdo geek com IA e retornar dados prontos para sua API NestJS. A API oferece endpoints para:

- ✅ Processamento batch de artigos
- ✅ Processamento batch de notícias
- ✅ Processamento batch de eventos
- ✅ Health check do serviço
- ✅ Integração stateless com NestJS

## Base URL

```
http://localhost:8000/api/v1
```

## Autenticação

Esta API stateless não requer autenticação - é projetada para ser chamada pela sua API NestJS interna.

**Integração típica:**
- API NestJS → Python Processor → Dados processados
- Sem exposição pública direta
- Segurança por rede interna

## Endpoints Principais

### 📈 Artigos Processados (Batch)

```http
POST /api/v1/batch/articles
```

**Body JSON:**
```json
{
  "category": "animes",  // animes, manga, filmes, studios, games, tech
  "persona": "games",    // tom editorial
  "limit": 20,           // máximo de artigos
  "min_score": 0.7       // qualidade mínima
}
```

**Resposta:**
```json
{
  "total_processed": 15,
  "articles": [
    {
      "category": "animes",
      "title": "Novo Episódio de Attack on Titan Quebra Recordes",
      "description": "O episódio final da série bateu recordes de audiência...",
      "text": "O tão aguardado episódio final de Attack on Titan...",
      "summary": "Attack on Titan encerra com chave de ouro...",
      "keyWords": ["attack on titan", "anime", "final"],
      "original_url": "https://exemplo.com/noticia-original",
      "source": "Anime News Network"
    }
  ],
  "processing_time": 45.2,
  "metadata": {...}
}
```

### 📰 Notícias Recentes (Batch)

```http
POST /api/v1/batch/news
```

**Body JSON:**
```json
{
  "limit": 15,
  "hours_ago": 24,
  "min_score": 0.6
}
```

**Resposta:**
```json
{
  "total_processed": 12,
  "news": [
    {
      "title": "Breaking: Novo Studio Ghibli Film Anunciado",
      "disclosure_date": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### 🎉 Eventos Futuros (Batch)

```http
POST /api/v1/batch/events
```

**Body JSON:**
```json
{
  "limit": 10,
  "days_ahead": 30,
  "location_filter": "São Paulo"  // opcional
}
```

**Resposta:**
```json
{
  "total_processed": 8,
  "events": [
    {
      "title": "Anime Friends 2024",
      "description": "O maior evento de anime do Brasil...",
      "location": "São Paulo Expo, São Paulo",
      "date_event": "2024-07-20T09:00:00Z",
      "url_event": "https://www.animefriends.com.br"
    }
  ]
}
```

### � Busca de Conteúdo

```http
GET /content/search?q=cyberpunk&category=games&limit=20
```

**Parâmetros:**
- `q` (string): Termo de busca (mínimo 2 caracteres)
- `category` (string): Filtrar por categoria
- `persona` (string): Filtrar por persona
- `limit` (int): Número máximo de resultados

**Resposta:**
```json
[
  {
    "id": 2,
    "title": "Cyberpunk 2077: Expansão Phantom Liberty",
    "search_relevance": 0.95,
    "highlighted_snippet": "...Cyberpunk 2077 recebe nova expansão...",
    "category": "games",
    "final_score": 0.88
  }
]
```

### � Feed Personalizado

```http
GET /content/feed/{user_id}?limit=20&offset=0
```

**Parâmetros de URL:**
- `user_id` (string): Identificador único do usuário

**Parâmetros de Query:**
- `limit` (int): Número máximo de artigos
- `offset` (int): Offset para paginação

**Resposta:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "Artigo personalizado...",
      "personalized_score": 0.94,
      "original_score": 0.85
    }
  ],
  "total": 25,
  "personalized": true,
  "filters_applied": ["Categorias: games, tecnologia"],
  "recommendations": ["Bom nível de personalização configurado"]
}
```

## ⚙️ **Parâmetros de Configuração**

### **Categorias Suportadas**
- `animes` - Anime News Network, Crunchyroll
- `manga` - Manga Updates, VIZ Media  
- `filmes` - Screen Rant, ComingSoon
- `studios` - Studio Ghibli, Disney Studios
- `games` - GameSpot, IGN, PC Gamer
- `tech` - TechCrunch, Wired, Ars Technica

### **Personas Editoriais**
- `games` - Tom focado em gaming
- `cinema` - Tom focado em filmes/séries
- `tech` - Tom focado em tecnologia
- `geek` - Tom geral geek/nerd

### **Scores e Qualidade**
- `min_score` - Score mínimo (0.0 a 1.0)
  - 0.6+ - Conteúdo aceitável
  - 0.7+ - Boa qualidade
  - 0.85+ - Alta qualidade (featured)

### **Limites Recomendados**
- Artigos: 5-20 por request
- Notícias: 10-30 por request  
- Eventos: 10-50 por request

### � Gerenciar Fontes

#### Listar Fontes
```http
GET /sources?active_only=true&category=games
```

#### Testar Fonte
```http
POST /sources/{source_id}/test
```

#### Criar Nova Fonte
```http
POST /sources
```

**Body:**
```json
{
  "name": "GameSpot Brasil",
  "domain": "gamespot.com.br",
  "base_url": "https://www.gamespot.com.br",
  "scraper_type": "rss",
  "scraper_config": {
    "feed_urls": ["https://www.gamespot.com.br/rss"]
  },
  "category_focus": ["games"],
  "requests_per_minute": 10
}
```

## Códigos de Status HTTP

- `200 OK` - Sucesso
- `201 Created` - Recurso criado
- `400 Bad Request` - Dados inválidos
- `404 Not Found` - Recurso não encontrado
- `422 Unprocessable Entity` - Erro de validação
- `500 Internal Server Error` - Erro interno

## Rate Limiting

- **Limite padrão:** 60 requisições por minuto
- **Burst:** Até 100 requisições em rajada
- **Headers de resposta:**
  - `X-RateLimit-Limit`: Limite por minuto
  - `X-RateLimit-Remaining`: Requisições restantes
  - `X-RateLimit-Reset`: Timestamp do reset

## Exemplos de Uso

### JavaScript/TypeScript

```javascript
// Buscar conteúdo trending
const response = await fetch('/api/v1/content/trending?limit=10&persona=games');
const articles = await response.json();

// Feed personalizado
const feedResponse = await fetch('/api/v1/content/feed/user123?limit=20');
const userFeed = await feedResponse.json();

// Registrar interação
fetch('/api/v1/users/user123/interaction', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    article_id: 456,
    interaction_type: 'view',
    interaction_data: { time_spent: 180 }
  })
});
```

### Python

```python
import requests

# Buscar artigos
response = requests.get('http://localhost:8000/api/v1/content/trending', 
                       params={'limit': 10, 'category': 'games'})
articles = response.json()

# Criar preferências
prefs = {
    'preferred_categories': ['games', 'tecnologia'],
    'preferred_personas': ['games', 'tech']
}
requests.put('http://localhost:8000/api/v1/users/user123/preferences', 
            json=prefs)
```

### cURL

```bash
# Buscar conteúdo trending
curl "http://localhost:8000/api/v1/content/trending?limit=5&persona=games"

# Analytics
curl "http://localhost:8000/api/v1/analytics/overview?days=7"

# Criar preferências
curl -X PUT "http://localhost:8000/api/v1/users/user123/preferences" \
  -H "Content-Type: application/json" \
  -d '{"preferred_categories": ["games"], "relevance_weight": 0.6}'
```

## Webhooks (Futuro)

Em futuras versões, a API suportará webhooks para:

- ✅ Notificar quando novo conteúdo de alta relevância for gerado
- ✅ Alertar sobre trending topics emergentes
- ✅ Notificar conclusão de geração de conteúdo em lote

## SDKs Disponíveis

- **JavaScript/TypeScript**: Em desenvolvimento
- **Python**: Em desenvolvimento
- **PHP**: Planejado
- **C#**: Planejado

## Suporte e Documentação

- **Documentação interativa:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

## Limitações Atuais

- Não há autenticação implementada
- Rate limiting básico
- Sem versionamento de API
- Webhooks não implementados
- SDKs em desenvolvimento

## Próximas Funcionalidades

## 🚀 **Exemplos de Integração**

### **Cron Job NestJS**
```typescript
@Cron('0 6 */3 * *')  // A cada 3 dias
async syncContent() {
  const response = await fetch('http://content-processor:8000/api/v1/batch/articles', {
    method: 'POST',
    body: JSON.stringify({ category: 'games', limit: 20 })
  });
  
  const { articles } = await response.json();
  
  for (const article of articles) {
    await this.articlesService.create(article);
  }
}
```

### **Teste Rápido**
```bash
curl -X POST http://localhost:8000/api/v1/batch/articles \
  -H "Content-Type: application/json" \
  -d '{"category": "games", "limit": 3}'
```

## 📚 **Documentação Relacionada**

- **[INSTALL.md](INSTALL.md)** - Instalação e configuração
- **[NESTJS_EXAMPLES.md](NESTJS_EXAMPLES.md)** - Exemplos de integração
- **[README.md](README.md)** - Visão geral do projeto

---

**🎮 API simples e direta para processamento de conteúdo geek!** 🚀