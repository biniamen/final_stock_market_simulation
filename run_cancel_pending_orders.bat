@echo off
REM Log the start time
echo [%date% %time%] Starting cancel_pending_orders >> "D:\Final Project Related Document\Project Source Code\ethiopian_stock_market\ethio_stock_simulation\cron.log"

REM Activate the virtual environment
call "D:\Final Project Related Document\Project Source Code\ethiopian_stock_market\env\Scripts\activate.bat"

REM Navigate to the project directory
cd /d "D:\Final Project Related Document\Project Source Code\ethiopian_stock_market\ethio_stock_simulation"

REM Execute the management command and log output
python manage.py cancel_pending_orders >> "D:\Final Project Related Document\Project Source Code\ethiopian_stock_market\ethio_stock_simulation\cron.log" 2>&1

REM Log the end time
echo [%date% %time%] Finished cancel_pending_orders >> "D:\Final Project Related Document\Project Source Code\ethiopian_stock_market\ethio_stock_simulation\cron.log"
