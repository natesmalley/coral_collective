#!/usr/bin/env python3
"""
Update all agent markdown files to include scratchpad and activity_tracker documentation
"""

import os
from pathlib import Path

# The section to add to each agent
TOOLS_SECTION = """
WORKING MEMORY & COORDINATION TOOLS:
You MUST use these two essential files throughout your work:

1. **scratchpad.md** (Project root)
   - Your temporary working memory and notes
   - Questions and discoveries to share with other agents
   - Draft content and ideas before finalizing
   - READ at start, UPDATE during work, CLEAN before handoff

2. **activity_tracker.md** (Project root)
   - Log ALL actions you take with timestamps
   - Document what worked, what failed, and why
   - Record files created/modified
   - Essential for retry logic and debugging

MANDATORY WORKFLOW:
- START: Read both files to understand current state
- DURING: Update activity_tracker with your progress
- DURING: Use scratchpad for notes and questions
- END: Finalize activity_tracker entry with results
- END: Clean scratchpad leaving only relevant notes for next agent

Example activity_tracker.md entry:
```
### [2025-01-15 10:30] {Agent Name}
**Task**: {What you're working on}
**Actions Taken**:
1. {First action}
2. {Second action}
**Results**: ✅ Success / ❌ Failed / ⚠️ Partial
**Files Modified**: {list of files}
**Notes for Next Agent**: {Important information}
```
"""

def update_agent_file(file_path: Path):
    """Update a single agent file with tools documentation"""
    
    # Skip the common tools file itself
    if file_path.name == "AGENT_COMMON_TOOLS.md":
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if "scratchpad.md" in content and "activity_tracker.md" in content:
        print(f"  ✓ Already updated: {file_path.name}")
        return False
    
    # Find where to insert (after the main prompt section, before usage/handoff)
    # Look for common patterns
    insert_markers = [
        "CLAUDE CODE OPTIMIZATION:",
        "DELIVERABLES:",
        "HANDOFF PROTOCOL:",
        "PROJECT STRUCTURE",
        "WORKING STYLE:",
        "AGENT HANDOFF WORKFLOW:",
        "Example handoff format:",
    ]
    
    insert_pos = -1
    for marker in insert_markers:
        pos = content.find(marker)
        if pos != -1:
            insert_pos = pos
            break
    
    if insert_pos == -1:
        # If no marker found, try to insert before the closing ``` of the prompt
        if "```" in content:
            # Find the last ``` before "## Usage" or "## Key"
            parts = content.split("```")
            if len(parts) >= 2:
                # Reconstruct with our section inserted
                new_content = "```".join(parts[:-1]) + TOOLS_SECTION + "\n```" + parts[-1]
            else:
                new_content = content + "\n" + TOOLS_SECTION
        else:
            # Just append if structure is unclear
            new_content = content + "\n" + TOOLS_SECTION
    else:
        # Insert before the marker
        new_content = content[:insert_pos] + TOOLS_SECTION + "\n" + content[insert_pos:]
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"  ✅ Updated: {file_path.name}")
    return True

def main():
    """Update all agent files"""
    base_path = Path(__file__).parent / "agents"
    
    # Get all markdown files
    agent_files = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.md') and file != 'AGENT_COMMON_TOOLS.md':
                agent_files.append(Path(root) / file)
    
    print(f"Found {len(agent_files)} agent files to update\n")
    
    updated_count = 0
    for agent_file in agent_files:
        relative_path = agent_file.relative_to(base_path)
        print(f"Processing: {relative_path}")
        if update_agent_file(agent_file):
            updated_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Updated {updated_count} agent files")
    print(f"📝 All agents now have scratchpad.md and activity_tracker.md documentation")
    print(f"\nNext steps:")
    print(f"1. Project Architect will create these files in new projects")
    print(f"2. All agents will use them for coordination")
    print(f"3. Better handoffs and no lost work!")

if __name__ == "__main__":
    main()