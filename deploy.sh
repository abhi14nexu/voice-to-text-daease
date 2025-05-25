#!/bin/bash

# Daease Assistant Deployment Script
# Usage: ./deploy.sh [development|production]

set -e

ENVIRONMENT=${1:-development}
APP_NAME="voice-transcriber"
APP_USER="streamlit"
APP_DIR="/home/$APP_USER/$APP_NAME"

echo "🚀 Deploying Daease Assistant in $ENVIRONMENT mode..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    portaudio19-dev \
    python3-pyaudio \
    curl \
    ufw

# Create application user
echo "👤 Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash $APP_USER
    sudo usermod -aG sudo $APP_USER
fi

# Setup application directory
echo "📁 Setting up application directory..."
sudo -u $APP_USER mkdir -p $APP_DIR
cd $APP_DIR

# Clone or update repository
if [ -d ".git" ]; then
    echo "🔄 Updating existing repository..."
    sudo -u $APP_USER git pull
else
    echo "📥 Cloning repository..."
    # Replace with your actual repository URL
    sudo -u $APP_USER git clone https://github.com/yourusername/voice-to-text.git .
fi

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Create necessary directories
sudo -u $APP_USER mkdir -p transcriptions medical_reports

# Setup systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null <<EOF
[Unit]
Description=Daease Assistant
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=GOOGLE_APPLICATION_CREDENTIALS=$APP_DIR/daease-transcription-4f98056e2b9c.json
ExecStart=$APP_DIR/venv/bin/streamlit run transcriber.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx configuration
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl restart nginx

# Check if credentials file exists
if [ ! -f "$APP_DIR/daease-transcription-4f98056e2b9c.json" ]; then
    echo "⚠️  WARNING: Google Cloud credentials file not found!"
    echo "   Please upload your credentials file to: $APP_DIR/daease-transcription-4f98056e2b9c.json"
    echo "   Then run: sudo systemctl start $APP_NAME"
else
    sudo systemctl start $APP_NAME
fi

# Production-specific setup
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔒 Setting up production environment..."
    
    # Prompt for domain name
    read -p "Enter your domain name (e.g., transcriber.yourdomain.com): " DOMAIN_NAME
    
    if [ ! -z "$DOMAIN_NAME" ]; then
        # Update Nginx config with domain
        sudo sed -i "s/server_name _;/server_name $DOMAIN_NAME;/" /etc/nginx/sites-available/$APP_NAME
        sudo systemctl reload nginx
        
        # Setup SSL with Let's Encrypt
        echo "🔐 Setting up SSL certificate..."
        sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
    fi
    
    # Setup log rotation
    sudo tee /etc/logrotate.d/$APP_NAME > /dev/null <<EOF
/var/log/$APP_NAME/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
}
EOF
fi

# Display status
echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Service Status:"
sudo systemctl status $APP_NAME --no-pager -l
echo ""
echo "🌐 Nginx Status:"
sudo systemctl status nginx --no-pager -l
echo ""
echo "🔗 Access your application at:"
if [ "$ENVIRONMENT" = "production" ] && [ ! -z "$DOMAIN_NAME" ]; then
    echo "   https://$DOMAIN_NAME"
else
    echo "   http://$(curl -s ifconfig.me)"
fi
echo ""
echo "📝 Useful commands:"
echo "   View logs: sudo journalctl -u $APP_NAME -f"
echo "   Restart app: sudo systemctl restart $APP_NAME"
echo "   Check status: sudo systemctl status $APP_NAME"
echo ""

if [ ! -f "$APP_DIR/daease-transcription-4f98056e2b9c.json" ]; then
    echo "⚠️  Don't forget to upload your Google Cloud credentials!"
fi 