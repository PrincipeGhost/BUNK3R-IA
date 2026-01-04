import time
import json
import logging
import threading
import traceback
import asyncio
from typing import Dict, Any, Callable
from core.workers.queue_manager import queue_manager

# Imports de handlers
from core.automation import GithubBot, RenderBot

logger = logging.getLogger(__name__)

class WorkerEngine:
    """
    Motor principal de Workers.
    """
    
    def __init__(self):
        self.running = False
        self.handlers: Dict[str, Callable] = {}
        self.worker_thread = None
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Registra los handlers por defecto del sistema"""
        self.register_handler('create_github_repo', self.handle_create_repo)
        self.register_handler('deploy_render', self.handle_deploy_render)
        self.register_handler('test_task', self.handle_test_task)

    def register_handler(self, task_type: str, handler_func: Callable):
        self.handlers[task_type] = handler_func
        logger.info(f"Handler registered: {task_type}")

    def start(self):
        if self.running: return
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Worker Engine started 🚀")

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Worker Engine stopped")

    def _worker_loop(self):
        # Crear loop de eventos para ejecución asíncrona en este hilo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            try:
                task = queue_manager.fetch_next_task()
                if task:
                    # Ejecutar procesamiento síncrono o asíncrono
                    loop.run_until_complete(self._process_task_async(task))
                else:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)
        loop.close()

    async def _process_task_async(self, task: Dict[str, Any]):
        task_id = task['task_id']
        task_type = task['task_type']
        
        logger.info(f"Processing task {task_id} ({task_type})...")
        handler = self.handlers.get(task_type)
        
        if not handler:
            queue_manager.update_task_status(task_id, 'failed', error=f"No handler for {task_type}")
            return

        try:
            payload = json.loads(task['payload'])
            user_id = task['user_id']
            
            # Chequear si handler es corrutinas
            if asyncio.iscoroutinefunction(handler):
                result = await handler(payload, user_id)
            else:
                result = handler(payload, user_id)
            
            queue_manager.update_task_status(task_id, 'completed', result=result)
            logger.info(f"Task {task_id} completed ✅")
            
        except Exception as e:
            error_msg = str(e)
            trace = traceback.format_exc()
            logger.error(f"Task {task_id} failed: {error_msg}")
            queue_manager.update_task_status(task_id, 'failed', error=error_msg)

    # --- HANDLERS ---

    def handle_test_task(self, payload, user_id):
        time.sleep(1)
        return {"msg": "Test OK"}

    async def handle_create_repo(self, payload, user_id):
        """Handler para crear repo en GitHub"""
        repo_name = payload.get('repo_name')
        token = payload.get('github_token') # En prod, sacar de BD encriptada
        
        bot = GithubBot(token=token, headless=True)
        await bot.start()
        try:
            url = await bot.create_repo(repo_name, private=True)
            return {"repo_url": url}
        finally:
            await bot.stop()

    async def handle_deploy_render(self, payload, user_id):
        """Handler para deploy en Render"""
        email = payload.get('email')
        password = payload.get('password')
        repo_url = payload.get('repo_url')
        service_name = payload.get('service_name')
        
        bot = RenderBot(headless=True)
        await bot.start()
        try:
            if email and password:
                await bot.login(email, password)
            
            # En un flujo real, guardaríamos cookies para no loguear cada vez
            service_url = await bot.create_web_service(repo_url, service_name)
            return {"service_url": service_url}
        finally:
            await bot.stop()

worker_engine = WorkerEngine()
