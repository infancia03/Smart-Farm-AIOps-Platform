#!/bin/bash

echo "🌾 Smart Farm AIOps Platform - Setup Script"
echo "==========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  .env file not found!"
    cp .env.example .env
    echo "✓ Created .env from template"
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your OpenRouter API key!"
    echo "   Get one at: https://openrouter.ai/keys"
    echo ""
    read -p "Press enter after you've updated .env..."
fi

# Generate sample data
echo ""
read -p "Generate sample sensor data? (y/n): " gen_data
if [ "$gen_data" = "y" ]; then
    echo "Generating sample data..."
    python data/seed_data.py
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Quick Start:"
echo "  1. Start API server: python app/main.py"
echo "  2. In new terminal, start dashboard: python ui/dashboard.py"
echo "  3. Visit http://localhost:7860"
echo ""
echo "📚 See README.md for detailed usage instructions"
