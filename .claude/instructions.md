# Claude Work Protocol - Mandatory Instructions

## Branch and Sync Management - CRITICAL PRIORITY

**At the START of every conversation:**
1. ALWAYS ask: "What branch are you currently working on locally?"
2. WAIT for response before proceeding
3. Check out that exact branch before making ANY changes
4. Confirm: "I've checked out branch [branch-name] to match your local environment"

**After EVERY git push:**
1. IMMEDIATELY tell the user: "⚠️ PULL REQUIRED: I've pushed changes to [branch-name]. Run: `git pull origin [branch-name]`"
2. WAIT for user confirmation of pull before proceeding with testing/verification
3. NEVER assume changes are available locally without explicit pull confirmation

**Environment Separation Rules:**
- Claude's working directory is COMPLETELY SEPARATE from user's local machine
- Changes Claude makes are NOT automatically on user's machine
- Changes user makes are NOT automatically in Claude's environment
- ALWAYS require explicit push/pull operations to sync
- NEVER say "you don't need to pull" - this is ALWAYS wrong

**If user reports errors:**
1. FIRST ask: "Have you pulled the latest changes from [branch-name]?"
2. Verify branches are in sync before troubleshooting
3. Confirm both on same branch and commit

## Git/Branch Management
- NEVER create new branches unless explicitly requested
- Always work on main branch by default
- If creating a branch, immediately notify with branch name and reason

## Task Execution Protocol

**Prompt Acknowledgment:**
- Timestamp in UTC format (HH:MM UTC)
- Estimated completion time
- Example: "ACKNOWLEDGED [15:45 UTC] - Estimated completion: 3 minutes"

**Progress Communication:**
- Provide check-in every 5 minutes while working
- Notify immediately upon task completion
- Notify immediately if unable to continue

**System Interruptions:**
If progress stops or system pauses work, immediately notify:
"⚠️ PROGRESS PAUSED BY SYSTEM - Work has stopped. Possible rate limiting or system interruption."

**Rate Limiting:**
If delivery exceeds estimated time without explanation, assume rate limiting is occurring.

**Failed Tasks:**
Do not continue working without producing results. If task cannot be completed, notify immediately and stop.

**Follow-up Questions:**
- Ask any required clarifying questions before starting
- If no clarification needed, acknowledge receipt and proceed
