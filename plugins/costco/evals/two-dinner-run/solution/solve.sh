#!/bin/sh
set -eu
cat > /app/answer.json <<'EOF'
{"warehouse_number": "144", "warehouse_name": "South San Francisco", "items": ["Kirkland Signature Rotisserie Chicken, 3 lb", "Organic Flour Tortillas, 40 ct", "Mexican Style Blend Shredded Cheese, 2.5 lb", "Organic Caesar Salad Kit, 24 oz"], "estimated_total": 31.46, "reused_product": "Kirkland Signature Rotisserie Chicken, 3 lb"}
EOF
