# 🚀 Daease Assistant - Deployment Guide

## Overview
This guide covers multiple deployment options for your medical voice transcription app, from simple cloud hosting to enterprise-grade solutions.

## 🔒 **Important Security Note**
**NEVER commit your Google Cloud credentials file (`daease-transcription-4f98056e2b9c.json`) to any public repository!**

---

## 1. 🌟 **Streamlit Cloud (Recommended for Testing)**

### Pros:
- ✅ **Free** for public repositories
- ✅ **Easy deployment** - just connect GitHub
- ✅ **Automatic updates** from GitHub pushes
- ✅ **Built-in SSL** and custom domains

### Cons:
- ❌ **Public repositories only** (for free tier)
- ❌ **Limited resources** (1GB RAM, 1 CPU)
- ❌ **Not suitable for production medical data**

### Setup Steps:
1. **Prepare Repository:**
   ```bash
   # Add credentials to .gitignore (if not already)
   echo "daease-transcription-4f98056e2b9c.json" >> .gitignore
   
   # Commit changes
   git add .
   git commit -m "Prepare for deployment"
   git push origin master
   ```

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select repository: `voice-to-text`
   - Main file: `transcriber.py`
   - Add secrets in Streamlit Cloud dashboard

3. **Add Secrets:**
   In Streamlit Cloud dashboard → Secrets:
   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "daease-transcription"
   private_key_id = "your_private_key_id"
   private_key = "-----BEGIN PRIVATE KEY-----\nyour_private_key\n-----END PRIVATE KEY-----\n"
   client_email = "your_service_account_email"
   client_id = "your_client_id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   ```

---

## 2. 🐳 **Docker + Cloud Platforms**

### Create Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application
CMD ["streamlit", "run", "transcriber.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Platform Options:

#### **A. Google Cloud Run** ⭐ (Recommended for Production)
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/daease-transcription/voice-transcriber
gcloud run deploy voice-transcriber \
    --image gcr.io/daease-transcription/voice-transcriber \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2
```

**Pros:**
- ✅ **Serverless** - pay per use
- ✅ **Auto-scaling** 
- ✅ **Integrated with Google Cloud**
- ✅ **HIPAA compliant** options available

**Cost:** ~$0.40 per million requests

#### **B. AWS ECS/Fargate**
```bash
# Push to ECR and deploy
aws ecr create-repository --repository-name voice-transcriber
docker tag voice-transcriber:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/voice-transcriber:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/voice-transcriber:latest
```

**Cost:** ~$30-100/month depending on usage

#### **C. Azure Container Instances**
```bash
az container create \
    --resource-group myResourceGroup \
    --name voice-transcriber \
    --image myregistry.azurecr.io/voice-transcriber:latest \
    --cpu 2 --memory 4 \
    --ports 8501
```

---

## 3. 🖥️ **Virtual Private Server (VPS)**

### Recommended Providers:
- **DigitalOcean Droplets** - $20-40/month
- **Linode** - $20-40/month  
- **AWS EC2** - $30-60/month
- **Google Compute Engine** - $25-50/month

### Setup Script:
```bash
#!/bin/bash
# Ubuntu 20.04 setup script

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx
sudo apt install -y portaudio19-dev python3-pyaudio

# Create app user
sudo useradd -m -s /bin/bash streamlit
sudo su - streamlit

# Setup application
git clone https://github.com/yourusername/voice-to-text.git
cd voice-to-text
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<EOF
[Unit]
Description=Streamlit Medical Transcriber
After=network.target

[Service]
Type=simple
User=streamlit
WorkingDirectory=/home/streamlit/voice-to-text
Environment=PATH=/home/streamlit/voice-to-text/venv/bin
ExecStart=/home/streamlit/voice-to-text/venv/bin/streamlit run transcriber.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit

# Setup Nginx reverse proxy
sudo tee /etc/nginx/sites-available/streamlit > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
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

sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL
sudo certbot --nginx -d your-domain.com
```

---

## 4. 🏢 **Enterprise/Hospital Deployment**

### **On-Premises Options:**

#### **A. Kubernetes Cluster**
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-transcriber
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voice-transcriber
  template:
    metadata:
      labels:
        app: voice-transcriber
    spec:
      containers:
      - name: voice-transcriber
        image: voice-transcriber:latest
        ports:
        - containerPort: 8501
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: voice-transcriber-service
spec:
  selector:
    app: voice-transcriber
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

#### **B. Docker Swarm**
```yaml
# docker-compose.yml
version: '3.8'
services:
  voice-transcriber:
    image: voice-transcriber:latest
    ports:
      - "8501:8501"
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
    volumes:
      - ./credentials.json:/app/credentials.json:ro
    networks:
      - transcriber-network

networks:
  transcriber-network:
    driver: overlay
```

---

## 5. 💰 **Cost Comparison**

| Platform | Monthly Cost | Pros | Best For |
|----------|-------------|------|----------|
| **Streamlit Cloud** | Free | Easy setup | Development/Testing |
| **Google Cloud Run** | $20-100 | Serverless, scalable | Production |
| **AWS ECS** | $30-150 | Enterprise features | Large organizations |
| **DigitalOcean VPS** | $20-40 | Full control | Small-medium clinics |
| **On-Premises** | $500+ | Complete control | Hospitals/Large clinics |

---

## 6. 🔐 **Security Considerations**

### **For Medical Data (HIPAA Compliance):**

1. **Use HTTPS everywhere**
2. **Encrypt data at rest and in transit**
3. **Implement proper access controls**
4. **Regular security audits**
5. **Data residency compliance**

### **Recommended Secure Setup:**
```bash
# Environment variables for production
export GOOGLE_APPLICATION_CREDENTIALS="/secure/path/to/credentials.json"
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
export STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false
```

---

## 7. 🚀 **Quick Start Recommendations**

### **For Development/Testing:**
→ **Streamlit Cloud** (Free, 5 minutes setup)

### **For Small Clinic:**
→ **DigitalOcean VPS** ($20/month, full control)

### **For Production/Hospital:**
→ **Google Cloud Run** (Scalable, HIPAA-ready)

### **For Enterprise:**
→ **On-premises Kubernetes** (Maximum security)

---

## 8. 📞 **Support & Monitoring**

### **Monitoring Tools:**
- **Uptime monitoring**: UptimeRobot, Pingdom
- **Application monitoring**: New Relic, DataDog
- **Log management**: ELK Stack, Splunk

### **Backup Strategy:**
- **Database backups**: Daily automated
- **Configuration backups**: Version controlled
- **Disaster recovery**: Multi-region deployment

---

## Next Steps

1. **Choose your deployment method** based on your needs
2. **Set up proper credentials management**
3. **Configure monitoring and backups**
4. **Test thoroughly before production use**
5. **Implement security best practices**

Need help with any specific deployment? Let me know your requirements! 