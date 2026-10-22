#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ollama_bin="$project_root/.runtime/ollama/bin/ollama"
if [[ ! -x "$ollama_bin" ]]; then
  echo '프로젝트 내부 Ollama 실행 파일이 없습니다. docs/ollama.md 설치 안내를 확인하세요.' >&2
  exit 1
fi
# Manual loopback-only process; no system service or shell-profile changes.
export OLLAMA_MODELS="$project_root/.runtime/models"
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NO_CLOUD=1
exec "$ollama_bin" serve
