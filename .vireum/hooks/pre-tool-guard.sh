#!/bin/bash
# Vireum Spec — Pre-Tool Guard Hook (Soft Enforcement)
# Gerado por vireum-spec setup
# Avisa se .spec/INDEX.md não foi lido nesta sessão

INDEX_FILE=".spec/INDEX.md"
FLAG_FILE="/tmp/vireum_index_read_$$"

# Verificar se INDEX.md foi lido (marcado por outro hook ou ação)
if [ ! -f "$FLAG_FILE" ] && [ -f "$INDEX_FILE" ]; then
  echo ""
  echo "⚠️  AVISO: .spec/INDEX.md não foi lido nesta sessão"
  echo "   Leia o INDEX.md antes de implementar para entender o contexto"
  echo ""
fi
