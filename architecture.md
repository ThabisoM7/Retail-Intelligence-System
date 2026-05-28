# Retail Intelligence System (RIS) Architecture

This document provides a high-level overview of the system architecture and data flow for the Retail Intelligence System (RIS).

## System Architecture

The RIS architecture is designed to harvest, process, store, and serve retail and wholesale intelligence. It uses a modern Python-based backend to orchestrate web scraping, visual reasoning, and geographic data aggregation.

```mermaid
graph TD
    %% Clients
    Client[Client Applications <br/> Web Dashboard / Mobile App]
    
    %% Core Backend
    subgraph "Backend System (FastAPI)"
        API[FastAPI Endpoints <br/> /api/recommendations]
        DataLayer[Data Layer Service <br/> app/services/data_layer.py]
        LocService[Location Service <br/> Overpass API Integration]
        
        subgraph "Ingestion Engine"
            RunScrapers[run_scrapers.py <br/> Orchestrator]
            
            subgraph "Scrapers"
                Playwright[Playwright + BS4 Scrapers <br/> KitKat, BigSave, RedStar]
                PDF[PDF Reasoning Scrapers <br/> Shoprite, Spar, Devland]
            end
            
            AIEngine[AI Engine <br/> Gemini 1.5 Pro/Flash]
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
    Client -->|HTTP GET /api/recommendations| API
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
    PDF -->|Save Data| DB_Wholesale
```

> [!NOTE]
> The backend decouples the **Ingestion Pipeline** (which runs asynchronously or via a cron job) from the **Serving Pipeline** (FastAPI) to ensure that the user-facing dashboard remains fast and responsive.

<br>

## Data Flow Diagram (DFD)

The Data Flow Diagram illustrates how information moves from raw external sources, gets transformed by our AI engine, is persisted, and is finally synthesized into actionable intelligence for SMEs.

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
    E4 -- Request Recommendations <br> (lat, lng) --> P5
    P5 -- Query Coordinates --> P4
    E3 -- Real Supermarket Locations --> P4
    P4 -- Mapped Supermarkets --> P5
    
    D1 -- Wholesale Pricing --> P5
    D2 -- Local Retail Pricing --> P5
    
    P5 -- Curated Procurement Plan --> E4
```

> [!TIP]
> **Process 3.0 (AI Structuring & Categorization)** is the core intelligence layer. Instead of fragile CSS selectors, we pass raw HTML/PDFs to Gemini. It structurally identifies the `item`, normalizes the `price`, determines the `category` (e.g., *Wholesale Staples*, *Toiletries*), and generates an `estimated_markup_potential`.

### Key Components Explained:
- **Ingestion Orchestrator (`run_scrapers.py`)**: Responsible for clearing old tables and kicking off scrapers.
- **AI Engine (`ai_engine.py`)**: Uses `google-generativeai`. It uses two distinct strategies: `extract_products_from_html` and `extract_products_from_pdf_url`.
- **Location Service (`location_service.py`)**: Dynamically queries OpenStreetMap nodes tagged with `shop=supermarket` to anchor the retail prices to a physical competitor near the SME.
- **Data Layer (`data_layer.py`)**: Synthesizes the data. It binds the physical locations (from Overpass) to the retail catalog (from Supabase) to deliver an exact "what your local competitors are charging" report.
