@echo off
set "API_URL=REPLACE_WITH_YOUR_INVOKE_URL"

curl -X POST "%API_URL%/orders" ^
  -H "Content-Type: application/json" ^
  -d "{\"customerName\":\"Ziyad\",\"items\":[\"Keyboard\",\"Mouse\"],\"total\":450}"

echo.
pause

