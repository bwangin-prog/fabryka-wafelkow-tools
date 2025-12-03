# XML to CSV Converter - Quick Deployment Guide

## 🚀 Fastest: Streamlit Community Cloud (FREE)

1. **Push to GitHub**:
   ```bash
   cd '/home/bartosz/Fabryka Wafelkow'
   git init
   git add xml_converter_app.py requirements.txt .streamlit/
   git commit -m "XML to CSV converter app"
   git remote add origin https://github.com/YOUR_USERNAME/xml-converter.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your GitHub repo
   - Set main file: `xml_converter_app.py`
   - Click "Deploy"
   - Done! Your app will be live at `https://your-app.streamlit.app`

## 🐳 Docker Deployment

```bash
# Build
docker build -t xml-converter .

# Run locally
docker run -p 8501:8501 xml-converter

# Access at http://localhost:8501
```

## 🌐 Deploy to Cloud Providers

### Heroku
```bash
# Create Procfile
echo "web: streamlit run xml_converter_app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
heroku login
heroku create your-app-name
git push heroku main
```

### Google Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/xml-converter
gcloud run deploy xml-converter --image gcr.io/PROJECT_ID/xml-converter --platform managed --port 8501
```

### AWS EC2 / DigitalOcean
```bash
# SSH to server
ssh user@your-server

# Clone repo
git clone https://github.com/YOUR_USERNAME/xml-converter.git
cd xml-converter

# Install
pip install -r requirements.txt

# Run with nohup
nohup streamlit run xml_converter_app.py --server.port=8501 --server.address=0.0.0.0 &
```

## 🏠 Local Development

```bash
# Run locally
streamlit run xml_converter_app.py

# App opens at http://localhost:8501
```

## 📝 Files Needed for Deployment

Essential files:
- ✅ `xml_converter_app.py` - Main application
- ✅ `requirements.txt` - Python dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `Dockerfile` - For Docker deployment (optional)

## 🔧 Environment Variables (if needed)

If you want to add secrets (e.g., API tokens), create `.streamlit/secrets.toml`:

```toml
# .streamlit/secrets.toml
BASELINKER_TOKEN = "your-token-here"
```

Then access in code:
```python
import streamlit as st
token = st.secrets["BASELINKER_TOKEN"]
```

## 🎯 Recommended: Streamlit Community Cloud

**Why?**
- ✅ FREE hosting
- ✅ Auto-deployment on git push
- ✅ HTTPS included
- ✅ No server management
- ✅ Built-in secrets management
- ✅ Perfect for internal tools

**Limitations:**
- 1 GB RAM (sufficient for XML parsing)
- Public by default (can set password in settings)
- Sleeps after inactivity (wakes on first request)

## 🔐 Securing Your App (IMPORTANT!)

### ✅ Password Protection (Built-in)

The app now includes password protection. To enable:

**1. Streamlit Cloud:**
- Go to your app dashboard
- Click "⚙️ Settings" → "Secrets"
- Add this secret:
```toml
password = "your_secure_password_here"
```
- Save and the app will restart

**2. Local/Docker:**
- Create/edit `.streamlit/secrets.toml`:
```toml
password = "your_secure_password_here"
```
- Restart the app

**Note:** If no password is configured, the app allows access (for development).

### Additional Security Options

**Email Whitelist (Streamlit Cloud):**
- Go to app Settings → "Sharing"
- Enable "Restrict viewing to invited users only"
- Add email addresses (requires Google sign-in)

**IP Whitelist (Self-hosted):**
- Use nginx/Apache to restrict by IP:
```nginx
location / {
    allow 203.0.113.0/24;  # Your IP range
    deny all;
    proxy_pass http://localhost:8501;
}
```

## 📊 Performance Tips

- XML feeds are fetched on-demand (no caching by default)
- For large feeds, consider adding `@st.cache_data` decorator
- Timeout is set to 30s - increase if needed for large feeds

## 🆘 Troubleshooting

**App won't start**: Check Python syntax with `python3 -m py_compile xml_converter_app.py`

**Module errors**: Ensure `requirements.txt` includes all dependencies

**Timeout on large feeds**: Increase timeout in `urllib.request.urlopen(url, timeout=60)`

**Memory issues**: Reduce preview size or add pagination

## 📚 Next Steps

1. Deploy to Streamlit Cloud (5 minutes)
2. Share link with team: `https://your-app.streamlit.app`
3. Monitor usage via Streamlit Cloud dashboard
4. Add more suppliers as needed

---

**Current Status**: ✅ Ready for deployment
