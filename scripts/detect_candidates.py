import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.improve_candidate_detection import detect_candidates

if __name__ == "__main__":
    detect_candidates()
