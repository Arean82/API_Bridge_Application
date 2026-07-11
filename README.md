# Universal API Bridge

A lightweight, robust, and fully dynamic Flask application designed to bridge data from internal Partner APIs (Source) to any external Client APIs (Destination). 

The app features a fully dynamic **Multi-Page Architecture** that allows you to construct any nested JSON payload structure on the fly without hardcoding specific vendor templates. It supports three execution modes: **Push** (scheduled data forwarding), **Pull REST** (auto-generated Swagger API endpoints), and **Pull GraphQL** (auto-generated GraphQL Playground IDE).

## Architecture Overview (MVC-S)

This application adheres to a clean, scalable **Model-View-Controller + Service (MVC-S)** architecture:
- **Models (`/models`)**: Defines the data schema (Templates, Configurations, Jobs) and database interactions using SQLite.
- **Views (`/templates` & `/static`)**: Completely modularized presentation layer. Server-side HTML logic is isolated in `templates/`, while client-side styles and reactivity logic are cleanly separated into `static/css/` and `static/js/` utilizing Vanilla JS for optimal caching and browser performance.
- **Controllers (`/controllers`)**: Minimalist API route handlers that act as traffic cops between the Views and Services.
- **Services (`/services`)**: Heavy lifting and business logic (like background task scheduling, external API fetching, AES-256-GCM encryption, and dynamic payload parsing) are decoupled from the controllers here.

## Advanced Features
- **AES-256-GCM Token Encryption**: All API auth tokens are safely encrypted in the database at rest using a 256-bit Master Key generated in your `.env` file.
- **OpenTelemetry Observability (OTLP)**: Natively instruments application traces and exports them via OTLP (compatible with Jaeger, Zabbix, or Datadog) using `config.ini`.
- **CORS-Enabled Mock Server**: Automatically generates functional `/api/mock/<id>/<path>` REST endpoints from OpenAPI 3.0.3 / Swagger configurations to serve static JSON examples to external frontends.
- **Dynamic Environments**: Configure multiple environment URLs (Dev/Staging/Prod) per connection and seamlessly switch between them in the UI.
- **Pull REST Mode**: Auto-generates live Swagger UI endpoints (`/api/bridge/pull/<slug>/<dest>/`) with full OpenAPI spec from your field mappings.
- **Pull GraphQL Mode**: Auto-generates a GraphQL Playground IDE (`/api/graphql/<slug>/<dest>/`) with a dynamic schema built from your field mappings.
- **Multi-Destination Support**: Each template supports multiple destination endpoints, each with independent field mappings, auth, and HTTP methods.

## Quick Start

### 1. Prerequisites
- Python 3.10+

### 2. Configuration (Required)
> [!IMPORTANT]
> Before running the application in a production environment, you must update `config.ini` with your database credentials (PostgreSQL or SQLite), environment mode, and host/port settings.

### 3. Installation & Setup
Run the following commands in the root directory:

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/macOS**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Running the Server
```bash
python run.py
```
Access the dashboard at `http://127.0.0.1:5000`


## Usage Guide

The application is split into three main areas to easily manage integrations.

### 1. Schedule Dashboard (`/`)
This is the default landing page. It acts as the central control panel for all active background feeds.
- Monitor active schedules, intervals, and last run times.
- Start or stop active jobs dynamically.
- Click "+ New Schedule" to jump to the configuration builder.

### 2. Create Configuration (`/templates/create`)
This is the configuration builder where you construct mappings from scratch.

> [!NOTE]
> Create is currently locked to prevent accidental template creation. Use **Edit** or **Edit as New** from the Templates Manager to modify existing configurations.

**Step 1: Select Execution Mode**
Choose one of the three execution modes:
- **Push** — The bridge fetches data from sources on a schedule and pushes it to destination URLs.
- **Pull REST** — The bridge auto-generates live Swagger REST endpoints that clients can call on-demand.
- **Pull GraphQL** — The bridge auto-generates a GraphQL Playground IDE with a dynamic schema.

**Step 2: Partner Source Setup**
- Support for **Multi-Source Data Aggregation**. Add multiple source endpoints, and their fields will be uniquely prefixed (e.g., `source_0.field`, `source_1.field`) to avoid collisions.
- Select a Source API from a connection or provide a Source URL.
- Enter your Bearer token if required.

**Step 3: Destination Setup**
- **Push mode**: Enter the Destination URL, HTTP method, auth type, and auth token for each destination.
- **Pull REST mode**: Provide a Destination Name (used to generate the URL slug) and HTTP method.
- **Pull GraphQL mode**: Provide a Destination Name (used to generate the URL slug).
- **Multiple Destinations**: Click "+ Add Destination" to route the same source data to multiple endpoints.
- **Field Mapping**: For each destination, click "+ Add Field". Select the source field from the dropdown and type the target field name.

**Step 4: Save**
- Provide a Template Name.
- Configure the schedule interval in seconds.
- Click "Save Config & Schedule" to activate.

> [!TIP]
> **Extreme Scaling & Multi-Node Clusters**
> If you are deploying to a production cluster or need to process thousands of endpoints simultaneously across multiple servers, the API Bridge supports distributed execution via Redis (Linux) and Memurai (Windows).
> 
> See the [Distributed Execution & Scaling Guide](SCALING_REDIS_MEMURAI.md) for setup instructions.

### 3. Templates Manager (`/templates`)
This page manages your saved configurations (templates), grouped by execution mode.
- **Edit**: Opens a popup modal where you can edit Template Name, Auth Keys, Destinations, and Field Mappings inline.
- **Edit as New**: Opens the full Create page pre-filled with data from an existing template, allowing you to create a variation without modifying the original.
- **Clone**: Opens a popup modal pre-filled with the source configuration. The Destination fields are intentionally left blank so you can quickly route the same feed to a new client.
- **Swagger UI** (Pull REST only): Opens the auto-generated Swagger UI documentation for the template's REST endpoints.
- **GraphQL IDE** (Pull GraphQL only): Opens the auto-generated GraphQL Playground for the template's GraphQL endpoints.
- **Delete**: Removes the template and all associated scheduled jobs.

## Telemetry
The app is fully instrumented with OpenTelemetry. Traces for HTTP requests and background jobs are printed to the console (for MVP debugging).
