#!/bin/bash
# Vireum Spec — Context Injection Hook
# Gerado por vireum-spec setup
# Injeta tasks ativas no contexto do prompt

SPEC_DIR=".spec"
ACTIVE_TASKS="${SPEC_DIR}/tasks/active.md"

if [ -f "$ACTIVE_TASKS" ]; then
  echo ""
  echo "📋 Tasks Ativas (Context Inject):"
  echo "=================================="
  grep "^##" "$ACTIVE_TASKS" | head -10
  echo ""
fi
