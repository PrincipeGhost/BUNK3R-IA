@echo off
title BUNK3R - Ollama ^& Tunnel Control
color 0E

echo ==========================================================
echo    BUNK3R AI - INICIADOR DE CEREBRO LOCAL (Ollama)
echo ==========================================================
echo.

echo [1] Iniciando Servidor Ollama...
start "BUNK3R - Ollama Serve" cmd /k "ollama serve"

echo [2] Esperando 5 segundos para que el motor caliente...
timeout /t 5 /nobreak > nul

echo [3] Iniciando Puente de Comunicacion para Render (Cloudflare)...
start "BUNK3R - Cloudflare Tunnel" cmd /k "cloudflared tunnel --url http://localhost:11434"

echo.
echo ==========================================================
echo ¡PROCESO COMPLETADO!
echo.
echo RECUERDA:
echo 1. Revisa la ventana de Cloudflare Tunnel.
echo 2. Busca la URL que dice https://...trycloudflare.com
echo 3. Copia esa URL en Render bajo OLLAMA_BASE_URL.
echo ==========================================================
echo.
pause
