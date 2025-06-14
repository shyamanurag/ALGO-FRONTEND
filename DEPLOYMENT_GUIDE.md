# 🚀 ALGO-FRONTEND DigitalOcean Deployment Guide

## 📋 Prerequisites
- DigitalOcean account with Redis and PostgreSQL
- Domain name (optional but recommended)
- SSH access to DigitalOcean droplet

## 🔧 Step 1: Create Droplet
```bash
# Create Ubuntu 22.04 droplet (minimum 2GB RAM for trading app)
# Size: Basic Droplet - $12/month (2GB RAM, 1 vCPU, 50GB SSD)
```

## 🗄️ Step 2: Database Configuration
```bash
# Get your DigitalOcean database connection strings:
# PostgreSQL: postgresql://username:password@host:port/database
# Redis: redis://username:password@host:port
```

## 📦 Step 3: Server Setup
```bash
# SSH into your droplet
ssh root@your_droplet_ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-pip nodejs npm yarn git nginx supervisor sqlite3

# Create app directory
mkdir -p /opt/algo-trading
cd /opt/algo-trading
```

## 📁 Step 4: Deploy Application Code
```bash
# Clone repository
git clone https://github.com/shyamanurag/ALGO-FRONTEND.git .

# Backend setup
cd backend
pip3 install -r requirements.txt

# Frontend setup  
cd ../frontend
yarn install
yarn build
```

## 🔐 Step 5: Environment Configuration
```bash
# Create backend/.env
cat > backend/.env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://your_username:your_password@your_postgres_host:port/trading_db
REDIS_URL=redis://your_username:your_password@your_redis_host:port

# Trading Configuration
PAPER_TRADING=true
AUTONOMOUS_TRADING_ENABLED=true
INTRADAY_TRADING_ENABLED=true
ELITE_RECOMMENDATIONS_ENABLED=true

# TrueData Configuration (Add your credentials)
TRUEDATA_USERNAME=your_truedata_username
TRUEDATA_PASSWORD=your_truedata_password
TRUEDATA_URL=push.truedata.in
TRUEDATA_PORT=8086
DATA_PROVIDER_ENABLED=true

# Zerodha Configuration (Add after deployment)
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_secret
ZERODHA_CLIENT_ID=your_client_id
ZERODHA_ACCOUNT_NAME=your_account_name
EOF

# Create frontend/.env
cat > frontend/.env << 'EOF'
REACT_APP_BACKEND_URL=https://your_domain.com
EOF
```

## 🔧 Step 6: Supervisor Configuration
```bash
# Create supervisor config
cat > /etc/supervisor/conf.d/algo-trading.conf << 'EOF'
[program:backend]
command=python3 /opt/algo-trading/backend/server.py
directory=/opt/algo-trading/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
user=root
environment=PYTHONPATH="/opt/algo-trading/backend"

[program:frontend]
command=yarn start
directory=/opt/algo-trading/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
user=root
EOF
```

## 🌐 Step 7: Nginx Configuration
```bash
# Create nginx config
cat > /etc/nginx/sites-available/algo-trading << 'EOF'
server {
    listen 80;
    server_name your_domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/algo-trading /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

## 🚀 Step 8: Start Services
```bash
# Start supervisor
supervisorctl reread
supervisorctl update
supervisorctl start all

# Check status
supervisorctl status
```

## 🔐 Step 9: SSL Certificate (Recommended)
```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your_domain.com
```

## 🧪 Step 10: Verify Deployment
```bash
# Test backend
curl http://localhost:8001/api/health

# Test frontend
curl http://localhost:3000

# Check logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/frontend.out.log
```

## 🔄 Step 11: Zerodha Authentication Setup
After deployment, add Zerodha credentials:

1. Edit `/opt/algo-trading/backend/.env`
2. Add your Zerodha API credentials
3. Restart backend: `supervisorctl restart backend`

## 📊 Step 12: Monitoring Setup
```bash
# Create monitoring script
cat > /opt/algo-trading/monitor.sh << 'EOF'
#!/bin/bash
# Check if services are running
supervisorctl status | grep -E "(backend|frontend)" | grep -v RUNNING && {
    echo "Service down, restarting..."
    supervisorctl restart all
}
EOF

chmod +x /opt/algo-trading/monitor.sh

# Add to crontab (check every 5 minutes)
echo "*/5 * * * * /opt/algo-trading/monitor.sh" | crontab -
```

## 🛡️ Security Checklist
- [ ] Change default SSH port
- [ ] Setup firewall (ufw)
- [ ] Enable automatic security updates
- [ ] Regular database backups
- [ ] Monitor API usage
- [ ] Log rotation setup

## 🆘 Troubleshooting
```bash
# View logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/nginx/error.log

# Restart services
supervisorctl restart all
systemctl restart nginx

# Check port usage
netstat -tlnp | grep -E "(3000|8001)"
```