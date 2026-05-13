@echo off
chcp 65001 >nul
echo ================================
echo   盼之代售 AI 客服 Demo 启动
echo ================================
echo.

cd /d "%~dp0"

:: 检查 config.py 中的 API_KEY
python -c "import config; assert config.API_KEY, '请先在 config.py 中填写 API_KEY'" 2>nul
if errorlevel 1 (
    echo [错误] 请先在 config.py 中填写 API_KEY 和 API_BASE
    echo.
    echo 支持的 AI 提供商:
    echo   DeepSeek:  API_BASE=https://api.deepseek.com  MODEL=deepseek-chat
    echo   智谱GLM:   API_BASE=https://open.bigmodel.cn/api/paas/v4  MODEL=glm-4-flash
    echo   通义千问:   API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1  MODEL=qwen-plus
    echo.
    pause
    exit /b 1
)

:: 检查依赖
python -c "import flask" 2>nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt -q
)

echo 启动服务...
echo 打开浏览器访问: http://127.0.0.1:5000
echo.
python app.py
pause