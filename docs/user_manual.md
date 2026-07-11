# 📖 Beginner's Guide to the Synora Connect

Welcome! This guide is written for complete beginners. If you want to take data from an internal system (like your GPS tracker) and push it to an external client without writing code, you are in the right place!

---

## 🚦 Phase 1: Creating a Configuration (The Blueprint)

Before the bridge can send data, you have to tell it **where to get it**, **how it should look**, and **how often to run**.

1. Go to your browser and open `http://127.0.0.1:5000`
2. Click the **"+ New Schedule"** button on the Dashboard.
3. You will see a screen divided into two sides: **Source (Left)** and **Destination (Right)**.

### The Left Side (Getting Data)
You can now pull data from multiple different APIs simultaneously!
1. **Source API**: Select an API from the dropdown or paste a custom URL.
2. **Auth Key**: If required, type the API token here.
3. **+ Add Endpoint**: Need to combine GPS data with fuel data from a different URL? Click this button to add another API endpoint to your feed.

### The Right Side (Formatting Data)
Now we have to translate your data into the exact format the client requested.

**First, choose your Execution Mode:**
- **Push** — The bridge pushes data to the client on a schedule.
- **Pull REST** — The bridge generates a live REST API endpoint (with Swagger UI) that the client can call whenever they want.
- **Pull GraphQL** — The bridge generates a GraphQL Playground IDE with a dynamic schema.

**Then, configure your destinations:**
1. **Push mode**: Enter the Destination URL, select the HTTP method (POST/PUT/PATCH), and configure auth if needed.
2. **Pull REST/GraphQL mode**: Enter a Destination Name (e.g., "Client Endpoint 1"). This name is used to generate the URL slug for the auto-generated endpoint.
3. **Multiple Destinations**: Click **"+ Add Destination"** to route the same source data to multiple clients simultaneously.
4. **Field Mapping**: For each destination, click **"+ Add Field"**. Select the Source field from the dropdown (multi-source fields are prefixed like `source_0.gps_data` and `source_1.fuel_data` so you know exactly which endpoint they came from). Then, type exactly what the Client wants that field to be named in the Target field box.
5. **Schedule**: At the bottom, type in an **Interval** (in seconds). If you type `20`, the bridge will push data every 20 seconds.
6. Click **"Save Config & Schedule"**.

---

## ⚙️ Phase 2: Managing Schedules and Templates

### The Schedule Dashboard
The main homepage of the app (`http://127.0.0.1:5000`) is your **Schedule Dashboard**.
Here you can:
- See all active background feeds.
- Monitor the exact time they last pushed data.
- Click **Start** or **Stop** to pause an active feed without deleting it.

### The Templates Manager
If you click **Templates** in the top navigation bar, you can manage the reusable configurations you've built. Templates are grouped by execution mode (Push, Pull REST, Pull GraphQL).
- **Edit**: Clicking Edit opens a popup where you can rename your template, change the API keys, or adjust your Field Mappings instantly.
- **Edit as New**: Opens the full Create page pre-filled with data from an existing template. This lets you create a variation without modifying the original.
- **Clone**: This is a massive time-saver. If you have a completely mapped out GPS feed and you want to send it to a *new* client, click **Clone**. A popup will appear perfectly pre-filled with your Source config and Mappings. All you have to do is type in the new Destination URL and hit Save!
- **Swagger UI** (Pull REST only): Click this button to open a fully interactive Swagger documentation page for your template's REST endpoints.
- **GraphQL IDE** (Pull GraphQL only): Click this button to open the GraphQL Playground where you can write and test queries against your dynamic schema.
- **Delete**: Removes the template and all associated scheduled jobs.

---

## 📊 Phase 3: Viewing API Usage (OpenTelemetry)

You installed **OpenTelemetry** into this application. Why? Because you need to know exactly how much data is flowing through your bridge (API Usage). 

Every time the bridge wakes up and pushes data, OpenTelemetry records a "Trace" (a receipt of the transaction). 

### How to see your API Usage right now:
Currently, the app is running in "Development Mode". 
If you look at the black terminal screen where you typed `python synora_connect.py`, you will see OpenTelemetry printing out detailed receipts every time a job runs. It shows exactly how long the API took to respond, what URL was hit, and the status code.

### How to see your API Usage in the future:
When you are ready to put this app on a real server for production, you can connect OpenTelemetry to a visual dashboard (like **Grafana**, **Jaeger**, or **Zabbix**). 
Simply edit the `config.ini` file in the root directory to point the `exporter_endpoint` to your Zabbix or Jaeger server.

---

## 🔒 Phase 4: Advanced Features & Security

### 1. The API Mock Server (For Frontend Developers)
If you are building a frontend (like a React or Vue app) and you need to test it against an API that isn't finished yet, you can use the built-in **Mock Server**.
- Every OpenAPI 3.0.3 / Swagger Connection you save automatically generates a live REST API endpoint at: `http://127.0.0.1:5000/api/mock/<connection_id>/<your_path>`
- **CORS** is fully enabled, meaning your external React/Vue app can fetch data from this URL without getting blocked by the browser.

### 2. Custom Environments
In the "Advanced Settings" tab when adding an OpenAPI 3.0.3 / Swagger connection, you can define a custom JSON array of environment URLs.
- Example: `[{"name": "Production", "url": "https://api.prod.com"}, {"name": "Staging", "url": "https://api.stage.com"}]`
- Once saved, a dropdown will appear in the UI allowing you to instantly switch between testing against Staging or Production.

### 3. AES-256-GCM Token Encryption (Security)
If your APIs require highly sensitive Auth Tokens, you do not need to worry about them being stolen from the database.
- The first time the app starts, it generates a hyper-secure **Master Key** in your `.env` file (`ENCRYPTION_KEY=...`).
- When you type an Auth Token into the UI, it is instantly encrypted using **AES-256-GCM** before touching the database.
- **IMPORTANT**: Back up your `.env` file! If you lose your `ENCRYPTION_KEY`, you will permanently lose access to decrypt your API tokens.
