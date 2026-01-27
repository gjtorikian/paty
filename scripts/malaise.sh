#!/bin/bash
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"The paty plugin is active. When hooks block a tool, the block reason will be shown to the user directly — you do not need to relay or act on those messages."}}
EOF
exit 0
