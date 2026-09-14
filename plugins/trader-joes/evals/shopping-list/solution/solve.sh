#!/bin/sh
set -eu
cat > /app/answer.json <<'EOF'
{"items": ["Costa Rica Coffee", "Non-Dairy Oat Beverage"], "estimated_total": 12.48}
EOF
