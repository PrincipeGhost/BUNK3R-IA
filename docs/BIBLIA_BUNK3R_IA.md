# 📖 BIBLIA MAESTRA: BUNK3R-IA (Manual de Ejecución)

Este documento es la única fuente de verdad para el desarrollo de BUNK3R-IA. Detalla el **qué**, el **cómo** y el **por qué** de cada componente para que el sistema sea 100% autónomo y seguro.

---

## 🏗️ 1. FILOSOFÍA Y POR QUÉ LO HACEMOS

### **¿Por qué este diseño?**
1.  **Aislamiento Radical:** En la BD Central NO existe información sensible (contraseñas, credenciales). Si la BD Central es vulnerada, el atacante no obtiene acceso a los datos de los usuarios.
2.  **Automatización "Ghost":** Usamos Playwright para imitar el comportamiento humano. Esto permite crear cuentas gratuitas y gestionar servicios en Render/GitHub sin depender de cuotas de API limitadas.
3.  **Escalabilidad Silenciosa:** Todo lo pesado ocurre fuera del proceso web (en Workers). El usuario siente una web rápida mientras en el fondo la IA automatiza todo.

---

## 🛠️ 2. EL "CÓMO" TÉCNICO (Módulos Críticos)

### 🤖 **Automatización Integrada (Playwright & APIs)**
- **GitHub:** Automatizar la creación de repositorios y el `git push` del código generado.
- **Bases de Datos (Auto-provisioning):**
    - **Neon.tech / Render DB:** La IA decidirá y ejecutará la creación de la base de datos (PostgreSQL) de forma automática.
- **Render (PaaS):** Registro de cuentas Render y conexión automática de GitHub -> Render -> Neon.
- **Variables de Entorno (.env):** Inyección automática de `DATABASE_URL` y otras claves en los servicios desplegados. Manejo seguro de archivos `.env` locales en el espacio del proyecto.

### 🐙 **Integración GitHub Real (Opcional)**
- **Auth:** Soporte para Personal Access Tokens (PAT) almacenados cifrados en la 'Bóveda de Secretos'.
- **Capacidades:**
    - Listar repositorios privados/públicos del usuario.
    - Clonar proyectos existentes al workspace de BUNK3R-IA.
    - Crear nuevos repos desde la interfaz de BUNK3R-IA usando la cuenta real del usuario (sin Ghost Mode).

### � **Gestión de Secretos (.env & Session Secrets)**
- **Almacenamiento Seguro:** Los archivos `.env` de cada proyecto se almacenan cifrados o en una bóveda segura dentro del espacio del usuario.
- **Sección 'Secrets':** Parte dedicada en la UI donde el usuario puede gestionar sus claves API, secretos de sesión y variables de entorno sin exponerlas en el código fuente.
- **Inyección:** Al desplegar o ejecutar (F12), estas variables se inyectan dinámicamente en el proceso, nunca se escriben en plano en el disco si es evitable.

### �🖥️ **Consolas y Comunicación en Tiempo Real**
- **Consola Render (Logs):** Captura de logs de Build y Runtime para auditoría de la IA y visualización del usuario.
- **Consola F12 (Backend):** Ejecución de comandos (`npm start`, `python app.py`) dentro de contenedores **Docker** para aislamiento total, capturando `stdout/stderr`.
- **WebSockets:** Uso de Socket.io para actualización instantánea de logs y estados sin refrescar la página.

### ⚙️ **Arquitectura de Workers & Multi-Tenancy**
- **Workers:** Procesos en segundo plano que gestionan las colas de tareas pesadas.
- **3 Niveles de BD:** 
    1. **Central:** Solo un índice de usuarios.
    2. **Usuario:** Credenciales de despliegue y listado de proyectos.
    3. **Proyecto:** Datos operativos de la App final. No hay mezcla de datos.

### 🛡️ **Seguridad y Aislamiento**
- **Privilegios Mínimos:** Workers con permisos restringidos.
- **Cifrado:** Credenciales en la BD del Usuario cifradas en reposo.
- **Restricción F12:** Ejecución limitada a comandos pre-aprobados para evitar fugas del contenedor.

---

## 🖼️ 3. EXPERIENCIA DEL USUARIO (Frontend)

Lo que el usuario verá en el tablero:
- **Dashboard de Proyectos:** Estados visuales (⏳ Creando, 🚀 Desplegando, ✅ Listo).
- **Conexión GitHub:** Panel para vincular cuenta y ver lista de repositorios remotos ("Importar desde GitHub").
- **Explorador de Archivos (Repo View):** Transformación de la sección "Archivos" en un IDE/Explorador completo. El usuario podrá navegar por todas las carpetas y archivos del proyecto generado, ver su código en tiempo real y entender la estructura del repositorio.
- **Gestor de Secretos (Vault):** Área protegida ('Session Secrets') para ver y editar el archivo `.env` del proyecto de forma gráfica y segura.
- **Consola de Trabajo:** Interfaz interactiva para ver el progreso de la IA y ejecutar comandos de backend.
- **Seguridad UI:** El usuario nunca ve contraseñas ni URLs internas de infraestructura.

---

## 🚀 4. HOJA DE RUTA (Cronograma de Ejecución)

### ✅ **Fase 1: El Cimiento (DATOS)**
*   **Estado:** Completado.
*   **Logro:** Estructura de `central.db` e implementación del `manager.py`.
*   **Verificado:** Sí, aislamiento de rutas confirmado.

### ✅ **Fase 2: El Cerebro (WORKERS & INFRAESTRUCTURA)**
*   **Estado:** Completado (Infraestructura Base).
*   **Logro:** Implementación de `queue_manager.py` (Cola SQLite) y `engine.py` (Procesador asíncrono).
*   **Verificado:** Sí, script `test_workers.py` confirmó ciclo completo de encolado y procesamiento.

### ✅ **Fase 3: El Brazo (AUTOMATIZACIÓN TOTAL)**
*   **Estado:** Completado (Bots Implementados).
*   **Logro:** Creación de `github_bot.py` y `render_bot.py` con soporte Playwright. Actualización del Engine a AsyncIO.
*   **Verificado:** Integración de handlers asíncronos verificada con `test_workers.py`.

### ✅ **Fase 4: El Rostro (UI DINÁMICA)**
*   **Estado:** Completado (Dashboard & Sidebar).
*   **Logro:** Implementación de Activity Bar, lista de proyectos y endpoint de API (`project_routes.py`).
*   **Extra:** Integración completa con GitHub (API + UI) para gestión de repositorios reales.
*   **Verificado:** Código inyectado en `workspace.html` con lógica JS para SPA.

### ⏳ **Fase 5: El Cerebro Superior (SISTEMA DE CONSOLAS)**
*   **Misión:** Implementación de Docker + Consola Interactiva.

---

## 🤖 5. REGLAS PARA EL AGENTE DE IA (Protocolo Obligatorio)

1.  **Actualización Constante:** Este archivo DEBE actualizarse tras finalizar cada fase.
2.  **Verificación Pre-Check:** Solo se marcará como completa una fase si se han realizado tests de funcionamiento.
3.  **Aislamiento de Código:** No editar archivos fuera de `BUNK3R-IA` sin permiso expreso.
4.  **Documentación Continua:** Cualquier cambio en la lógica de automatización debe ser reflejado inmediatamente en la sección **2. EL "CÓMO" TÉCNICO**.

---
*Estado Actual: Fase 4 (UI Dashboard) completada. Listo para la Fase Final (Consolas).*
