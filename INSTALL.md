# 🚀 Instalação - Geek Content Processor (Stateless)

## ✅ **Serviço Totalmente Stateless**

- ❌ **SEM PostgreSQL** - Sem banco de dados
- ❌ **SEM Redis** - Sem cache pago
- ❌ **SEM Celery** - Sem tasks complexas
- ✅ **Apenas processamento** - Recebe request, processa, retorna JSON

## Pré-requisitos

### Sistema
- **Python 3.11+**
- **Docker & Docker Compose** (recomendado)

### APIs Necessárias (OBRIGATÓRIO)
- **OpenAI API Key** (GPT-4/GPT-3.5) - OBRIGATÓRIO
- **Anthropic API Key** (Claude) - opcional mas recomendado

## 🐳 Instalação com Docker (Recomendado)

### 1. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/geek-content-generator.git
cd geek-content-generator
```

### 2. Configure Variáveis de Ambiente
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:
```bash
# Configuração básica
STATELESS_MODE=true
DEBUG=false
ENVIRONMENT=production

# APIs de IA (OBRIGATÓRIO)
OPENAI_API_KEY=sk-sua-chave-openai-aqui
ANTHROPIC_API_KEY=sk-ant-sua-chave-anthropic-aqui

# Configurações de Scraping
SCRAPING_DELAY_MIN=1
SCRAPING_DELAY_MAX=3
MAX_CONCURRENT_REQUESTS=10

# Configuração de Conteúdo
MIN_CONTENT_SCORE=0.7
MAX_ARTICLES_PER_REQUEST=20
```

### 3. Inicie o Serviço
```bash
# Build e start do serviço (stateless)
docker-compose up -d

# Ou para desenvolvimento (com logs)
docker-compose up
```

### 4. Teste a Instalação
```bash
# Teste endpoint de artigos
curl -X POST "http://localhost:8000/api/v1/batch/articles" \
  -H "Content-Type: application/json" \
  -d '{"category": "games", "limit": 3}'

# Acesse a documentação da API
open http://localhost:8000/docs
```

## 🐍 Instalação Manual (Python)

### 1. Clone e Configure o Ambiente
```bash
git clone https://github.com/seu-usuario/geek-content-generator.git
cd geek-content-generator

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

### 2. Configure Variáveis de Ambiente
```bash
cp .env.example .env
# Edite .env com suas configurações (principalmente as API keys)
```

### 3. Inicie o Serviço
```bash
# Servidor stateless (sem dependências externas)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ⚙️ Configuração Avançada

### Configuração de Fontes

O sistema vem com fontes pré-configuradas para as categorias:
- **animes** - Anime News Network, Crunchyroll
- **manga** - Manga Updates, VIZ Media
- **filmes** - Screen Rant, ComingSoon
- **studios** - Studio Ghibli, Disney Studios
- **games** - GameSpot, IGN, Polygon
- **tech** - TechCrunch, Ars Technica

#### Teste dos Endpoints Batch
```bash
# Teste artigos de animes
curl -X POST "http://localhost:8000/api/v1/batch/articles" \
  -H "Content-Type: application/json" \
  -d '{"category": "animes", "limit": 5}'

# Teste notícias recentes
curl -X POST "http://localhost:8000/api/v1/batch/news" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "hours_ago": 24}'

# Teste eventos
curl -X POST "http://localhost:8000/api/v1/batch/events" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "days_ahead": 30}'
```

#### Via Banco de Dados
```sql
INSERT INTO sources (name, domain, base_url, scraper_type, scraper_config, category_focus) 
VALUES (
  'GameInformer', 
  'gameinformer.com',
  'https://www.gameinformer.com',
  'rss',
  '{"feed_urls": ["https://www.gameinformer.com/rss.xml"]}',
  '["games"]'
);
```

### Configuração de Personas

Personas são configuradas em `app/core/config.py`:

```python
PERSONAS = {
    "games": {
        "tone": "casual e entusiasmado",
        "style": "linguagem gamer, referências técnicas",
        "focus": "gameplay, reviews, news"
    },
    "cinema": {
        "tone": "analítico e cinematográfico", 
        "style": "crítico especializado, referências artísticas",
        "focus": "análises, bastidores, tendências"
    },
    # Adicione suas personas customizadas
}
```

### Configuração de Webhooks (Futuro)

```bash
# No .env
WEBHOOK_URL=https://sua-app.com/webhook/content
WEBHOOK_SECRET=sua-chave-secreta
```

## 🔧 Scripts Úteis

### Inicialização
```bash
# Configurar banco de dados
python scripts/init_database.py

# Testar fontes
python scripts/test_sources.py

# Deploy automatizado
python scripts/deploy.py deploy --environment production
```

### Manutenção
```bash
# Status dos serviços
docker-compose ps

# Logs em tempo real
docker-compose logs -f app

# Backup do banco
docker-compose exec db pg_dump -U postgres geek_content > backup.sql

# Limpeza de containers
docker-compose down --remove-orphans
docker system prune
```

## 🚨 Solução de Problemas

### Erro: "ModuleNotFoundError"
```bash
# Certifique-se de estar no ambiente virtual
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: "Connection refused" (Redis/PostgreSQL)
```bash
# Verifique se os serviços estão rodando
sudo systemctl status redis
sudo systemctl status postgresql

# Ou com Docker
docker-compose ps
```

### Erro: "API Key not configured"
```bash
# Verifique se as chaves estão no .env
cat .env | grep API_KEY

# Reinicie o serviço após configurar
docker-compose restart app
```

### Erro: "Permission denied" (Docker)
```bash
# Adicione seu usuário ao grupo docker
sudo usermod -aG docker $USER
# Faça logout e login novamente
```

### Performance Lenta
```bash
# Verifique recursos do sistema
docker stats

# Ajuste workers do Celery
docker-compose up --scale celery-worker=3

# Otimize configuração PostgreSQL
# Edite postgresql.conf:
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
```

## 🔒 Segurança em Produção

### 1. Configure SSL/HTTPS
```bash
# Gere certificados SSL
sudo certbot --nginx -d seu-dominio.com

# Ou use certificados customizados no nginx.conf
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

### 2. Configure Firewall
```bash
# Ubuntu UFW
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw deny 8000   # API interna
sudo ufw deny 5432   # PostgreSQL
sudo ufw deny 6379   # Redis
```

### 3. Configure Autenticação
```python
# Em produção, implemente JWT
# Veja documentação da API para exemplos
```

### 4. Monitore Logs
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/geek-content

# Monitore com ferramentas como ELK Stack ou Grafana
```

## 📈 Monitoramento

### Métricas Básicas
```bash
# Health check
curl http://localhost:8000/health

# Analytics
curl http://localhost:8000/api/v1/analytics/overview

# Status das fontes
curl http://localhost:8000/api/v1/sources
```

### Alertas
```bash
# Configure alertas para:
# - Fontes com muitos erros
# - Score de qualidade baixo
# - Performance degradada
# - Uso excessivo de API
```

## 🆘 Suporte

- **Documentação:** http://localhost:8000/docs
- **Issues:** https://github.com/seu-usuario/geek-content-generator/issues
- **Wiki:** https://github.com/seu-usuario/geek-content-generator/wiki

## 🎯 Próximos Passos

1. **Configure suas fontes** de conteúdo favoritas
2. **Personalize as personas** editoriais
3. **Integre com sua plataforma** via API
4. **Configure webhooks** para notificações
5. **Monitore métricas** de qualidade
6. **Otimize performance** conforme necessário

---

**🎮 Pronto para gerar conteúdo geek incrível! 🚀**