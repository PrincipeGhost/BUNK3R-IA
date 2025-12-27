@echo off
title BUNK3R - Brain Hub ^& Tunnel Control
setlocal enabledelayedexpansion
color 0E

echo ==========================================================
echo    BUNK3R AI - INICIADOR DE CEREBRO LOCAL (Ollama)
echo ==========================================================
echo.

:: Check if Ollama is already running
tasklist /fi "imagename eq ollama.exe" | find /i "ollama.exe" > nul
if %errorlevel% equ 0 (
    echo [+] Ollama ya esta corriendo en segundo plano.
) else (
    echo [1] Iniciando Servidor Ollama...
    start "BUNK3R - Ollama Serve" cmd /k "ollama serve"
    echo [2] Esperando a que el motor caliente...
    timeout /t 5 /nobreak > nul
)

:: Re-verify Ollama
curl -s http://localhost:11434/api/tags > nul
if %errorlevel% neq 0 (
    echo [!] ADVERTENCIA: No se pudo verificar Ollama en puerto 11434.
    echo     Asegurate de que este instalado y funcionando.
) else (
    echo [+] Ollama verificado y listo.
)

echo.
echo [3] Iniciando Puente de Comunicacion y Registro...

:: Create a temporary PS1 script for registration
if exist tunnel_log.txt del /f /q tunnel_log.txt
echo $url = ""; > reg_brain.ps1
echo $proc = Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:11434" -PassThru -NoNewWindow -RedirectStandardError "tunnel_log.txt"; >> reg_brain.ps1
echo echo "Esperando a que Cloudflare genere la URL (max 20s)..."; >> reg_brain.ps1
echo $timeout = Get-Date; $timeout = $timeout.AddSeconds(20); >> reg_brain.ps1
echo while ($(Get-Date) -lt $timeout) { >> reg_brain.ps1
echo     if (Test-Path "tunnel_log.txt") { >> reg_brain.ps1
echo         $content = Get-Content "tunnel_log.txt" -Raw; >> reg_brain.ps1
echo         if ($content -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") { >> reg_brain.ps1
echo             $url = $matches[0]; >> reg_brain.ps1
echo             if ($url) { break; } >> reg_brain.ps1
echo         } >> reg_brain.ps1
echo     } >> reg_brain.ps1
echo     Start-Sleep -s 1; >> reg_brain.ps1
echo } >> reg_brain.ps1
echo if ($url) { >> reg_brain.ps1
echo     echo "[+] URL Detectada: $url"; >> reg_brain.ps1
echo     echo "[+] Registrando en Render..."; >> reg_brain.ps1
echo     try { >> reg_brain.ps1
echo         $body = @{ url = $url } ^| ConvertTo-Json; >> reg_brain.ps1
echo         Invoke-RestMethod -Method Post -Uri "https://bunk3r-ia.onrender.com/api/system/register-brain" -Body $body -ContentType "application/json"; >> reg_brain.ps1
echo         echo "[OK] Tu IA local esta ahora conectada a Render!"; >> reg_brain.ps1
echo     } catch { >> reg_brain.ps1
echo         echo "[X] Error al registrar. Hazlo manualmente: $url"; >> reg_brain.ps1
echo     } >> reg_brain.ps1
echo } else { echo "[!] No se pudo capturar la URL automaticamente."; } >> reg_brain.ps1
echo while ($true) { Start-Sleep -s 60; } >> reg_brain.ps1

:: Run the PS1 script
start "BUNK3R - Brain Connector" powershell -ExecutionPolicy Bypass -File reg_brain.ps1

echo.
echo ==========================================================
echo ¡BRAIN SYNC SYSTEM ACTIVO!
echo.
echo No cierres la ventana de PowerShell que se acaba de abrir.
echo Ella mantiene el tunel y sincroniza tu IA con la nube.
echo ==========================================================
echo.
pause

