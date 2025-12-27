$url = ""; 
$proc = Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:11434" -PassThru -NoNewWindow -RedirectStandardError "tunnel_log.txt"; 
echo "Esperando a que Cloudflare genere la URL (max 20s)..."; 
$timeout = Get-Date; $timeout = $timeout.AddSeconds(20); 
while ($(Get-Date) -lt $timeout) { 
    if (Test-Path "tunnel_log.txt") { 
        $content = Get-Content "tunnel_log.txt" -Raw; 
        if ($content -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") { 
            $url = $matches[0]; 
            if ($url) { break; } 
        } 
    } 
    Start-Sleep -s 1; 
} 
if ($url) { 
    echo "[+] URL Detectada: $url"; 
    echo "[+] Registrando en Render..."; 
    try { 
        $body = @{ url = $url } | ConvertTo-Json; 
        Invoke-RestMethod -Method Post -Uri "https://bunk3r-ia.onrender.com/api/system/register-brain" -Body $body -ContentType "application/json"; 
        echo "[OK] Tu IA local esta ahora conectada a Render"; 
    } catch { 
        echo "[X] Error al registrar. Hazlo manualmente: $url"; 
    } 
} else { echo "[] No se pudo capturar la URL automaticamente."; } 
while ($true) { Start-Sleep -s 60; } 
