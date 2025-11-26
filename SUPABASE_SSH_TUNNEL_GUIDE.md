# 🔐 Supabase SSH Tunnel Setup Guide

**Problem:** Ports 5432 und 8000 sind durch Firewall blockiert  
**Lösung:** SSH Tunnel über Port 22 (SSH ist offen!)

---

## 📊 Port-Scan Ergebnisse

```
✅ Port 22  (SSH)   - OPEN
✅ Port 80  (HTTP)  - OPEN  
✅ Port 443 (HTTPS) - OPEN
❌ Port 5432 (PostgreSQL) - BLOCKED
❌ Port 8000 (Supabase API) - BLOCKED
```

---

## 🔧 Lösung: SSH Tunnel

### **Option 1: SSH Tunnel für PostgreSQL (Port 5432)**

```bash
# Windows (PowerShell)
ssh -L 5432:localhost:5432 user@109.91.247.253

# Dann in anderem Terminal:
psql -h localhost -p 5432 -U postgres -d postgres
# Password: VDt5mjy92lGDWQuE6OpfaHxX9XvFEjEw
```

### **Option 2: SSH Tunnel für Supabase API (Port 8000)**

```bash
# Windows (PowerShell)
ssh -L 8000:localhost:8000 user@109.91.247.253

# Dann in anderem Terminal:
curl http://localhost:8000/rest/v1/
```

### **Option 3: Beide Ports gleichzeitig**

```bash
ssh -L 5432:localhost:5432 -L 8000:localhost:8000 user@109.91.247.253
```

---

## 🔑 SSH Credentials

**Du brauchst:**
1. SSH Username
2. SSH Password oder Private Key
3. Server: `109.91.247.253` oder `supabasekong-s0wkccwgk84w0o8ww8s8wccs.luli-server.de`

**Mögliche Usernames:**
- `root`
- `admin`
- `postgres`
- `supabase`
- Der Username aus deinem Hosting-Provider

---

## 🚀 Automatisches Setup Script

### **Windows PowerShell Script:**

```powershell
# save as: setup_ssh_tunnel.ps1

$SSH_USER = "YOUR_SSH_USERNAME"  # <-- HIER EINTRAGEN
$SSH_HOST = "109.91.247.253"

Write-Host "🔐 Setting up SSH Tunnel to Supabase..."
Write-Host "   PostgreSQL: localhost:5432 → $SSH_HOST:5432"
Write-Host "   Supabase API: localhost:8000 → $SSH_HOST:8000"
Write-Host ""
Write-Host "⚠️  Keep this window open!"
Write-Host ""

ssh -L 5432:localhost:5432 -L 8000:localhost:8000 $SSH_USER@$SSH_HOST
```

### **Python Script (Alternative):**

```python
# save as: scripts/ssh_tunnel.py

import subprocess
import sys

SSH_USER = "YOUR_SSH_USERNAME"  # <-- HIER EINTRAGEN
SSH_HOST = "109.91.247.253"

def create_tunnel():
    print("🔐 Creating SSH Tunnel...")
    print(f"   User: {SSH_USER}")
    print(f"   Host: {SSH_HOST}")
    print(f"   Tunnels: 5432, 8000")
    print()
    print("⚠️  Keep this running!")
    print()
    
    cmd = [
        "ssh",
        "-L", "5432:localhost:5432",
        "-L", "8000:localhost:8000",
        f"{SSH_USER}@{SSH_HOST}"
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    create_tunnel()
```

---

## 🧪 Nach SSH Tunnel Setup

### **1. Test PostgreSQL:**

```bash
python scripts/setup_supabase_connection.py
# Sollte jetzt funktionieren!
```

### **2. Test Supabase API:**

```bash
curl http://localhost:8000/rest/v1/
```

### **3. Migration durchführen:**

```bash
python scripts/migrate_to_supabase.py
```

---

## 🔧 Alternative: Reverse Proxy auf Server einrichten

**Wenn du SSH-Zugriff hast, kannst du auf dem Server einen Reverse Proxy einrichten:**

```bash
# SSH zum Server
ssh user@109.91.247.253

# Nginx Reverse Proxy Config
sudo nano /etc/nginx/sites-available/supabase

# Inhalt:
server {
    listen 80;
    server_name supabasekong-s0wkccwgk84w0o8ww8s8wccs.luli-server.de;
    
    location /rest/ {
        proxy_pass http://localhost:8000/rest/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Aktivieren
sudo ln -s /etc/nginx/sites-available/supabase /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Firewall öffnen
sudo ufw allow 80
sudo ufw allow 443
```

---

## 📝 Was ich brauche von dir:

1. **SSH Username** für `109.91.247.253`
2. **SSH Password** oder **Private Key Path**
3. Oder: **Zugriff zum Server** um Firewall/Reverse Proxy zu konfigurieren

---

## 🎯 Sobald SSH Tunnel läuft:

```python
# database_hybrid.py wird automatisch funktionieren!
# Weil localhost:5432 und localhost:8000 dann erreichbar sind

# Test:
python -c "
from src.core.database_hybrid import get_database_info
print(get_database_info())
"

# Output sollte sein:
# {
#   'type': 'postgresql',
#   'url': 'localhost:5432/postgres',
#   ...
# }
```

---

**Erstellt:** 2025-11-25  
**Status:** Warte auf SSH Credentials  
**Vault Run:** VLT-20251125-004

