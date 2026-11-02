import sys
from pathlib import Path

# Add project root to sys.path so app package can be imported
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import create_app

app = create_app()
