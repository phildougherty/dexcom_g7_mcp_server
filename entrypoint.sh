#!/bin/sh
set -e

INTERNAL_PORT="${MCP_SOCAT_INTERNAL_PORT:-12345}"
SERVER_COMMAND="$1"

# If no command provided, use default from CMD  
if [ -z "$SERVER_COMMAND" ]; then
    SERVER_COMMAND="python"
    SERVER_ARGS="server.py"
else
    shift
    SERVER_ARGS="$@"
fi

echo "Socat Hoster: Starting socat on TCP port $INTERNAL_PORT to execute: $SERVER_COMMAND $SERVER_ARGS" >&2

# Remove the fork option and don't use PTY - simpler approach
exec socat TCP-LISTEN:$INTERNAL_PORT,reuseaddr,bind=0.0.0.0 EXEC:"$SERVER_COMMAND $SERVER_ARGS"