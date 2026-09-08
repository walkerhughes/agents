#!/bin/sh
set -eu
cat > /app/answer.json <<'EOF'
{"name": "Lucerne Milk Whole - Half Gallon", "price": 3.99, "base_price": 4.49, "inventory_available": true}
EOF
