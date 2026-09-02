import sys
import os

# Ensure the parent directory is in sys.path so app.py can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel entrypoint
app.debug = False
