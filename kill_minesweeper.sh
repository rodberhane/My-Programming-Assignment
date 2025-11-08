#!/bin/bash

# Minesweeper Game - Kill Script
# ===============================
# This script finds and terminates any running Minesweeper game processes.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Minesweeper Game - Kill Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for non-interactive mode (--force flag)
FORCE_KILL=false
if [ "$1" == "--force" ] || [ "$1" == "-f" ]; then
    FORCE_KILL=true
fi

# Find all Python processes running minesweeper.py
# Use pgrep for more reliable process finding
PIDS=$(pgrep -f "minesweeper.py" 2>/dev/null || ps aux | grep -i "[p]ython.*minesweeper.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}No Minesweeper processes found.${NC}"
    echo -e "${GREEN}✓${NC} Game is not running."
    exit 0
fi

# Count how many processes found (handle single vs multiple)
if [ $(echo "$PIDS" | wc -l) -eq 1 ] && [ -z "$(echo "$PIDS" | tr -d '[:space:]')" ]; then
    # Empty result
    echo -e "${YELLOW}No Minesweeper processes found.${NC}"
    echo -e "${GREEN}✓${NC} Game is not running."
    exit 0
fi

# Count how many processes found
COUNT=$(echo "$PIDS" | grep -v '^$' | wc -l | tr -d ' ')
echo -e "${YELLOW}Found $COUNT Minesweeper process(es):${NC}"

# Show the processes
for PID in $PIDS; do
    if [ ! -z "$PID" ] && [ "$PID" != "" ]; then
        PROCESS_INFO=$(ps -p $PID -o pid,command --no-headers 2>/dev/null | head -1)
        if [ ! -z "$PROCESS_INFO" ]; then
            echo -e "  PID: ${BLUE}$PID${NC} - $(echo "$PROCESS_INFO" | sed 's/^[[:space:]]*[0-9]*[[:space:]]*//')"
        fi
    fi
done

echo ""

# Skip confirmation if --force flag is used
if [ "$FORCE_KILL" = true ]; then
    REPLY="y"
else
    read -p "Kill these processes? (y/N): " -n 1 -r
    echo ""
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    KILLED=0
    FAILED=0
    
    for PID in $PIDS; do
        # Check if process still exists
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Killing process $PID...${NC}"
            kill $PID 2>/dev/null
            
            # Wait a moment and check if it's still running
            sleep 0.5
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}  Process still running, forcing kill...${NC}"
                kill -9 $PID 2>/dev/null
                sleep 0.2
            fi
            
            # Verify it's dead
            if ! ps -p $PID > /dev/null 2>&1; then
                echo -e "${GREEN}  ✓${NC} Process $PID terminated"
                ((KILLED++))
            else
                echo -e "${RED}  ✗${NC} Failed to kill process $PID"
                ((FAILED++))
            fi
        else
            echo -e "${YELLOW}  Process $PID already terminated${NC}"
        fi
    done
    
    echo ""
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All Minesweeper processes terminated successfully."
    else
        echo -e "${YELLOW}⚠${NC} Killed $KILLED process(es), $FAILED failed."
        echo -e "${YELLOW}  You may need to kill them manually with: kill -9 <PID>${NC}"
    fi
else
    echo -e "${YELLOW}Cancelled. No processes were killed.${NC}"
fi

echo ""

