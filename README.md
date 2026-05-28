# Retail Intelligence System (RIS)

The Retail Intelligence System (RIS) is a modern, AI-powered backend microservice designed to harvest, process, store, and serve retail and wholesale intelligence. Developed as an API for the Thola Mobile application, it orchestrates web scraping, visual reasoning, geographic data aggregation, and AI-driven recommendations to help Small and Medium Enterprises (SMEs), particularly Spaza shop owners, make data-driven procurement and pricing decisions.

## 🚀 What the System Does

RIS operates in two primary phases:
1. **Ingestion Pipeline**: Asynchronously scrapes wholesale e-commerce sites (via Playwright) and parses regional retail promotional leaflets (via PDFs). It leverages Google Gemini AI to visually reason and extract structured data (item, price, category, etc.) from unstructured HTML and PDFs, storing the intelligence in Supabase.
2. **Serving Pipeline**: A Fast API backend that serves endpoints (e.g., `/v1/recommend`) which accept a user's location and budget. It queries local supermarket locations via the Overpass API (OpenStreetMap), cross-references this with the ingested corporate retail specials and wholesale prices, and uses Gemini AI to generate a curated procurement plan.

## 🏛️ System Architecture

The architecture decouples heavy asynchronous data ingestion from the fast user-facing API.

```mermaid
graph TD
    %% Clients
    Client[Client Applications <br/> Thola Mobile App / Web Dashboard]
    
    %% Core Backend
    subgraph "Backend System (FastAPI)"
        API[FastAPI Endpoints <br/> /v1/recommend]
        DataLayer[Data Layer Service <br/> data_layer.py]
        LocService[Location Service <br/> Overpass API Integration]
        
        subgraph "Ingestion Engine"
            RunScrapers[run_scrapers.py <br/> Orchestrator]
            
            subgraph "Scrapers"
                Playwright[Playwright + BS4 Scrapers <br/> Wholesale Sites]
                PDF[PDF Reasoning Scrapers <br/> Retail Flyers]
            end
            
            AIEngine[AI Engine <br/> Gemini Pro/Flash]
        end
    end

    %% External Systems & APIs
    subgraph "External Providers"
        Websites[Wholesale E-commerce Sites]
        PDFLeaflets[Regional Retail PDFs]
        Overpass[OpenStreetMap / Overpass API]
        Gemini[Google Gemini API]
    end

    %% Database
    subgraph "Supabase Database"
        DB_Wholesale[(wholesale_inventory)]
        DB_Retail[(retail_inventory)]
    end

    %% Architecture Flow
    Client -->|HTTP POST /v1/recommend| API
    API --> DataLayer
    DataLayer --> LocService
    LocService -->|Query Supermarkets| Overpass
    DataLayer -->|Query Corporate Specials| DB_Retail
    
    RunScrapers --> Playwright
    RunScrapers --> PDF
    
    Playwright -->|Scrape HTML| Websites
    PDF -->|Download| PDFLeaflets
    
    Playwright -->|Clean HTML| AIEngine
    PDF -->|Raw PDF| AIEngine
    
    AIEngine -->|Extract Structured Data| Gemini
    
    Playwright -->|Save Data| DB_Wholesale
    PDF -->|Save Data| DB_Retail
```

## 📊 Data Flow Diagram (DFD)

This diagram illustrates how raw external data is transformed into structured intelligence and served as recommendations to the SME owner.

```mermaid
flowchart LR
    %% External Entities
    E1[Wholesale Websites]
    E2[Retail PDFs]
    E3[OpenStreetMap]
    E4[SME Spaza Owner]

    %% Processes
    P1((1.0 <br> Web Scraping))
    P2((2.0 <br> Visual PDF Parsing))
    P3((3.0 <br> AI Structuring & Categorization))
    P4((4.0 <br> Location Mapping))
    P5((5.0 <br> Recommendation Synthesis))

    %% Data Stores
    D1[(D1: Wholesale Inventory)]
    D2[(D2: Retail Inventory)]

    %% Flow: Ingestion
    E1 -- Raw HTML/JSON --> P1
    E2 -- Raw PDF File --> P2
    
    P1 -- Unstructured Text --> P3
    P2 -- Unstructured Visuals --> P3
    
    P3 -- Structured Wholesale Data --> D1
    P3 -- Structured Retail Data --> D2

    %% Flow: Serving
    E4 -- Request Recommendations <br> (lat, lng, budget) --> P5
    P5 -- Query Coordinates --> P4
    E3 -- Real Supermarket Locations --> P4
    P4 -- Mapped Supermarkets --> P5
    
    D1 -- Wholesale Pricing --> P5
    D2 -- Local Retail Pricing --> P5
    
    P5 -- Curated Procurement Plan --> E4
```

## 🔄 State Diagram

The system operates across two main state cycles: the background ingestion process and the synchronous API request lifecycle.

```mermaid
stateDiagram-v2
    state "Data Ingestion Lifecycle" as Ingestion {
        [*] --> Idle_Ingestion
        Idle_Ingestion --> Scraping : Trigger (Cron/Manual)
        Scraping --> Parsing : Raw Data (HTML/PDF) Retrieved
        Parsing --> Structuring : Send to Gemini AI
        Structuring --> Storing : AI returns JSON
        Storing --> Idle_Ingestion : Save to Supabase
    }

    state "API Request Lifecycle" as API {
        [*] --> Idle_API
        Idle_API --> ValidatingRequest : POST /v1/recommend
        ValidatingRequest --> FetchingLocalData : Location Extracted
        FetchingLocalData --> FetchingPricing : Overpass API success
        FetchingPricing --> GeneratingRecommendation : DB Query Success
        GeneratingRecommendation --> ReturningResponse : Gemini AI Synthesis
        ReturningResponse --> Idle_API : JSON Response
    }
```

## ⏱️ Sequence Diagram

A typical sequence when the client application requests a tailored recommendation for an SME.

```mermaid
sequenceDiagram
    participant Client as Thola App
    participant API as FastAPI (/v1/recommend)
    participant DL as Data Layer
    participant OS as Overpass (Location)
    participant DB as Supabase
    participant AI as Gemini Engine

    Client->>API: POST /v1/recommend (Location, Budget, Preferences)
    API->>DL: Fetch context data
    DL->>OS: Query nearby supermarkets (lat, lng)
    OS-->>DL: Return local competitors
    DL->>DB: Query corporate retail specials
    DB-->>DL: Return retail inventory
    API->>DB: Query wholesale inventory (if Premium)
    DB-->>API: Return wholesale data
    API->>AI: Generate recommendation (combined data)
    AI-->>API: Structured curated procurement plan
    API-->>Client: 200 OK (Optimized Basket, Spend, Combos)
```

## 📱 Integration with TholaMobile

The RIS API is built to seamlessly integrate with the **[TholaMobile App](https://github.com/ThabisoM7/TholaMobile/tree/dev)**. Integration strategies include:

1. **Procurement Dashboard & Arbitrage Math**: TholaMobile features a dedicated RIS Intelligence screen where vendors can manage their business profile. When requesting `/v1/recommend`, the app can pass the vendor's actual `vendor_inventory` (what they pay for stock). RIS calculates exact profit margins based on these numbers, or falls back to a 5% supermarket undercut assumption if missing.
2. **Visual FlatLists**: Thanks to DuckDuckGo automated image fetching and BS4 zero-cost scraping, every item returned in the `optimized_basket` and `suggested_combos` includes a high-quality `image_url`. TholaMobile can display these beautifully in a native scrolling FlatList.
3. **Competitor Alert System**: Using the local retail data pulled from RIS, TholaMobile can push notifications to SMEs when a nearby corporate supermarket (e.g., Shoprite, Spar) drops prices on staple items, suggesting a temporary price match or alternative stock focus.
4. **Admin Upload Portal**: The RIS `/api/admin/upload-leaflet` endpoint can be integrated into an internal Thola administrative dashboard, allowing Thola staff to rapidly upload new wholesale and retail promotional PDFs for instant system updates.

## 🌟 Capabilities & Recent Optimizations

### Current Capabilities
- **Geospatial Radar (5km)**: Uses Overpass API to identify actual competitor supermarkets (`SPAR`, `Pick n Pay`, `Boxer`, `Shoprite`, `Checkers`) strictly within a 5000-meter radius of the user's latitude and longitude.
- **National Leaflet Logic**: A single promotional PDF (e.g., "SPAR specials") is intelligently applied to any physical store of that matching brand discovered nationwide, eliminating data duplication.
- **Cost-Optimized Web Scraping**: Wholesale sites are scraped using zero-cost Python heuristics (BeautifulSoup and Regex) rather than AI token consumption, natively extracting prices and product images.
- **DuckDuckGo Image AI**: For promotional PDFs that Gemini visually reads, the system runs a silent background search on DuckDuckGo to automatically grab relevant product pictures for the UI.
- **Multimodal AI Scraping**: Uses Gemini to visually read promotional PDFs without relying on fragile OCR or text extraction libraries.
- **Stabilized MOCK_MODE**: For hackathon or local development without live databases, RIS cleanly falls back to generated mock responses if `MOCK_MODE` is enabled, preventing crashes.
- **Tiered Intelligence**: Differentiates between standard users and premium SMEs by gating advanced wholesale insights.

### Possible Future Feature Integrations
- **Demand Forecasting**: Integrate historical sales data from TholaMobile to predict what inventory an SME will need next week, allowing RIS to proactively seek out wholesale deals for those specific items.
- **Crowdsourced Price Validation**: Allow TholaMobile users to confirm or correct pricing data directly in the app, feeding it back into the RIS Supabase instance to improve data accuracy.
- **Automated Order Fulfillment**: Connect the RIS API directly to wholesale suppliers' APIs (where available) so that once the SME approves the `optimized_basket`, TholaMobile can dispatch an order automatically.
- **WhatsApp Bot Integration**: Expose RIS recommendations through a WhatsApp conversational interface for SMEs who may have limited smartphone data or prefer chat-based interactions.
