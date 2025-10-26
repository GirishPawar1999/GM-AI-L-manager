#!/bin/bash

# Gmail AI Manager - Setup Script
# This script automates the initial setup process

echo "=========================================="
echo "  Gmail AI Manager - Setup Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Node.js is installed
echo "🔍 Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✅ Node.js is installed: $(node --version)${NC}"

# Check if npm is installed
echo "🔍 Checking npm installation..."
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm is installed: $(npm --version)${NC}"

# Check if Python is installed
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python is not installed${NC}"
    echo "AI features require Python. Install from https://python.org/"
    read -p "Continue without Python? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi
    echo -e "${GREEN}✅ Python is installed: $($PYTHON_CMD --version)${NC}"
fi

# Install Node.js dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
npm install
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install Node.js dependencies${NC}"
    exit 1
fi

# Install Python dependencies (if Python is available)
if [ ! -z "$PYTHON_CMD" ]; then
    echo ""
    echo "📦 Installing Python dependencies..."
    
    # Check if pip is installed
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        echo -e "${YELLOW}⚠️  pip is not installed. Skipping Python dependencies.${NC}"
        PIP_CMD=""
    fi
    
    if [ ! -z "$PIP_CMD" ]; then
        $PIP_CMD install -r requirements.txt
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Python dependencies installed${NC}"
        else
            echo -e "${YELLOW}⚠️  Some Python dependencies failed to install${NC}"
        fi
    fi
fi

# Create necessary directories
echo ""
echo "📁 Creating necessary directories..."
mkdir -p assets
echo -e "${GREEN}✅ Directories created${NC}"

# Check for credentials.json
echo ""
echo "🔐 Checking for Gmail API credentials..."
if [ -f "credentials.json" ]; then
    echo -e "${GREEN}✅ credentials.json found${NC}"
else
    echo -e "${YELLOW}⚠️  credentials.json not found${NC}"
    echo ""
    echo "You need to set up Gmail API credentials:"
    echo "1. Visit: https://console.cloud.google.com/"
    echo "2. Create a project and enable Gmail API"
    echo "3. Create OAuth 2.0 credentials"
    echo "4. Download and save as credentials.json"
    echo ""
    echo "You can also set this up from the Home page after starting the app."
fi

# Create default configuration files if they don't exist
echo ""
echo "⚙️  Creating default configuration files..."

if [ ! -f "AI_settings.json" ]; then
    cat > AI_settings.json << EOF
{
  "emailSummarization": true,
  "aiAutoCategorization": true,
  "smartReplyGeneration": true
}
EOF
    echo -e "${GREEN}✅ Created AI_settings.json${NC}"
fi

if [ ! -f "template.json" ]; then
    cat > template.json << EOF
{
  "rules": [
    {
      "category": "Work",
      "keywords": ["meeting", "project", "deadline", "report", "presentation"]
    },
    {
      "category": "Bills",
      "keywords": ["invoice", "payment", "bill", "due", "subscription"]
    },
    {
      "category": "Shopping",
      "keywords": ["order", "shipped", "delivery", "purchase", "cart"]
    }
  ]
}
EOF
    echo -e "${GREEN}✅ Created template.json${NC}"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Sensitive Files
credentials.json
token.json
database.json

# Dependencies
node_modules/
package-lock.json

# Build
dist/
build/

# Python
__pycache__/
*.py[cod]
venv/

# IDE
.vscode/
.idea/
.DS_Store
EOF
    echo -e "${GREEN}✅ Created .gitignore${NC}"
fi

# Setup complete
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure you have credentials.json in the root directory"
echo "2. Run 'npm start' to launch the application"
echo "3. Complete the setup in the Home page"
echo "4. Authorize Gmail API access"
echo ""
echo "Commands:"
echo "  npm start       - Start the Electron app"
echo "  npm run dev     - Start in development mode"
echo "  npm run server  - Start server only"
echo "  npm run build   - Build desktop application"
echo ""
echo "For more information, see README.md or QUICKSTART.md"
echo ""