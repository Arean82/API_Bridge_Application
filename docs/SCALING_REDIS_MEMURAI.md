# Distributed Execution & Scaling

To achieve extreme scaling (hundreds of parallel processes and thousands of concurrent APIs), you can configure the Synora Bridge to use **Redis** (on Linux) or **Memurai** (on Windows) as its central task broker.

By doing this, you can run `python synora_connect.py` (or the compiled `.exe`) on multiple different servers simultaneously. Redis acts as a distributed lock—ensuring that if a scheduled job triggers, only *one* of the servers picks it up and processes it, preventing duplicate data pushes.

**Note:** Redis/Memurai is used *strictly* for background task coordination. Your application data (Templates, Jobs, Settings) will continue to live securely in your SQLite or PostgreSQL database.

---

## 1. Setting Up the Datastore

### Option A: Linux (Redis)
Redis is native to Linux and is the industry standard.
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Option B: Windows (Memurai)
Native Redis does not exist for Windows. Memurai is a 100% Redis-compatible datastore built specifically for Windows.
1. Download the Developer Edition from [Memurai.com](https://www.memurai.com/get-memurai).
2. Run the `.msi` installer.
3. It will automatically install and run as a Windows Service on port `6379`.

---

## 2. Securing Your Datastore (Highly Recommended)

By default, Redis and Memurai allow open access without a password, which is a security risk in production.

### A. Set a Password
1. Locate your configuration file:
   - **Linux:** `/etc/redis/redis.conf`
   - **Windows:** `C:\Program Files\Memurai\memurai.conf`
2. Open the file and find the `requirepass` directive. Uncomment it and set a strong password:
   ```conf
   requirepass your_super_strong_password
   ```
3. *(Optional but Recommended)* Ensure `bind 127.0.0.1` is set if everything is on the same machine, or bind it to your private internal IP if bridging across servers.
4. Restart the service:
   - **Linux:** `sudo systemctl restart redis-server`
   - **Windows:** Open Services (services.msc) and restart the `Memurai` service.

---

## 3. Configuring the Application

Once your Redis/Memurai server is running and secured, you simply need to tell the Synora Bridge how to access it.

1. Open your `config.ini` file in the root of the Synora Bridge project.
2. Under the `[Server]` section, add the `redis_url` property using the following connection string format:
   - Without password: `redis://localhost:6379/0`
   - With password: `redis://:your_super_strong_password@localhost:6379/0`
   - Remote Server: `redis://:your_super_strong_password@192.168.1.100:6379/0`

```ini
[Server]
environment = production
timezone = Asia/Kolkata
redis_url = redis://:your_super_strong_password@localhost:6379/0
```

---

## 4. Verifying Access & Connectivity

Before running a full cluster, verify that your Synora Bridge can successfully communicate with the Redis broker.

### Method 1: Ping the Server
Use the built-in CLI tools to verify connectivity.

**If you DID NOT set a password (Default):**
- **Linux:** `redis-cli ping`
- **Windows (Command Prompt):** `"C:\Program Files\Memurai\memurai-cli.exe" ping`
- **Windows (PowerShell):** `& "C:\Program Files\Memurai\memurai-cli.exe" ping`

**If you DID set a password:**
- **Linux:** `redis-cli -a your_super_strong_password ping`
- **Windows (Command Prompt):** `"C:\Program Files\Memurai\memurai-cli.exe" -a your_super_strong_password ping`
- **Windows (PowerShell):** `& "C:\Program Files\Memurai\memurai-cli.exe" -a your_super_strong_password ping`

*(A successful connection will return `PONG`)*

### Method 2: Application Boot Logs
When you start the Synora Bridge via `python synora_connect.py`, watch the terminal output carefully. 
- If the connection string is correct, APScheduler will silently bind to the RedisJobStore.
- If the password or port is incorrect, you will immediately see a `redis.exceptions.AuthenticationError` or `redis.exceptions.ConnectionError` in the terminal when booting up.

## 5. Running the Cluster

Once configured, simply start the application on multiple machines:

**Server 1:**
```bash
python synora_connect.py
```

**Server 2:**
```bash
python synora_connect.py
```

Both servers will connect to the same Redis instance. They will share the workload, fetching data from external APIs simultaneously, providing massive horizontal scale.

## Removing Redis
If you want to return to standalone mode (where a single machine handles everything in memory), simply remove the `redis_url` line from your `config.ini` and restart the application. It will gracefully fall back to the standalone SQLite JobStore.
