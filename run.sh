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

# Load Hermes/OpenRouter credentials when the project is run outside a Hermes process.
if [ -n "${HERMES_HOME:-}" ] && [ -f "$HERMES_HOME/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$HERMES_HOME/.env"
    set +a
fi

# Load project .env if present
if [ -f "$INTELLIGENCE_DIR/.env" ]; then
    echo "Loading .env..."
    set -a
    # shellcheck disable=SC2046
    source "$INTELLIGENCE_DIR/.env"
    set +a
fi

if [ -z "${TYPESAFE_API_KEY:-}" ]; then
    echo "⚠️  TYPESAFE_API_KEY not set — using fallback evaluation"
    echo "   Set TYPESAFE_API_KEY for real Jev atomic judgements"
    echo ""
fi

if [ -z "${OPENROUTER_API_KEY:-}" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "⚠️  No OpenRouter/OpenAI key set — LLM interpretation disabled"
    echo "   OpenRouter is supported via OPENROUTER_API_KEY"
    echo ""
fi

if [ -n "${OPENROUTER_API_KEY:-}" ]; then
    export OPENROUTER_BASE_URL="${OPENROUTER_BASE_URL:-https://openrouter.ai/api/v1}"
    export OPENROUTER_MODEL="${OPENROUTER_MODEL:-deepseek/deepseek-v4-flash}"
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