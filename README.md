# Universal API Bridge

A lightweight, robust, and fully dynamic Flask application designed to bridge GPS and Telemetry data from internal Partner APIs (Source) to any external Client APIs (Destination). 

The app features a fully dynamic **Multi-Page Architecture** that allows you to construct any nested JSON payload structure on the fly without hardcoding specific vendor templates.

## Architecture Overview (MVC-S)

This application adheres to a clean, scalable **Model-View-Controller + Service (MVC-S)** architecture:
- **Models (`/models`)**: Defines the data schema (Templates, Configurations, Jobs) and database interactions using SQLite.
- **Views (`/templates` & `/static`)**: Completely modularized presentation layer. Server-side HTML logic is isolated in `templates/`, while client-side styles and Alpine.js reactivity logic are cleanly separated into `static/css/` and `static/js/` for optimal caching and browser performance.
- **Controllers (`/controllers`)**: Minimalist API route handlers that act as traffic cops between the Views and Services.
- **Services (`/services`)**: Heavy lifting and business logic (like background task scheduling, external API fetching, and dynamic payload parsing) are decoupled from the controllers here.

## Quick Start

### 1. Prerequisites
- Python 3.12+

### 2. Installation & Setup
Run the following commands in the root directory:

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r bridge_app/requirements.txt
```

**Linux/macOS**
```bash
python -m venv venv
source venv/bin/activate
pip install -r bridge_app/requirements.txt
```

### 3. Running the Server
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
This is the 2-pane configuration builder where you construct mappings from scratch.

**Step 1: Partner Source Setup (Left Pane)**
- Support for **Multi-Source Data Generation**. You can add multiple endpoints, and their fields will be uniquely prefixed (e.g., `source_0.field`, `source_1.field`) to avoid collisions.
- Select a Source API or provide a Source URL.
- Enter your Bearer token if required.

**Step 2: Client Destination Setup (Right Pane)**
- Enter the Client's API URL and Auth token.
- **Dynamic Payload Builder**: Build your mapping row by row. Select the source field on the left, and type the exact destination key name on the right. 

**Step 3: Save**
- Provide a Template Name.
- Configure the schedule interval in seconds at the bottom.
- Click "Save Config & Schedule" to immediately start the background feed.

### 3. Templates Manager (`/templates`)
This page manages your saved configurations (templates).
- **Edit**: Opens a unified popup modal where you can edit Template Name, Auth Keys, and Field Mappings inline. Includes robust fallback support for legacy data mapping strings.
- **Clone**: Opens a unified popup modal pre-filled with the source configuration and mappings of the cloned template. The Destination fields are intentionally left blank so you can quickly route the same feed to a new client. Includes a toggle to overwrite the inherited Source API key if needed.

## Telemetry
The app is fully instrumented with OpenTelemetry. Traces for HTTP requests and background jobs are printed to the console (for MVP debugging).
