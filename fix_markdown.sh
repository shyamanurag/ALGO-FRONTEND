#!/bin/bash
# Fix markdown syntax errors in Python files

files=(
    "/app/backend/src/trading_strategies.py"
    "/app/backend/src/scheduler_jobs.py"
    "/app/backend/src/core/security.py"
    "/app/backend/src/core/logging_config.py"
    "/app/backend/src/core/utils.py"
    "/app/backend/src/core/schemas.py"
    "/app/backend/src/core/tests/test_utils.py"
    "/app/backend/src/core/tests/test_security.py"
    "/app/backend/src/market_data_handling.py"
    "/app/backend/src/clients/zerodha_client.py"
    "/app/backend/src/clients/tests/test_zerodha_client.py"
    "/app/backend/src/database.py"
    "/app/backend/src/api_routes/user_routes.py"
    "/app/backend/src/api_routes/truedata_routes.py"
    "/app/backend/src/api_routes/trading_routes.py"
    "/app/backend/src/api_routes/strategy_routes.py"
    "/app/backend/src/api_routes/admin_routes.py"
    "/app/backend/src/api_routes/zerodha_routes.py"
    "/app/backend/src/api_routes/webhook_routes.py"
    "/app/backend/src/api_routes/system_routes.py"
    "/app/backend/src/api_routes/market_data_routes.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Fixing $file"
        # Remove markdown code block markers from the end of files
        sed -i '/^```$/d' "$file"
        # Remove any trailing empty lines after the fix
        sed -i -e :a -e '/^\s*$/N; s/\n$//; ta' "$file"
    fi
done

echo "✅ Fixed markdown syntax errors in Python files"