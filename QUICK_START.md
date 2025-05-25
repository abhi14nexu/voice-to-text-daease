# 🚀 Quick Start - Deploy Your Daease Assistant

## 🎯 **Choose Your Deployment Method**

### 1. 🌟 **Streamlit Cloud (5 minutes, FREE)**
**Perfect for testing and demos**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin master
   ```

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Set main file: `transcriber.py`
   - Click "Deploy"

3. **Add Secrets:**
   - In your app dashboard, click "⚙️ Settings" → "Secrets"
   - Paste your Google Cloud credentials as JSON

**✅ Your app will be live at: `https://yourapp.streamlit.app`**

---

### 2. 🐳 **Docker (Local/Cloud)**
**For development and production**

**Quick Local Setup:**
```bash
# Build and run
docker build -t voice-transcriber .
docker run -p 8501:8501 -v $(pwd)/daease-transcription-4f98056e2b9c.json:/app/daease-transcription-4f98056e2b9c.json voice-transcriber
```

**Or use Docker Compose:**
```bash
docker-compose up -d
```

**✅ Access at: `http://localhost:8501`**

---

### 3. ☁️ **Google Cloud Run (Production)**
**Scalable, pay-per-use**

```bash
# Install Google Cloud CLI first
gcloud auth login
gcloud config set project daease-transcription

# Build and deploy
gcloud builds submit --tag gcr.io/daease-transcription/voice-transcriber
gcloud run deploy voice-transcriber \
    --image gcr.io/daease-transcription/voice-transcriber \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi
```

**✅ Google will provide a URL like: `https://voice-transcriber-xxx.run.app`**

---

### 4. 🖥️ **VPS Deployment (DigitalOcean/AWS/etc.)**
**Full control, $20-40/month**

1. **Create a VPS** (Ubuntu 20.04+)
2. **Upload files:**
   ```bash
   scp -r . user@your-server-ip:/home/user/voice-to-text/
   ```
3. **Run deployment script:**
   ```bash
   ssh user@your-server-ip
   cd voice-to-text
   chmod +x deploy.sh
   ./deploy.sh production
   ```

**✅ Access at: `http://your-server-ip`**

---

## 🔐 **Security Setup (Important!)**

### For Production Deployment:

1. **Never commit credentials:**
   ```bash
   # Add to .gitignore
   echo "daease-transcription-4f98056e2b9c.json" >> .gitignore
   ```

2. **Use environment variables:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
   ```

3. **Enable HTTPS:**
   - Streamlit Cloud: Automatic
   - VPS: Use Let's Encrypt (included in deploy script)
   - Cloud Run: Automatic

---

## 💰 **Cost Comparison**

| Method | Cost | Setup Time | Best For |
|--------|------|------------|----------|
| **Streamlit Cloud** | FREE | 5 min | Testing/Demo |
| **Google Cloud Run** | $10-50/month | 15 min | Production |
| **VPS (DigitalOcean)** | $20-40/month | 30 min | Full Control |
| **Docker Local** | FREE | 5 min | Development |

---

## 🚀 **Recommended Path**

### **For Testing:**
1. Start with **Streamlit Cloud** (free, instant)
2. Test all features thoroughly

### **For Production:**
1. Use **Google Cloud Run** (scalable, secure)
2. Or **VPS** if you need full control

### **For Development:**
1. Use **Docker** locally
2. Easy to replicate environment

---

## 🆘 **Need Help?**

### **Common Issues:**

1. **Audio not working:**
   - Check microphone permissions
   - Ensure HTTPS (required for audio)

2. **Credentials error:**
   - Verify JSON format
   - Check file path

3. **Deployment fails:**
   - Check requirements.txt
   - Verify Python version (3.9+)

### **Quick Commands:**

```bash
# Check if app is running
curl http://localhost:8501/_stcore/health

# View logs (VPS)
sudo journalctl -u voice-transcriber -f

# Restart service (VPS)
sudo systemctl restart voice-transcriber

# Test Docker build
docker build -t test-transcriber .
```

---

## 🎯 **Next Steps**

1. **Choose your deployment method** from above
2. **Follow the specific instructions**
3. **Test thoroughly** with sample recordings
4. **Set up monitoring** for production use
5. **Configure backups** for important data

**Ready to deploy? Pick your method and follow the steps above!** 🚀 