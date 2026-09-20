#!/bin/bash
# Inflexion Intelligence Engine — Manual Run Script
# Usage: ./run.sh [site_root]

set -e

SITE_ROOT="${1:-/Users/nicholaschristensen/Projects/04-inflexion/08-Website}"
INTELLIGENCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "  INFLEXION INTELLIGENCE ENGINE"
echo "  Manual run: $INTELLIGENCE_DIR/run.sh"
echo "============================================"
echo ""

# Check for API keys
if [ -z "$TYPESAFE_API_KEY" ]; then
    echo "⚠️  TYPESAFE_API_KEY not set — using fallback evaluation"
    echo "   Set TYPESAFE_API_KEY for real Jev atomic judgements"
    echo ""
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set — LLM interpretation disabled"
    echo "   Set OPENAI_API_KEY for strategic interpretation layer"
    echo ""
fi

# Load .env if present
if [ -f "$INTELLIGENCE_DIR/.env" ]; then
    echo "Loading .env..."
    export $(grep -v '^#' "$INTELLIGENCE_DIR/.env" | xargs)
fi

# Run the pipeline
cd "$INTELLIGENCE_DIR"
PYTHONPATH=. python3 pipelines/full_run.py "$SITE_ROOT"

echo ""
echo "============================================"
echo "  RUN COMPLETE"
echo "============================================"
echo ""
echo "Results saved to: $INTELLIGENCE_DIR/data/"
echo "Visualisations: $INTELLIGENCE_DIR/data/visualisations/"
echo ""
echo "To view the dashboard:"
echo "  cd $INTELLIGENCE_DIR/ui && python3 -m http.server 8080"
echo "  Then open http://localhost:8080/dashboard.html"
echo ""
echo "To query the intelligence:"
echo "  PYTHONPATH=. python3 -c \""
echo "  from intelligence.interface.ask_the_site import create_ask_the_site"
echo "  from intelligence.core.models import IntelligenceRun"
echo "  import json"
echo "  with open('data/latest_run.json') as f:"
echo "      run = IntelligenceRun.from_json(f.read())"
echo "  asker = create_ask_the_site(run)"
echo "  result = asker.query('Why is AI Discovery underperforming?')"
echo "  print(result.answer)"
echo "  \""