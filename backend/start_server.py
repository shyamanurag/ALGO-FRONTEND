"""
Simple startup script for ALGO-FRONTEND backend without file watching
"""
import sys
import os
sys.path.append('/app/backend')

# Import the app
from server import app

if __name__ == "__main__":
    import uvicorn
    
    # Create log directory
    os.makedirs('/var/log/algo-trading', exist_ok=True)
    
    # Run without file watching to avoid file watch limit
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        reload=False,  # Disable auto-reload to avoid file watch issues
        log_level="info"
    )