# 🏗️ System Architecture

## Overview

Astra Genesis WishCatcher follows a **microservices-inspired modular architecture** with clear separation of concerns, making it scalable, maintainable, and testable.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                         │
│                    (Next.js Frontend)                        │
│  • React Components                                          │
│  • TypeScript Type Safety                                    │
│  • Tailwind CSS Styling                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        API GATEWAY                           │
│                    (FastAPI Router)                         │
│  • Request Validation                                        │
│  • Authentication (Future)                                   │
│  • Rate Limiting (Future)                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         WishCatcher Engine (NLP Pipeline)            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │   │
│  │  │   Scraper    │→ │   Parser     │→ │  Detector │  │   │
│  │  │  (Context)   │  │  (Intent)    │  │ (Proactive)│  │   │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │   │
│  │         │                │                  │           │   │
│  │         └────────────────┴──────────────────┘          │   │
│  │                        │                                │   │
│  │                        ▼                                │   │
│  │              ┌──────────────────┐                       │   │
│  │              │  Analyzer Layer  │                       │   │
│  │              │  • Market Research                       │   │
│  │              │  • Prioritization                        │   │
│  │              │  • Feedback Loop                         │   │
│  │              └──────────────────┘                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Product Gap Finder                            │   │
│  │  • Multi-marketplace Scraper                         │   │
│  │  • Gap Detector                                      │   │
│  │  • FBA Calculator                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Software Gap Finder                          │   │
│  │  • Existence Validator                               │   │
│  │  • Gap Detector                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Astra Genesis (Business Generator)           │   │
│  │  • Business Plan Generator                           │   │
│  │  • MVP Structure Generator                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        DATA LAYER                            │
│  • Wish Storage (JSON)                                      │
│  • Product Gap Storage                                       │
│  • Software Gap Storage                                      │
│  • Business Plan Storage (MD + PDF)                         │
│  • MVP Storage (ZIP)                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. WishCatcher Engine

#### Context Collector (`wishcatcher/scraper/`)
- **Responsibility**: Collects context from multiple sources
- **Sources**: Reddit, Quora, Indie Hackers, Hacker News, Romanian forums
- **Pattern**: Async scraping with rate limiting
- **Output**: `RedditContext` objects with metadata

#### Intent Parser (`wishcatcher/parser/`)
- **Responsibility**: Detects user intent from text
- **Methods**:
  - Pattern matching (regex)
  - Semantic analysis (spaCy)
  - Context combination
- **Output**: Structured intent data with confidence scores

#### Proactive Detectors (`wishcatcher/detector/`)
- **ProactiveWishDetector**: Detects wishes from frustration patterns
- **ImplicitIntentDetector**: Extracts wishes from actions
- **WorkaroundDetector**: Finds wishes from user hacks
- **ConversationalAnalyzer**: Analyzes full conversation threads
- **ComparisonAnalyzer**: Extracts wishes from product comparisons

#### Analyzers (`wishcatcher/analyzer/`)
- **MarketResearchValidator**: Validates wishes with external data
- **SmartPrioritizer**: Multi-factor prioritization
- **FeedbackLoop**: Learns from successful wishes
- **NegativeSpaceAnalyzer**: Identifies market gaps

#### Extractors (`wishcatcher/extractor/`)
- **PreciseContextExtractor**: Filters garbage, extracts entities
- **RealityChecker**: Validates wish feasibility

### 2. Product Gap Finder

#### Multi-Marketplace Scraper
- **eMAG Scraper**: Romanian e-commerce
- **Amazon UK Scraper**: Uses PA-API 5.0 (official API)
- **Altex/PCGarage**: Romanian tech stores
- **Output**: Product data with prices, availability

#### Gap Detector
- **Price Gap Detection**: Identifies price differences
- **Availability Gap**: Finds missing products
- **Profitability Analysis**: Calculates profit margins

#### FBA Calculator
- **Cost Calculation**: Amazon FBA fees
- **Profit Margin**: Net profit analysis
- **ROI Estimation**: Return on investment

### 3. Software Gap Finder

#### Existence Validator
- **GitHub API**: Checks for open-source alternatives
- **App Store**: iOS app validation
- **Google Play**: Android app validation
- **Product Hunt**: Startup validation

#### Gap Detector
- **Missing Software**: No existing solution
- **Low Quality**: Existing but poor quality
- **Feature Gap**: Missing specific features
- **Localization Gap**: Not available in target market

### 4. Astra Genesis

#### Business Plan Generator
- **LLM-Powered**: Uses structured prompts
- **Sections**: Executive summary, market analysis, financials
- **Output**: Markdown + PDF

#### MVP Structure Generator
- **Code Scaffolding**: Generates project structure
- **Boilerplate**: FastAPI, Next.js templates
- **Output**: ZIP archive with full project

---

## Data Flow

### Wish Collection Flow

```
1. User Request → API Gateway
2. Context Collector → Scrape multiple sources
3. Intent Parser → Detect intent from text
4. Proactive Detectors → Find implicit wishes
5. Reality Checker → Filter impossible wishes
6. Precise Context Extractor → Extract entities
7. Market Research Validator → Validate with external data
8. Smart Prioritizer → Score and prioritize
9. Storage → Save to JSON
10. Background Tasks → Process gaps (async)
```

### Product Gap Detection Flow

```
1. Wish Data → Product Extractor
2. Product Name Extraction → NLP + Pattern matching
3. Multi-Marketplace Scraper → Search eMAG, Amazon UK
4. Gap Detector → Compare prices/availability
5. FBA Calculator → Calculate profitability
6. Storage → Save gaps
```

### Business Plan Generation Flow

```
1. Wish Data → Business Plan Generator
2. Structured Data Extraction → What, why, who, when, how
3. LLM Prompt Construction → Structured prompts
4. Business Plan Generation → Sections generation
5. PDF Conversion → Markdown → PDF
6. Storage → Save MD + PDF
```

---

## Design Patterns

### 1. **Strategy Pattern**
- Different intent detection strategies (pattern, semantic, context)
- Different gap detection strategies (product, software)

### 2. **Factory Pattern**
- Storage factories for different data types
- Generator factories for different outputs

### 3. **Observer Pattern**
- Background tasks observe wish creation events
- Feedback loop observes successful wishes

### 4. **Chain of Responsibility**
- NLP pipeline: Scraper → Parser → Detector → Analyzer
- Validation chain: Reality Check → Precise Context → Market Validation

### 5. **Repository Pattern**
- Storage abstraction (JSON now, DB later)
- Clean separation of data access logic

---

## Scalability Considerations

### Current Architecture
- **Stateless API**: FastAPI is stateless, can scale horizontally
- **Async Processing**: Background tasks don't block requests
- **File-based Storage**: Simple but limited scalability

### Future Improvements
- **Database Migration**: PostgreSQL for better scalability
- **Message Queue**: Redis/RabbitMQ for background tasks
- **Caching Layer**: Redis for frequently accessed data
- **Load Balancing**: Nginx for multiple API instances
- **Containerization**: Docker for easy deployment

---

## Security Considerations

### Current
- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: Comprehensive error handling prevents information leakage
- **CORS**: Configured for frontend origin only

### Future
- **Authentication**: JWT tokens
- **Rate Limiting**: Prevent abuse
- **API Keys**: Secure storage for external APIs
- **HTTPS**: SSL/TLS encryption

---

## Testing Strategy

### Unit Tests (Future)
- Test individual components in isolation
- Mock external dependencies

### Integration Tests (Future)
- Test API endpoints
- Test data flow between components

### End-to-End Tests (Future)
- Test complete user workflows
- Test error scenarios

---

## Monitoring & Observability (Future)

- **Logging**: Structured logging with levels
- **Metrics**: Request counts, processing times
- **Tracing**: Distributed tracing for debugging
- **Alerting**: Error rate alerts

---

## Deployment Architecture (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
│                            (Nginx)                            │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│   API Instance 1     │        │   API Instance 2     │
│    (FastAPI)         │        │    (FastAPI)         │
└──────────────────────┘        └──────────────────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database (PostgreSQL)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Message Queue (Redis)                    │
│              Background Task Processing                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Choices Rationale

### FastAPI
- **Async Support**: High performance for I/O-bound operations
- **Type Safety**: Pydantic integration
- **Auto Documentation**: OpenAPI/Swagger generation
- **Modern**: Python 3.10+ features

### spaCy
- **Production-Ready**: Industrial-strength NLP
- **Multilingual**: Romanian + English support
- **Fast**: Optimized Cython implementation
- **Extensible**: Custom pipelines

### Next.js
- **SSR**: Server-side rendering for SEO
- **TypeScript**: Type safety
- **Modern**: React 18+ features

### JSON Storage (Current)
- **Simple**: Easy to start
- **Portable**: No database setup needed
- **Migration Path**: Easy to migrate to PostgreSQL

---

## Performance Optimizations

### Current
- **Async Processing**: Non-blocking I/O
- **Background Tasks**: Don't block API responses
- **Lazy Loading**: Load models only when needed

### Future
- **Caching**: Redis for frequently accessed data
- **Database Indexing**: Optimize queries
- **CDN**: Static asset delivery
- **Connection Pooling**: Database connections

---

## Conclusion

This architecture provides:
- ✅ **Modularity**: Easy to understand and modify
- ✅ **Scalability**: Can scale horizontally
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Testability**: Components can be tested in isolation
- ✅ **Extensibility**: Easy to add new features
