# Guía para URL Persistente de BUNK3R-IA

Para que tu local AI siempre tenga la misma URL y no tengas que cambiarla en Render cada vez, sigue estos pasos:

## 1. Login en Cloudflare
Abre una terminal (CMD o PowerShell) y escribe:
```bash
cloudflared tunnel login
```
Se abrirá tu navegador. Selecciona un dominio si tienes uno, o simplemente autoriza el acceso.

## 2. Crear un Túnel Nombrado
Crea un túnel llamado `bunk3r-brain`:
```bash
cloudflared tunnel create bunk3r-brain
```
Esto generará un archivo JSON de credenciales y un **ID de Túnel**. Cópialo.

## 3. Configurar el nombre persistente (Si tienes dominio)
Si tienes un dominio en Cloudflare (ej: `tudominio.com`), ejecuta:
```bash
cloudflared tunnel route dns bunk3r-brain brain.tudominio.com
```

## 4. Usar el ID del Túnel (Si NO tienes dominio)
Si no tienes dominio, Cloudflare no ofrece URLs fijas gratuitas de tipo `trycloudflare.com` que sean permanentes. Sin embargo, tener el túnel creado facilita el proceso.

## 5. Actualizar BUNK3R_START_LOCAL_IA.bat
Una vez tengas tu túnel creado, el archivo `.bat` se puede configurar para usarlo.

> [!IMPORTANT]
> Si no tienes un dominio propio, la URL de `trycloudflare.com` siempre será aleatoria por diseño de Cloudflare. Para una URL 100% fija, se recomienda usar un dominio gratuito (como `.pp.ua` o similares) o uno barato y vincularlo a Cloudflare.
