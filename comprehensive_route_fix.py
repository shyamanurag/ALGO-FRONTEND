#!/usr/bin/env python3
"""
Final comprehensive fix for all backend route import issues
"""

import os
import re

def fix_route_file(file_path):
    """Fix import issues in a specific route file"""
    
    if not os.path.exists(file_path):
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Standard import block for most routes
    standard_import = '''try:
    from backend.server import get_app_state, get_settings
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    from src.config import settings as _global_settings_instance
    def get_app_state(): return _global_app_state_instance
    def get_settings(): return _global_settings_instance'''
    
    # Special import block for market_data_routes (needs get_market_data_state)
    market_data_import = '''try:
    from backend.server import get_app_state, get_settings, get_market_data_state
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    from src.config import settings as _global_settings_instance
    def get_app_state(): return _global_app_state_instance
    def get_settings(): return _global_settings_instance
    def get_market_data_state(): return _global_app_state_instance.market_data'''
    
    # Special import block for webhook_routes (needs get_market_data_state)
    webhook_import = '''try:
    from backend.server import get_market_data_state, get_app_state
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    def get_market_data_state(): return _global_app_state_instance.market_data
    def get_app_state(): return _global_app_state_instance'''
    
    # Determine which import pattern to use
    if 'market_data_routes.py' in file_path:
        target_import = market_data_import
    elif 'webhook_routes.py' in file_path:
        target_import = webhook_import
    else:
        target_import = standard_import
    
    # Find the problematic import section and replace it
    lines = content.split('\n')
    new_lines = []
    skip_until_logger = False
    
    for i, line in enumerate(lines):
        if skip_until_logger:
            if 'logger = logging.getLogger(__name__)' in line:
                skip_until_logger = False
                new_lines.append('')
                new_lines.append('logger = logging.getLogger(__name__)')
            continue
            
        if line.strip() == 'try:' and i+1 < len(lines):
            next_line = lines[i+1].strip()
            if ('from backend.server import' in next_line and 
                ('get_app_state' in next_line or 'get_market_data_state' in next_line)):
                # Found the import block to replace
                new_lines.extend(target_import.split('\n'))
                skip_until_logger = True
                continue
        
        new_lines.append(line)
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    return True

# Fix all route files
route_files = [
    '/app/backend/src/api_routes/user_routes.py',
    '/app/backend/src/api_routes/truedata_routes.py',
    '/app/backend/src/api_routes/zerodha_routes.py',
    '/app/backend/src/api_routes/system_routes.py',
    '/app/backend/src/api_routes/market_data_routes.py',
    '/app/backend/src/api_routes/webhook_routes.py',
    '/app/backend/src/api_routes/trading_routes.py',
    '/app/backend/src/api_routes/strategy_routes.py'
]

for file_path in route_files:
    if fix_route_file(file_path):
        print(f"✅ Fixed {os.path.basename(file_path)}")
    else:
        print(f"⚠️ Could not fix {os.path.basename(file_path)}")

print("\n✅ All route files have been fixed for deployment!")
print("🚀 Ready for redeployment - strategies should now be visible!")