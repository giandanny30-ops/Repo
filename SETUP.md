# GIANNI Bot Panel — Deployment na www.gian.com

## Zahtjevi
- Ubuntu 22.04+ / Debian 12+
- Node.js 20+ (`curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt install nodejs`)
- nginx (`apt install nginx`)
- SSL certifikat (preporučujemo Let's Encrypt)

## Koraci instalacije

### 1. Upload fajlova na server
```bash
scp -r gianni-deploy/ root@YOUR_SERVER:/var/www/gianni/
```

### 2. Postavi strukturu
```bash
mkdir -p /var/www/gianni/data
cp -r /var/www/gianni/gianni-deploy/api-server /var/www/gianni/
cp -r /var/www/gianni/gianni-deploy/bot-panel   /var/www/gianni/
```

### 3. Instaliraj Node.js dependencije za API
```bash
cd /var/www/gianni/api-server
npm install --omit=dev
```

### 4. Postavi .env fajl
```bash
cp /var/www/gianni/gianni-deploy/.env.example /var/www/gianni/.env
nano /var/www/gianni/.env
# Popuni DISCORD_TOKEN i SESSION_SECRET
```

### 5. Kopiraj nginx config
```bash
cp /var/www/gianni/gianni-deploy/nginx/gian.com.conf /etc/nginx/sites-available/gian.com
ln -s /etc/nginx/sites-available/gian.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 6. SSL certifikat (Let's Encrypt)
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d gian.com -d www.gian.com
```

### 7. Postavi systemd servis za API
```bash
cp /var/www/gianni/gianni-deploy/gianni-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable gianni-api
systemctl start gianni-api
systemctl status gianni-api
```

### 8. Provjeri da radi
```bash
curl http://localhost:5000/api/healthz
# Trebalo bi vratiti: {"ok":true}
```

## Upravljanje

```bash
# Restart API servera
systemctl restart gianni-api

# Logovi
journalctl -u gianni-api -f

# Provjera nginx
nginx -t && systemctl reload nginx
```

## Discord Token

Nakon deploymenta, otvori `https://www.gian.com/settings` i unesi
Discord Bot Token direktno u panelu — snimi bez restarta servera.

## Hostovanje

Preporučeni VPS provideri:
- Hetzner Cloud (CX11 — 3.49€/mj) — https://hetzner.com
- DigitalOcean (Basic — $4/mj) — https://digitalocean.com  
- Contabo (S — 4.99€/mj) — https://contabo.com
