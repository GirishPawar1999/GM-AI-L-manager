<div align="center">

# 📧 GM-AI-L Manager

### AI-Powered Email Management Desktop Application

[![Electron](https://img.shields.io/badge/Electron-27.0.0-47848F?style=for-the-badge&logo=electron&logoColor=white)](https://www.electronjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18.x-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

*Intelligent email management powered by AI - Built with Electron, Node.js, and Python*

[Features](#-features) • [Installation](#-installation) • [Usage](#-running-the-application) • [Documentation](#-application-pages) • [Contributing](#-contributing)

</div>

---
## 🎬 Demo Video (Local File)

<video src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/Demo.mp4" width="600" controls></video>
---

## 🌟 Overview

Gmail AI Manager is a cross-platform desktop application that revolutionizes email management using cutting-edge AI technology. It provides intelligent email summarization, automatic categorization, tone analysis, and smart reply suggestions - all running locally on your device with no cloud connectivity required.

<div align="center">

### 🎯 Built With Modern Technologies

| Backend | Frontend | Database | AI/ML |
|---------|----------|----------|-------|
| Node.js | EJS, JavaScript, CSS | JSON | HuggingFace Transformers |

</div>

---

## 🖼️ UI Preview

<div align="center">

### 🏠 Home / Setup Page
<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/Home.png" width="700" alt="Home Page"/>

---

### 📊 Dashboard Page
<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/Dashboard-1.png" width="700" alt="Dashboard"/>

---

### 💬 Bulk Summary and Individual Summarization View
<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/Bulk-summary.png" width="700" alt="Bulk Summary"/>

<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/AI-Individual-email-summary.png" width="700" alt="Indivisual Summary"/>

---

### 💬Smart Reply View
<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/Smart-Reply.png" width="700" alt="Smart Reply"/>

---

### 💬AI Settings and AI Label View
<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/AI-Settings.png" width="700" alt="AI_settings"/>

<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/AI-Label.png" width="700" alt="AI Label"/>

---

### 💬Compose Mail View
<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/Compose-Mail.png" width="700" alt="Smart Reply"/>

---

### 👨‍💻 Developer Page
<img src="https://github.com/GirishPawar1999/GM-AI-L-manager/blob/main/Screenshorts/Dev.png" width="700" alt="Developer Page"/>

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🤖 AI-Powered Intelligence

- **📝 Email Summarization**: Instant AI-generated summaries (Bulk & List view)
- **🎯 Smart Categorization**: Automatic email categorization based on content
- **😊 Tone Analysis**: Detect email sentiment and tone
- **💬 Smart Replies**: AI-generated contextual reply suggestions
- **🔒 On-Device Processing**: All AI runs locally - no cloud connectivity

</td>
<td width="50%">

### 🚀 Core Features

- **⚡ Easy Setup**: Simple configuration wizard
- **📬 Load 50+ Emails**: Handle multiple emails efficiently
- **🔍 Email Search**: Fast search functionality
- **📄 Pagination**: 10 emails per page view
- **🎨 Modern UI**: Beautiful, intuitive interface
- **🔔 New Email Popup**: Real-time notifications

</td>
</tr>
</table>

### 🖥️ Cross-Platform Support

Works seamlessly on Windows, macOS, and Linux

---

## 🎓 AI Models Used

<div align="center">

| Purpose | Model | Provider |
|---------|-------|----------|
| **Email Summarization & Tone** | `sshleifer/distilbart-cnn-12-6` | HuggingFace |
| **Smart Reply Generation** | `google/flan-t5-base` | Google/HuggingFace |
| **Training Dataset** | `sidhq/email-thread-summary` | Custom |

</div>

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

```bash
✅ Node.js (v18.x or higher)
✅ Python (v3.8 or higher)  
✅ npm or yarn
✅ Gmail API Credentials (see setup below)
```

---

## 🔧 Installation

### **Step 1: Clone the Repository**

```bash
git clone https://github.com/girishpawar1999/gmail-ai-manager.git
cd gmail-ai-manager
```

### **Step 2: Install Dependencies**

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### **Step 3: Quick Setup (Recommended)**

**For Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**For Windows:**
```bash
setup.bat
```

---

## 🔐 Gmail API Setup

### **Step 1: Enable Gmail API**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **"APIs & Services"** → **"Library"**
4. Search for **"Gmail API"** and enable it

### **Step 2: Create OAuth 2.0 Credentials**

1. In Google Cloud Console, go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Choose **"Web application"**
4. Add authorized redirect URI: `http://localhost`
5. Download the credentials JSON file
6. Save it as `credentials.json` in the project root

<details>
<summary>📸 Click to see visual guide</summary>

> 1. Navigate to Credentials page
> 2. Click "Create Credentials"
> 3. Select "OAuth client ID"
> 4. Configure consent screen if prompted
> 5. Download JSON file

</details>

---

## 📁 Project Structure

```
gmail-ai-manager/
├── 📄 main.js                  # Electron main process
├── 📄 preload.js              # Electron preload script  
├── 📄 index.js                # Express server
├── 📄 package.json            # Project configuration
├── 📄 credentials.json        # Gmail API credentials (you provide)
├── 📄 Summary_and_tone.py     # Python AI processing script
├── 📄 dataset.py              # Dataset analysis tool
├── 📂 views/
│   ├── Home.ejs              # Setup/Configuration page
│   ├── Home.css              # Home page styles
│   ├── Dev.ejs               # Developer information page
│   ├── Dev.css               # Developer page styles
│   └── dashboard.ejs         # Main dashboard interface
├── 📂 assets/
│   └── icon.png              # Application icon
├── 📂 node_modules/          # Node dependencies
└── 📂 __pycache__/           # Python cache
```

---

## 🎮 Running the Application

### **Development Mode**

```bash
# Start as Electron app (Recommended)
npm start

# Run in development mode with DevTools
npm run dev

# Run server only (browser-based)
npm run server
```

### **First Run Setup**

1. 🚀 Launch the application
2. 🏠 You'll be redirected to the **Home page**
3. 📋 Follow the setup instructions:
   - Enter your Gmail API credentials
   - Or upload your `credentials.json` file
   - Configure AI settings (all enabled by default)
4. ✅ Click **"Go to Dashboard"** after setup
5. 🔐 Authorize the app when prompted in your browser
6. 📋 Copy the authorization code and paste it in the terminal
7. 🎉 Start managing emails!

---

## 📦 Building for Production

### **Build for Current Platform**

```bash
npm run build
```

### **Build for Specific Platforms**

```bash
# Windows Installer
npm run build:win

# macOS DMG
npm run build:mac

# Linux AppImage/DEB
npm run build:linux
```

> 📦 Built applications will be available in the `dist/` folder

---

## 🎨 Application Pages

### **1. 🏠 Home Page** (`/home`)

<details>
<summary>View Details</summary>

- Setup and configuration wizard
- Gmail API credentials input (paste or upload)
- Initial AI settings configuration
- Step-by-step setup instructions
- Feature showcase and demo
- Beautiful loading animation on fresh run

</details>

### **2. 📊 Dashboard Page** (`/`)

<details>
<summary>View Details</summary>

- Main email management interface
- Email list with AI-generated summaries
- Smart category filters
- Email composition interface
- Quick reply functionality
- Search and pagination
- New email notifications

</details>

### **3. 👨‍💻 Developer Page** (`/dev`)

<details>
<summary>View Details</summary>

- Developer information (Girish Pawar)
- Project documentation
- Technical stack details
- Skills showcase
- Contact information
- Portfolio links

</details>

---

## ⚙️ Configuration Files

### **`credentials.json`** - Gmail API OAuth 2.0 Credentials

```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "project_id": "YOUR_PROJECT_ID",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost"]
  }
}
```

### **`AI_settings.json`** - AI Feature Toggles (Auto-created)

```json
{
  "emailSummarization": true,
  "aiAutoCategorization": true,
  "smartReplyGeneration": true
}
```

### **`template.json`** - Email Categorization Rules (Auto-created)

```json
{
  "rules": [
    {
      "category": "Work",
      "keywords": ["meeting", "project", "deadline"]
    },
    {
      "category": "Bills",
      "keywords": ["invoice", "payment", "bill"]
    }
  ]
}
```

---

## 🔐 Security Notes

> ⚠️ **Important Security Guidelines**

- ❌ **Never** commit `credentials.json` or `token.json` to version control
- ✅ Always add sensitive files to `.gitignore`:
  ```
  credentials.json
  token.json
  database.json
  ```
- 🔒 Keep your client secret secure
- 🔄 Regularly rotate OAuth tokens
- 🛡️ All AI processing happens on-device (no cloud connectivity)

---

## 🐛 Troubleshooting

<details>
<summary><b>Issue: "Missing credentials.json"</b></summary>

**Solution:** Follow the Gmail API setup steps above and ensure `credentials.json` is in the project root directory.

</details>

<details>
<summary><b>Issue: "Invalid grant" or "Access denied"</b></summary>

**Solution:**
1. Delete `token.json` from project root
2. Restart the application
3. Re-authorize when prompted

</details>

<details>
<summary><b>Issue: Python script not running</b></summary>

**Solution:**
1. Check Python installation: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure `Summary_and_tone.py` exists in project root

</details>

<details>
<summary><b>Issue: Port 3000 already in use</b></summary>

**Solution:**
1. Kill the process using port 3000
2. Or change the port in `index.js`:
   ```javascript
   const PORT = 3001; // Change to any available port
   ```

</details>

---

## 🛠️ Development

### **Adding New Routes**

Edit `index.js` and add new routes:

```javascript
app.get("/new-route", (req, res) => {
  res.render("new-page");
});
```

### **Modifying UI**

- Edit EJS templates in `views/` folder
- Edit CSS files for styling
- Restart the app to see changes

### **Python AI Processing**

The `Summary_and_tone.py` script runs in the background to:
- Summarize email content using `distilbart-cnn-12-6`
- Analyze email tone and sentiment
- Generate smart reply suggestions using `flan-t5-base`

Modify this file to customize AI behavior.

### **Dataset Analysis**

Use `dataset.py` to view and analyze the training dataset:

```bash
python dataset.py
```

---

## 📝 API Endpoints

### **Configuration Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/save-credentials` | Save Gmail API credentials |
| `POST` | `/api/save-ai-settings` | Save AI feature settings |
| `GET` | `/api/check-credentials` | Check if app is configured |

### **Email Management Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/send-email` | Send an email |
| `POST` | `/api/save-reply` | Save a reply draft |
| `POST` | `/api/add-template` | Add categorization rule |
| `POST` | `/api/delete-template` | Delete categorization rule |

---

## 🎯 Current Features

<div align="center">

| # | Feature | Status |
|---|---------|--------|
| 1 | Easy Setup Wizard | ✅ Available |
| 2 | AI Email Summary (Bulk & List) | ✅ Available |
| 3 | AI Email Categorization | ✅ Available |
| 4 | AI Smart Reply Generation | ✅ Available |
| 5 | AI Settings Configuration | ✅ Available |
| 6 | Load up to 50 Emails | ✅ Available |
| 7 | On-Device AI Processing | ✅ Available |
| 8 | New Email Popup Notifications | ✅ Available |
| 9 | Compose Mail UI | ✅ Available |
| 10 | Email Search Functionality | ✅ Available |
| 11 | Pagination (10 emails/page) | ✅ Available |
| 12 | Developer Information Page | ✅ Available |

</div>

---

## 🚧 Upcoming Features

<div align="center">

| # | Feature | Status |
|---|---------|--------|
| 1 | POP Email Service Support | 🔄 In Progress |
| 2 | Fine-Tuned Models | 🔄 In Progress |
| 3 | Send Email Functionality | 📋 Planned |
| 4 | Forward Email Feature | 📋 Planned |
| 5 | Reply Email Functionality | 📋 Planned |
| 6 | Mark as Unread | 📋 Planned |
| 7 | Trash & SPAM Filtering | 📋 Planned |
| 8 | Email Threading | 📋 Planned |

</div>

---

## 🤝 Contributing

Please do ask for permitions before utilization or modification of code. This code solely belongs to Girish Pawar

### **Development Guidelines**

- Follow existing code style and conventions
- Write meaningful commit messages
- Test your changes thoroughly
- Update documentation as needed

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---


## 🙏 Acknowledgments

<div align="center">

Special thanks to these amazing projects and communities:

- 📧 **Gmail API** by Google
- ⚡ **Electron Framework** for cross-platform desktop apps
- 🟢 **Node.js Community** for server-side JavaScript
- 🐍 **Python Community** for AI/ML capabilities
- 🤗 **HuggingFace** for transformer models
- 📚 **Open Source Community** for continuous inspiration

</div>

---

## 📊 Tech Stack

<div align="center">

### **Backend**
![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=node.js&logoColor=white)
![Express.js](https://img.shields.io/badge/Express.js-000000?style=for-the-badge&logo=express&logoColor=white)

### **Frontend**
![EJS](https://img.shields.io/badge/EJS-B4CA65?style=for-the-badge&logo=ejs&logoColor=black)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

### **Database**
![JSON](https://img.shields.io/badge/JSON-000000?style=for-the-badge&logo=json&logoColor=white)

### **AI/ML**
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Transformers](https://img.shields.io/badge/Transformers-FF6F00?style=for-the-badge&logo=pytorch&logoColor=white)

### **Desktop Framework**
![Electron](https://img.shields.io/badge/Electron-47848F?style=for-the-badge&logo=electron&logoColor=white)

</div>

---

<div align="center">

### ⭐ Star this repository if you find it helpful!

**Made with ❤️ by [Girish Pawar](https://girishpawar1999.github.io/girish.pawar/aboutme.html)**

*For more information, visit the [Developer Page](/dev) in the application*

---

**Version 1.0.0** | Last Updated: October 2025

</div>
