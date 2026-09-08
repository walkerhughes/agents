#!/bin/sh
set -eu
cat > /app/answer.json <<'EOF'
{"store_id": "2766", "name": "San Francisco Central", "distance_miles": 1.8, "pickup_status": "IN_STOCK"}
EOF
