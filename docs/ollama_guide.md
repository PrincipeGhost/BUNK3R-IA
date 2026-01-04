# Guía de Ollama en Terminal para BUNK3R-IA

Para que tu IA consuma el mínimo de recursos y funcione como el "Cerebro" de BUNK3R, te recomiendo correrla exclusivamente desde la terminal.

## 1. Arrancar el Servidor (Modo Headless)

En lugar de abrir la aplicación de escritorio, abre una terminal (PowerShell o CMD) y ejecuta:

```bash
ollama serve
```

> [!TIP]
> Esto inicia el backend sin la interfaz gráfica, lo que ahorra memoria RAM significativa.

## 2. Modelos Recomendados

Para BUNK3R-IA, he configurado `llama3.2` por defecto por su equilibrio entre velocidad y razonamiento.

- **Para descargar el modelo:**
  ```bash
  ollama pull llama3.2
  ```

- **Si tu PC tiene poca RAM (8GB o menos), usa:**
  ```bash
  ollama pull phi3
  ```
  *(Luego podemos cambiar el nombre en `config.py`)*

## 3. Monitoreo de Recursos

Si quieres ver qué está haciendo Ollama mientras BUNK3R trabaja:

```bash
# Ver modelos cargados en memoria
ollama ps
```

## 4. Conectar con Render (Cloudflare Tunnel)

Como tu IA está en **Render** y Ollama está en tu **PC**, necesitas un puente (túnel) para que Render pueda "ver" tu terminal local.

1.  **En una nueva terminal ejecutada:**
    ```bash
    cloudflared tunnel --url http://localhost:11434
    ```

2.  **Copia la URL** que te dará Cloudflare (ej: `https://pretty-cloud-tunnel.trycloudflare.com`).

3.  **Configura Render**:
    Ve al panel de Render de tu `BUNK3R-IA` y añade esta variable de entorno:
    - `OLLAMA_BASE_URL` = `https://tu-url-de-cloudflare.trycloudflare.com`

---

## 5. Ventajas de la Terminal
- **Menor consumo de CPU/GPU** al no renderizar interfaz.
- **Transparencia**: Verás los logs de cada consulta en tiempo real.
- **Seguridad**: Solo tú conoces la URL del túnel.
