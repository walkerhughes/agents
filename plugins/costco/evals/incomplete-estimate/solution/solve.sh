#!/bin/sh
set -eu
cat > /app/answer.json <<'EOF'
{"requested_items": 2, "priced_items": 1, "known_subtotal": 18.99, "unpriced_product": "Hass Avocados, 6 ct", "estimate_complete": false}
EOF
