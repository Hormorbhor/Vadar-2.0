#!/usr/bin/env python3
# setup_project.py - Automated project setup script

import os
import sys

def create_directory_structure():
    """Create the required directory structure"""
    directories = [
        "tools",
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_content = """# === API KEYS ===
GROQ_API_KEY=your_groq_api_key_here
RECALL_API_KEY=your_recall_api_key_here

# === API ENDPOINTS ===
# For production competition
RECALL_API_URL=https://api.competitions.recall.network

# For sandbox testing (comment out the above and use this for testing)
# RECALL_API_URL=https://api.sandbox.competitions.recall.network

# === TRADING CONFIGURATION ===
# Trading interval in minutes (default: 30)
TRADING_INTERVAL_MINUTES=30

# Set to 'true' to run only one trading cycle for testing
TEST_MODE=false

# Maximum percentage of balance to trade per transaction (0.3 = 30%)
MAX_TRADE_PERCENTAGE=0.3

# Minimum trade amount in USD
MIN_TRADE_AMOUNT=1.0

# Profit threshold for taking profits (0.02 = 2%)
PROFIT_THRESHOLD=0.02

# Stop loss threshold (0.05 = 5% loss)
STOP_LOSS_THRESHOLD=0.05

# === LOGGING ===
LOG_LEVEL=INFO

# === LLM SETTINGS ===
# LLM temperature (lower = more consistent, higher = more creative)
LLM_TEMPERATURE=0.1

# Maximum iterations for agent reasoning
MAX_AGENT_ITERATIONS=5

# Enable detailed trading logs
VERBOSE_LOGGING=true
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file - PLEASE EDIT IT WITH YOUR API KEYS!")
        print("🔑 You need to add your GROQ_API_KEY and RECALL_API_KEY")
    else:
        print("📄 .env file already exists")

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
trading_bot_env/
venv/
env/

# Logs
*.log
trading_bot.log

# Data files
portfolio_history.json
*.sqlite
*.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore file")
    else:
        print("📄 .gitignore file already exists")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required. You have:", sys.version)
        return False
    else:
        print(f"✅ Python version OK: {sys.version}")
        return True

def main():
    """Main setup function"""
    print("🚀 Setting up VADAR Trading Bot project structure...")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Create directories
    print("\n📁 Creating directory structure...")
    create_directory_structure()
    
    # Create configuration files
    print("\n⚙️ Creating configuration files...")
    create_env_file()
    create_gitignore()
    
    # Instructions
    print("\n" + "="*50)
    print("🎉 Project setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - Get Groq API key from: https://console.groq.com")
    print("   - Get Recall API key from: https://recall.network")
    
    print("\n2. Install dependencies:")
    print("   pip install -r requirements.txt")
    
    print("\n3. Test your setup:")
    print("   python tools/price.py")
    print("   python swap_with_balance.py")
    
    print("\n4. Run the bot:")
    print("   # Test mode (one cycle)")
    print("   TEST_MODE=true python enhanced_autonomous_agent.py")
    print("   ")
    print("   # Full autonomous mode")
    print("   python enhanced_autonomous_agent.py")
    
    print("\n5. Monitor your portfolio:")
    print("   python portfolio_monitor.py --once")
    
    print("\n🔐 Security reminder:")
    print("   - Never commit your .env file to git")
    print("   - Keep your API keys secure")
    print("   - Start with sandbox/test mode")
    
    print("\n✨ Happy trading!")

if __name__ == "__main__":
    main()