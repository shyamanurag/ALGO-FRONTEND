#!/bin/bash
# 🚀 ALGO-FRONTEND Automated Deployment Script for DigitalOcean

set -e  # Exit on any error

echo "🚀 Starting ALGO-FRONTEND deployment..."

# Configuration (Update these with your details)
DOMAIN_NAME="your-domain.com"
POSTGRES_URL="postgresql://username:password@host:port/database"
REDIS_URL="redis://username:password@host:port"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing dependencies..."
apt install -y python3 python3-pip nodejs npm yarn git nginx supervisor sqlite3 curl

print_status "Creating application directory..."
mkdir -p /opt/algo-trading
cd /opt/algo-trading

print_status "Cloning repository..."
if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/shyamanurag/ALGO-FRONTEND.git .
fi

print_status "Setting up backend..."
cd backend
pip3 install -r requirements.txt

print_status "Setting up frontend..."
cd ../frontend
yarn install

print_status "Creating environment files..."
cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=${POSTGRES_URL}
REDIS_URL=${REDIS_URL}
DB_NAME=trading_db

# Trading Configuration
PAPER_TRADING=true
AUTONOMOUS_TRADING_ENABLED=true
INTRADAY_TRADING_ENABLED=true
ELITE_RECOMMENDATIONS_ENABLED=true

# Auto Trading Controls
AUTO_SQUARE_OFF_ENABLED=true
AUTO_TARGET_BOOKING=true
AUTO_STOP_LOSS=true
DAILY_STOP_LOSS_PERCENT=2.0

# TrueData Configuration (Update with your credentials)
TRUEDATA_USERNAME=""
TRUEDATA_PASSWORD=""
TRUEDATA_URL=push.truedata.in
TRUEDATA_PORT=8086
DATA_PROVIDER_ENABLED=false

# Zerodha Configuration (Update after deployment)
ZERODHA_API_KEY=""
ZERODHA_API_SECRET=""
ZERODHA_CLIENT_ID=""
ZERODHA_ACCOUNT_NAME=""
EOF

cat > frontend/.env << EOF
REACT_APP_BACKEND_URL=https://${DOMAIN_NAME}
EOF

print_status "Building frontend..."
cd frontend
yarn build

print_status "Setting up Supervisor configuration..."
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
command=npx serve -s build -l 3000
directory=/opt/algo-trading/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
user=root
EOF

print_status "Setting up Nginx configuration..."
cat > /etc/nginx/sites-available/algo-trading << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    # Frontend (React build)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/algo-trading /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

print_status "Testing Nginx configuration..."
nginx -t

print_status "Starting services..."
systemctl restart nginx
supervisorctl reread
supervisorctl update
supervisorctl start all

print_status "Creating monitoring script..."
cat > /opt/algo-trading/monitor.sh << 'EOF'
#!/bin/bash
# Monitor trading application services

# Check backend
if ! curl -f http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "$(date): Backend down, restarting..." >> /var/log/algo-trading-monitor.log
    supervisorctl restart backend
fi

# Check frontend
if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "$(date): Frontend down, restarting..." >> /var/log/algo-trading-monitor.log
    supervisorctl restart frontend
fi

# Check supervisor status
supervisorctl status | grep -E "(backend|frontend)" | grep -v RUNNING && {
    echo "$(date): Services not running, restarting all..." >> /var/log/algo-trading-monitor.log
    supervisorctl restart all
}
EOF

chmod +x /opt/algo-trading/monitor.sh

# Add monitoring to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/algo-trading/monitor.sh") | crontab -

print_status "Setting up log rotation..."
cat > /etc/logrotate.d/algo-trading << 'EOF'
/var/log/supervisor/backend.*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    postrotate
        supervisorctl restart backend
    endscript
}

/var/log/supervisor/frontend.*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    postrotate
        supervisorctl restart frontend
    endscript
}
EOF

print_status "Deployment completed! 🎉"
echo
echo "📊 Service Status:"
supervisorctl status

echo
echo "🌐 Access your application:"
echo "   Frontend: http://${DOMAIN_NAME}"
echo "   Backend API: http://${DOMAIN_NAME}/api/health"

echo
echo "📝 Next Steps:"
echo "1. Update DNS records to point ${DOMAIN_NAME} to this server"
echo "2. Add SSL certificate: certbot --nginx -d ${DOMAIN_NAME}"
echo "3. Update TrueData credentials in /opt/algo-trading/backend/.env"
echo "4. Update Zerodha credentials in /opt/algo-trading/backend/.env"
echo "5. Restart backend: supervisorctl restart backend"

echo
echo "📋 Log Files:"
echo "   Backend: tail -f /var/log/supervisor/backend.out.log"
echo "   Frontend: tail -f /var/log/supervisor/frontend.out.log"
echo "   Monitor: tail -f /var/log/algo-trading-monitor.log"

print_warning "⚠️  Remember to:"
print_warning "   - Change default SSH settings"
print_warning "   - Setup firewall (ufw enable)"
print_warning "   - Add your trading API credentials"
print_warning "   - Test all functionality before live trading"