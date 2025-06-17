"""
TrueData Library Patch
Fixes the lz4 decompression issue in TrueData library
"""
import sys
import os

# Add the TrueData package to modify it
truedata_path = '/root/.venv/lib/python3.11/site-packages/truedata/websocket'
sys.path.insert(0, truedata_path)

# Patch the decompression function
def patch_truedata_decompress():
    """Patch the TrueData decompression function"""
    try:
        import lz4.block
        from truedata.websocket.utils import msg_map, map_data_with_types
        
        def decompress_data_fixed(data):
            """Fixed decompression function"""
            try:
                # Convert string to bytes if needed
                if isinstance(data, str):
                    data = data.encode('utf-8')
                    
                uncomp_length = 1024
                decompressed = lz4.block.decompress(data, uncomp_length)
            except Exception as e:
                try:
                    # Convert string to bytes if needed
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                        
                    uncomp_length = len(data) * 5
                    decompressed = lz4.block.decompress(data, uncomp_length)
                except Exception as e2:
                    # If still failing, return empty data
                    print(f"❌ TrueData decompression failed: {e2}")
                    return {}
                    
            try:
                msg_code = decompressed[:1].decode('utf-8')
                map_fields_with_bytes = msg_map[msg_code]
                data_dict = dict(map(lambda x: map_data_with_types(x, decompressed), map_fields_with_bytes))
                return data_dict
            except Exception as e:
                print(f"❌ TrueData data parsing failed: {e}")
                return {}
        
        # Replace the function in the utils module
        import truedata.websocket.utils as utils
        utils.decompress_data = decompress_data_fixed
        
        print("✅ TrueData decompression function patched successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to patch TrueData: {e}")
        return False

# Apply the patch
if __name__ == "__main__":
    patch_truedata_decompress()