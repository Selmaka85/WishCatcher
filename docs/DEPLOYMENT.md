# 🚀 Deployment Guide

## Current Setup

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy models
python -m spacy download ro_core_news_sm
python -m spacy download en_core_web_sm

# Run server
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Production Deployment (Future)

### Option 1: Docker Deployment

#### Dockerfile (Backend)
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models
RUN python -m spacy download ro_core_news_sm
RUN python -m spacy download en_core_web_sm

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Dockerfile (Frontend)
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "start"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/wishcatcher
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=wishcatcher
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Option 2: Cloud Deployment

#### AWS (EC2 + RDS)
1. Launch EC2 instance
2. Install Docker
3. Deploy with docker-compose
4. Use RDS for PostgreSQL
5. Use ElastiCache for Redis

#### Heroku
```bash
# Backend
heroku create wishcatcher-backend
heroku addons:create heroku-postgresql
git push heroku main

# Frontend
heroku create wishcatcher-frontend
git push heroku main
```

#### Vercel (Frontend)
```bash
cd frontend
vercel deploy
```

#### Railway
1. Connect GitHub repository
2. Select backend/frontend
3. Configure environment variables
4. Deploy

---

## Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/wishcatcher

# Redis
REDIS_URL=redis://localhost:6379

# Amazon PA-API
AMAZON_ACCESS_KEY=your_access_key
AMAZON_SECRET_KEY=your_secret_key
AMAZON_PARTNER_TAG=your_partner_tag

# API Keys (Future)
GOOGLE_TRENDS_API_KEY=your_key
SIMILARWEB_API_KEY=your_key

# Security
SECRET_KEY=your_secret_key
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Database Migration

### Current: JSON Files
- Simple, no setup required
- Good for development
- Limited scalability

### Future: PostgreSQL

#### Schema Design
```sql
-- Wishes table
CREATE TABLE wishes (
    id VARCHAR PRIMARY KEY,
    intent TEXT NOT NULL,
    intent_full TEXT,
    domain VARCHAR,
    score FLOAT,
    business_score FLOAT,
    priority_score FLOAT,
    structured JSONB,
    source VARCHAR,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Product gaps table
CREATE TABLE product_gaps (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR,
    category VARCHAR,
    emag_price FLOAT,
    amazon_price FLOAT,
    profit_margin FLOAT,
    opportunity_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Software gaps table
CREATE TABLE software_gaps (
    id SERIAL PRIMARY KEY,
    software_name VARCHAR,
    gap_type VARCHAR,
    opportunity_score FLOAT,
    validation_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Migration Script
```python
# backend/migrations/migrate_to_postgres.py
import json
import psycopg2
from app.storage.wish_storage import WishStorage

def migrate_wishes():
    # Load from JSON
    wish_storage = WishStorage()
    wishes = wish_storage.load_all_wishes()
    
    # Insert into PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    for wish in wishes:
        cur.execute("""
            INSERT INTO wishes (id, intent, intent_full, domain, score, ...)
            VALUES (%s, %s, %s, %s, %s, ...)
        """, (wish.id, wish.intent, ...))
    
    conn.commit()
    conn.close()
```

---

## Monitoring & Observability

### Logging
```python
# backend/app/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("wishcatcher")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    "logs/wishcatcher.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Metrics (Future)
- Prometheus for metrics collection
- Grafana for visualization
- Custom metrics:
  - Request count
  - Processing time
  - Error rate
  - Wish detection accuracy

### Health Checks
```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": check_database(),
        "redis": check_redis(),
        "spacy_models": check_spacy_models()
    }
```

---

## CI/CD Pipeline (Future)

### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: docker/build-push-action@v2
      - run: docker-compose up -d
```

---

## Security Checklist

- [ ] Environment variables for secrets
- [ ] HTTPS/SSL certificates
- [ ] Rate limiting
- [ ] Input validation
- [ ] SQL injection prevention (when using DB)
- [ ] CORS configuration
- [ ] Authentication/Authorization (future)
- [ ] API key rotation

---

## Performance Optimization

### Caching
```python
# Use Redis for caching
import redis
r = redis.Redis(host='localhost', port=6379)

# Cache expensive operations
@cache(ttl=3600)
def expensive_operation():
    ...
```

### Database Indexing
```sql
CREATE INDEX idx_wishes_domain ON wishes(domain);
CREATE INDEX idx_wishes_timestamp ON wishes(timestamp);
CREATE INDEX idx_product_gaps_category ON product_gaps(category);
```

### Async Processing
- Background tasks for heavy operations
- Message queue for scalability
- Connection pooling

---

## Backup Strategy

### Current (JSON Files)
```bash
# Backup script
tar -czf backup_$(date +%Y%m%d).tar.gz backend/data/
```

### Future (PostgreSQL)
```bash
# Automated backups
pg_dump -h localhost -U user -d wishcatcher > backup.sql
```

---

## Troubleshooting

### Common Issues

1. **spaCy models not found**
   ```bash
   python -m spacy download ro_core_news_sm
   python -m spacy download en_core_web_sm
   ```

2. **Port already in use**
   ```bash
   # Change port in uvicorn command
   uvicorn app.main:app --port 8001
   ```

3. **CORS errors**
   - Check `ALLOWED_ORIGINS` in backend
   - Verify frontend URL matches

4. **Import errors**
   ```bash
   # Ensure you're in the correct directory
   cd backend
   python -m app.main
   ```

---

## Next Steps

1. **Database Migration**: Move from JSON to PostgreSQL
2. **Docker Deployment**: Containerize application
3. **CI/CD**: Set up automated testing and deployment
4. **Monitoring**: Add Prometheus/Grafana
5. **Scaling**: Load balancing, horizontal scaling
6. **Security**: Authentication, rate limiting

---

## Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
