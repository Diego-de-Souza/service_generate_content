# 🎮 Geek Content Processor (Stateless)

## 📊 **O que é este serviço?**

Um **serviço stateless** que processa conteúdo geek usando IA e retorna dados prontos para sua API NestJS salvar no banco. 

**SEM banco de dados, SEM Redis, SEM dependências pagas.**

## ⚡ **Arquitetura Simples**

```
┌─────────────────┐    ┌──────────────────────┐
│   API NestJS    │───▶│  Python Processor    │
│   (Principal)   │    │     (Stateless)      │
│                 │    │                      │
│ • Cron Jobs     │    │ • Web Scraping       │
│ • Salva Banco   │    │ • IA Rewriting       │
│ • API Frontend  │    │ • Scoring/Filter     │
│                 │    │ • Retorna JSON       │
└─────────────────┘    └──────────────────────┘
```

## 🔥 **3 Endpoints Principais**

| Endpoint | Função | Frequência Recomendada |
|----------|--------|-------------------------|
| `POST /api/v1/batch/articles` | Processa artigos | A cada 3 dias |
| `POST /api/v1/batch/news` | Processa notícias | A cada 6 horas |
| `POST /api/v1/batch/events` | Processa eventos | Semanal |

## 📋 **Campos Retornados**

### Artigos
- `categoria` (animes, manga, filmes, studios, games, tech)
- `title`, `description`, `text`, `summary`
- `keyWords`, `original_url`, `source`

### Notícias  
- `title`, `disclosure_date`

### Eventos
- `title`, `description`, `location`, `date_event`, `url_event`

## 🚀 **Instalação Rápida**

### 1. **Configure API Keys**
```bash
Copy-Item .env.example .env
# Edite .env e coloque suas API keys OpenAI/Anthropic
```

### 2. **Docker (Recomendado)**
```bash
# Suba o serviço
docker-compose up -d

# Teste se está funcionando
curl -X POST http://localhost:8000/api/v1/batch/articles \
  -H "Content-Type: application/json" \
  -d '{"categoria": "games", "limit": 3}'
```

### 3. **Manual (Python)**
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## ✅ **O que NÃO precisa**
- ❌ PostgreSQL
- ❌ MySQL  
- ❌ Redis
- ❌ Celery
- ❌ Nenhum banco de dados
- ❌ Serviços pagos

## ✅ **O que precisa**
- ✅ Python 3.11+
- ✅ OpenAI API Key (OBRIGATÓRIO)
- ✅ Anthropic API Key (opcional)
- ✅ Docker (recomendado)

## 🔌 **Integração com NestJS**

Veja os guias completos:
- **[NESTJS_INTEGRATION.md](NESTJS_INTEGRATION.md)** - Como integrar
- **[NESTJS_EXAMPLES.md](NESTJS_EXAMPLES.md)** - Exemplos de código
- **[INSTALL.md](INSTALL.md)** - Instalação detalhada

## 📊 **Exemplo de Uso**

```bash
# Request
curl -X POST http://localhost:8000/api/v1/batch/articles \
  -H "Content-Type: application/json" \
  -d '{
    "categoria": "games", 
    "limit": 10, 
    "min_score": 0.7
  }'

# Response
{
  "total_processed": 8,
  "articles": [
    {
      "categoria": "games",
      "title": "Novo DLC de Elden Ring Anunciado",
      "description": "FromSoftware revela expansão...",
      "text": "Texto completo reescrito pela IA...",
      "summary": "Resumo gerado pela IA...", 
      "keyWords": ["elden ring", "fromsoftware"],
      "original_url": "https://fonte.com",
      "source": "GameInformer"
    }
  ]
}
```

## 🎯 **Por que Stateless?**

- **Simples**: Sem dependências complexas
- **Confiável**: Menos pontos de falha  
- **Escalável**: Fácil de replicar
- **Barato**: Sem serviços pagos
- **Flexível**: Sua API controla tudo

## 📚 **Documentação**

- **[API_GUIDE.md](API_GUIDE.md)** - Todos os endpoints
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Guia final
- **[INSTALL.md](INSTALL.md)** - Instalação passo a passo

---

**🎮 Processamento inteligente de conteúdo geek, sem complicação!** 🚀