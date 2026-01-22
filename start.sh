#!/bin/bash

# CoralCollective Quick Start Script
# This script provides easy access to all CoralCollective functionality

echo "🪸 CoralCollective - AI Development Colony"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check and install required packages
check_and_install() {
    if ! python3 -c "import $1" 2>/dev/null; then
        echo "Installing $1..."
        pip3 install $1
    fi
}

echo "Checking dependencies..."
check_and_install "rich"
check_and_install "pyperclip" 
check_and_install "pyyaml"

clear

# Main menu
while true; do
    echo ""
    echo "🪸 CORALCOLLECTIVE COMMAND CENTER"
    echo "================================="
    echo ""
    echo "1. 🚀 Run Agent Workflow (Recommended)"
    echo "2. 🎯 Run Single Agent"
    echo "3. 📊 Project Manager"
    echo "4. 📈 View Dashboard"
    echo "5. 📝 Add Feedback"
    echo "6. 📋 List All Agents"
    echo "7. 🔧 Advanced Options"
    echo "8. ❌ Exit"
    echo ""
    read -p "Select option (1-8): " choice

    case $choice in
        1)
            echo ""
            echo "🚀 Starting Workflow Wizard..."
            python3 -m coral_collective.agent_runner workflow
            ;;
        2)
            echo ""
            echo "🎯 Running Single Agent..."
            python3 -m coral_collective.agent_runner run
            ;;
        3)
            echo ""
            echo "📊 Opening Project Manager..."
            python3 -m coral_collective.project_manager
            ;;
        4)
            echo ""
            echo "📈 Loading Dashboard..."
            python3 -m coral_collective.agent_runner dashboard
            ;;
        5)
            echo ""
            echo "📝 Feedback Collection"
            echo "Which agent would you like to provide feedback for?"
            read -p "Agent ID: " agent_id
            read -p "Issue description: " issue
            read -p "Improvement suggestion: " suggestion
            read -p "Priority (low/medium/high/critical): " priority
            python3 -m coral_collective.tools.feedback_collector feedback \
                --agent "$agent_id" \
                --issue "$issue" \
                --suggestion "$suggestion" \
                --priority "$priority"
            ;;
        6)
            echo ""
            echo "📋 Available Agents:"
            python3 -m coral_collective.agent_runner list
            ;;
        7)
            echo ""
            echo "🔧 Advanced Options"
            echo "==================="
            echo "a. Generate Performance Report"
            echo "b. Export Project Data"
            echo "c. View Agent Metrics"
            echo "d. Check Pending Improvements"
            echo "e. Back to Main Menu"
            read -p "Select option: " adv_choice
            
            case $adv_choice in
                a)
                    echo "Generating performance report..."
                    python3 -m coral_collective.tools.feedback_collector report
                    ;;
                b)
                    echo "Export project data..."
                    read -p "Project name: " project_name
                    read -p "Format (yaml/json/markdown): " format
                    python3 -c "
from coral_collective.project_manager import ProjectManager
m = ProjectManager()
m.export_project('$project_name', '$format')
"
                    ;;
                c)
                    echo "View agent metrics..."
                    read -p "Agent ID (or press Enter for all): " agent_id
                    if [ -z "$agent_id" ]; then
                        cat metrics/agent_metrics.yaml
                    else
                        grep -A 20 "$agent_id:" metrics/agent_metrics.yaml
                    fi
                    ;;
                d)
                    echo "Checking pending improvements..."
                    grep -B 2 "status: pending" feedback/agent_feedback.yaml | grep -E "agent:|issue:" 
                    ;;
                e)
                    continue
                    ;;
            esac
            ;;
        8)
            echo ""
            echo "👋 Thank you for using CoralCollective!"
            echo "Your feedback helps the colony grow stronger."
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    clear
done