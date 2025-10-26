#!/bin/bash
# AutoQuant Web Application Startup Script

echo "🚀 Starting AutoQuant Web Application..."
echo "📱 Mobile & Desktop Responsive Dashboard"
echo ""

# Check if virtual environment exists
if [ -d "../venv" ]; then
    echo "✅ Activating virtual environment..."
    source ../venv/bin/activate
else
    echo "⚠️  Warning: Virtual environment not found at ../venv"
    echo "   Proceeding with system Python..."
fi

# Check Flask installation
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Error: Flask is not installed"
    echo "   Please run: pip install flask"
    exit 1
fi

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check database connectivity
echo "🔍 Checking database connection..."
if python3 -c "from src.database import Database; db = Database(); db.get_session().close()" 2>/dev/null; then
    echo "✅ Database connection OK"
else
    echo "⚠️  Warning: Database connection failed"
    echo "   Check your .env file configuration"
fi

# Start the web app
echo ""
echo "🌐 Starting Flask server..."
echo "   Access at: http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

cd "$PROJECT_ROOT/webapp"
python3 app_new.py
