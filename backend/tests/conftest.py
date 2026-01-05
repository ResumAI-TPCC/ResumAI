import sys
from pathlib import Path

# Ensure backend/app is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))