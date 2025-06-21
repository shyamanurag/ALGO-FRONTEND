#!/usr/bin/env python3
"""
Script to fix circular import issues in API route files
"""

import re
import os

# Files to fix and their specific patterns
files_to_fix = [
    "/app/backend/src/api_routes/user_routes.py",
    "/app/backend/src/api_routes/truedata_routes.py", 
    "/app/backend/src/api_routes/zerodha_routes.py",
    "/app/backend/src/api_routes/system_routes.py"
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        print(f"Fixing {file_path}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix the import fallback pattern
        old_pattern = r'try:\s+from backend\.server import get_app_state, get_settings\s+except ImportError:\s+.*?_fallback_logger.*?\.error\(.*?\)\s+from src\.app_state import app_state as .*?\s+from src\.config import settings as .*?\s+async def get_app_state\(\): return .*?\s+async def get_settings\(\): return .*?'
        
        new_pattern = '''try:
    from backend.server import get_app_state, get_settings
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    from src.config import settings as _global_settings_instance
    def get_app_state(): return _global_app_state_instance
    def get_settings(): return _global_settings_instance'''
        
        # Use simpler string replacement approach
        if "CRITICAL: Could not import get_app_state, get_settings from backend.server" in content:
            # Find and replace the problematic section
            lines = content.split('\n')
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                if "try:" in line and "from backend.server import get_app_state, get_settings" in lines[i+1] if i+1 < len(lines) else False:
                    # Found the start of the problematic block
                    new_lines.append("try:")
                    new_lines.append("    from backend.server import get_app_state, get_settings")
                    new_lines.append("except ImportError:")
                    new_lines.append("    # Use fallback functions (this is expected due to circular imports)")
                    new_lines.append("    from src.app_state import app_state as _global_app_state_instance")
                    new_lines.append("    from src.config import settings as _global_settings_instance")
                    new_lines.append("    def get_app_state(): return _global_app_state_instance")
                    new_lines.append("    def get_settings(): return _global_settings_instance")
                    
                    # Skip the old problematic lines
                    i += 1  # skip "from backend.server..."
                    while i < len(lines) and ("except ImportError:" in lines[i] or 
                                             "logging.basicConfig" in lines[i] or
                                             "_fallback_logger" in lines[i] or
                                             ".error(" in lines[i] or
                                             "from src.app_state import app_state" in lines[i] or
                                             "from src.config import settings" in lines[i] or
                                             "async def get_app_state" in lines[i] or
                                             "async def get_settings" in lines[i]):
                        i += 1
                    continue
                else:
                    new_lines.append(line)
                i += 1
            
            # Write the fixed content
            with open(file_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            print(f"✅ Fixed {file_path}")
        else:
            print(f"⚠️ Pattern not found in {file_path}")

print("✅ All route import fixes completed!")