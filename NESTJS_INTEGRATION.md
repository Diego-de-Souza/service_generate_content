# 🚀 Integração com API NestJS - Guia Completo

## ⚡ **Arquitetura Stateless**

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

**Fluxo:**
1. **NestJS** agenda cron jobs (3 dias/6h/semanal)
2. **Python Service** processa conteúdo (scraping + IA)
3. **Retorna dados** processados via JSON
4. **NestJS salva** no seu banco existente

## 🔌 **Service de Integração NestJS**

### **content-integration.service.ts**
```typescript
import { Injectable, Logger } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';

@Injectable()
export class ContentIntegrationService {
  private readonly logger = new Logger(ContentIntegrationService.name);
  private readonly pythonServiceUrl = 'http://content-processor:8000/api/v1/batch';
  
  constructor(
    private readonly articlesService: ArticlesService,
    private readonly newsService: NewsService,
    private readonly eventsService: EventsService
  ) {}
  
  // Sincroniza artigos a cada 3 dias
  @Cron('0 6 */3 * *')
  async syncArticles() {
    const categorias = ['animes', 'manga', 'filmes', 'studios', 'games', 'tech'];
    
    for (const categoria of categorias) {
      try {
        this.logger.log(`Sincronizando artigos de ${categoria}...`);
        
        const response = await this.callPythonService('/articles', {
          categoria,
          limit: 15,
          min_score: 0.7
        });
        
        await this.saveArticles(response.articles);
        this.logger.log(`✅ ${response.total_processed} artigos de ${categoria} sincronizados`);
        
        // Delay entre categorias para evitar sobrecarga
        await new Promise(resolve => setTimeout(resolve, 2000));
        
      } catch (error) {
        this.logger.error(`❌ Erro sincronizando ${categoria}:`, error.message);
      }
    }
  }
  
  // Sincroniza notícias a cada 6 horas
  @Cron('0 */6 * * *')
  async syncNews() {
    try {
      this.logger.log('Sincronizando notícias...');
      
      const response = await this.callPythonService('/news', {
        limit: 20,
        hours_ago: 6
      });
      
      await this.saveNews(response.news);
      this.logger.log(`✅ ${response.total_processed} notícias sincronizadas`);
      
    } catch (error) {
      this.logger.error('❌ Erro sincronizando notícias:', error.message);
    }
  }
  
  // Sincroniza eventos semanalmente
  @Cron('0 8 * * 0')  // Todo domingo às 8h
  async syncEvents() {
    try {
      this.logger.log('Sincronizando eventos...');
      
      const response = await this.callPythonService('/events', {
        limit: 30,
        days_ahead: 90
      });
      
      await this.saveEvents(response.events);
      this.logger.log(`✅ ${response.total_processed} eventos sincronizados`);
      
    } catch (error) {
      this.logger.error('❌ Erro sincronizando eventos:', error.message);
    }
  }
  
  private async saveArticles(articles: any[]) {
    let saved = 0;
    
    for (const article of articles) {
      try {
        // Verifica duplicata por título
        const existing = await this.articlesService.findByTitle(article.title);
        
        if (!existing) {
          await this.articlesService.create({
            categoria: article.categoria,
            title: article.title,
            description: article.description,
            text: article.text,
            summary: article.summary,
            keyWords: article.keyWords,
            original_url: article.original_url,
            source: article.source,
          });
          saved++;
        }
      } catch (error) {
        this.logger.error(`Erro salvando artigo "${article.title}":`, error.message);
      }
    }
    
    this.logger.log(`💾 ${saved} novos artigos salvos no banco`);
  }
  
  private async saveNews(news: any[]) {
    let saved = 0;
    
    for (const item of news) {
      try {
        const existing = await this.newsService.findByTitle(item.title);
        
        if (!existing) {
          await this.newsService.create({
            title: item.title,
            disclosure_date: new Date(item.disclosure_date),
          });
          saved++;
        }
      } catch (error) {
        this.logger.error(`Erro salvando notícia "${item.title}":`, error.message);
      }
    }
    
    this.logger.log(`💾 ${saved} novas notícias salvas no banco`);
  }
  
  private async saveEvents(events: any[]) {
    let saved = 0;
    
    for (const event of events) {
      try {
        const existing = await this.eventsService.findByTitle(event.title);
        
        if (!existing) {
          await this.eventsService.create({
            title: event.title,
            description: event.description,
            location: event.location,
            date_event: new Date(event.date_event),
            url_event: event.url_event,
          });
          saved++;
        }
      } catch (error) {
        this.logger.error(`Erro salvando evento "${event.title}":`, error.message);
      }
    }
    
    this.logger.log(`💾 ${saved} novos eventos salvos no banco`);
  }
  
  private async callPythonService(endpoint: string, payload: any) {
    const response = await fetch(`${this.pythonServiceUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      timeout: 120000  // 2 minutos timeout
    });
    
    if (!response.ok) {
      throw new Error(`Python service error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
  
  // Health check do serviço Python
  async checkPythonServiceHealth() {
    try {
      const response = await fetch(`http://content-processor:8000/health`);
      const health = await response.json();
      
      return {
        status: health.status,
        ready_for_batch: health.ready_for_batch,
        ai_services: health.ai_services
      };
    } catch {
      return { status: 'unhealthy' };
    }
  }
}
```

## 📊 **Entities TypeORM**

### **article.entity.ts**
```typescript
import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn } from 'typeorm';

@Entity('articles')
export class Article {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  categoria: string;  // animes, manga, filmes, studios, games, tech

  @Column()
  title: string;

  @Column('text')
  description: string;  // pequena descrição

  @Column('longtext')
  text: string;  // artigo completo

  @Column('text')
  summary: string;

  @Column('simple-array')
  keyWords: string[];

  @Column({ nullable: true })
  original_url?: string;

  @Column()
  source: string;

  @CreateDateColumn()
  createdAt: Date;
}
```

### **news.entity.ts**
```typescript
@Entity('news')
export class News {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  title: string;

  @Column()
  disclosure_date: Date;  // data de divulgação

  @CreateDateColumn()
  createdAt: Date;
}
```

### **event.entity.ts**
```typescript
@Entity('events')
export class Event {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  title: string;

  @Column('text')
  description: string;

  @Column()
  location: string;

  @Column()
  date_event: Date;

  @Column()
  url_event: string;

  @CreateDateColumn()
  createdAt: Date;
}
```

## 🛠️ **Module Configuration**

### **app.module.ts**
```typescript
import { Module } from '@nestjs/common';
import { ScheduleModule } from '@nestjs/schedule';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ContentIntegrationService } from './content-integration.service';
import { Article } from './entities/article.entity';
import { News } from './entities/news.entity';
import { Event } from './entities/event.entity';

@Module({
  imports: [
    ScheduleModule.forRoot(),  // Habilita cron jobs
    TypeOrmModule.forFeature([Article, News, Event]),
    // ... outras configurações
  ],
  providers: [ContentIntegrationService],
})
export class AppModule {}
```

## 🐳 **Docker Compose Integration**

### **docker-compose.yml**
```yaml
version: '3.8'

services:
  # Sua API NestJS
  nestjs-api:
    build: .
    ports: ["3000:3000"]
    depends_on: [postgres, content-processor]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/geek_db
  
  # Processador de conteúdo Python (stateless)
  content-processor:
    image: geek-content-processor
    ports: ["8000:8000"]
    environment:
      - STATELESS_MODE=true
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  
  # Seu banco PostgreSQL
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=geek_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

## 📈 **Monitoring & Health Checks**

### **health.controller.ts**
```typescript
@Controller('health')
export class HealthController {
  constructor(
    private readonly contentService: ContentIntegrationService
  ) {}

  @Get('content-processor')
  async checkContentProcessor() {
    return this.contentService.checkPythonServiceHealth();
  }

  @Get('sync-status')
  async getSyncStatus() {
    return {
      last_articles_sync: await this.getLastSync('articles'),
      last_news_sync: await this.getLastSync('news'),
      last_events_sync: await this.getLastSync('events'),
      total_articles: await this.articlesService.count(),
      total_news: await this.newsService.count(),
      total_events: await this.eventsService.count(),
    };
  }
}
```

## ✅ **Vantagens desta Arquitetura**

- **🔄 Separação clara**: NestJS (API/Business) + Python (IA/Scraping)
- **⚡ Performance**: Processamento paralelo e assíncrono
- **🛡️ Confiabilidade**: Fallback se Python service cair
- **📈 Escalabilidade**: Serviços independentes
- **💰 Custo**: Sem Redis, sem dependências pagas
- **🔧 Manutenibilidade**: Cada serviço na sua especialidade

## 🚀 **Setup Rápido**

1. **Configure Python Service**:
```bash
cd python-service
docker-compose up -d
```

2. **Configure sua API NestJS** com os services acima

3. **Teste integração**:
```bash
curl -X POST http://localhost:8000/api/v1/batch/articles \
  -H "Content-Type: application/json" \
  -d '{"categoria": "games", "limit": 5}'
```

**✅ Pronto! Sua API NestJS agora tem conteúdo geek alimentado por IA!** 🎮🤖