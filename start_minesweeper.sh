#!/bin/bash

# Minesweeper Game - Start Script
# ================================
# This script sets up and runs the Minesweeper game.
# It handles dependency checking, installation, and launches the game.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Minesweeper Game - Starting...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓${NC} Found: $PYTHON_VERSION"

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment found"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python3 -m pip install --upgrade pip --quiet

# Check and install dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies (this may take a moment)...${NC}"
python3 -m pip install -r requirements.txt --quiet || {
    echo -e "${YELLOW}Some packages may need to be installed manually. Trying individual packages...${NC}"
    python3 -m pip install PyQt5 --quiet || echo -e "${RED}Warning: PyQt5 installation failed${NC}"
    python3 -m pip install matplotlib --quiet || echo -e "${RED}Warning: matplotlib installation failed${NC}"
    python3 -m pip install "numpy>=1.20" --quiet || echo -e "${RED}Warning: numpy installation failed${NC}"
}

# Verify dependencies
echo ""
echo -e "${YELLOW}Verifying dependencies...${NC}"

# Check PyQt5
if python3 -c "from PyQt5 import QtCore" 2>/dev/null; then
    QT_VERSION=$(python3 -c "from PyQt5 import QtCore; print(QtCore.QT_VERSION_STR)" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓${NC} PyQt5 OK (Qt $QT_VERSION)"
else
    echo -e "${RED}✗${NC} PyQt5 not available"
    echo -e "${YELLOW}  Try: pip install PyQt5${NC}"
    exit 1
fi

# Check numpy
if python3 -c "import numpy" 2>/dev/null; then
    NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null)
    echo -e "${GREEN}✓${NC} numpy OK (version $NUMPY_VERSION)"
else
    echo -e "${RED}✗${NC} numpy not available"
    echo -e "${YELLOW}  Try: pip install numpy${NC}"
    exit 1
fi

# Check matplotlib (optional for analytics)
if python3 -c "import matplotlib" 2>/dev/null; then
    MATPLOTLIB_VERSION=$(python3 -c "import matplotlib; print(matplotlib.__version__)" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓${NC} matplotlib OK (version $MATPLOTLIB_VERSION)"
else
    echo -e "${YELLOW}⚠${NC} matplotlib not available (analytics feature will be limited)"
fi

# Check if game file exists
if [ ! -f "minesweeper.py" ]; then
    echo -e "${RED}Error: minesweeper.py not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   All checks passed!${NC}"
echo -e "${GREEN}   Launching Minesweeper...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Run the game
python3 minesweeper.py

# If we get here, the game has exited
echo ""
echo -e "${BLUE}Game closed. Thank you for playing!${NC}"
