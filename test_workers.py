import time
import sys
import os

# Ajustar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from BUNK3R_IA.core.workers import queue_manager, worker_engine

def test_workers():
    print("--- INICIANDO TEST DE WORKERS ---")
    
    # 1. Iniciar el engine
    worker_engine.start()
    
    # 2. Encolar una tarea de prueba
    print("Encolando tarea 'test_task'...")
    task_id = queue_manager.enqueue_task(
        task_type='test_task',
        payload={'data': 'Prueba 123'},
        user_id='tester_001'
    )
    print(f"Tarea encolada con ID: {task_id}")
    
    # 3. Esperar procesamiento (Polling)
    print("Esperando procesamiento...")
    for _ in range(10):
        conn = queue_manager.db._get_connection(queue_manager.db.central_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status, result FROM task_queue WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        
        # Ahora que row_factory está forzado a sqlite3.Row, podemos usar acceso por nombre
        if row:
            status = row['status']
            print(f"Estado actual: {status}")
            
            if status == 'completed':
                result_json = row['result'] 
                print(f"✅ Tarea completada! Resultado: {result_json}")
                break
            elif status == 'failed':
                print(f"❌ Tarea falló: {row['error_message']}")
                break
        else:
             print("Esperando... (No row)")
            
        time.sleep(1)
        
    # 4. Detener engine
    worker_engine.stop()
    print("--- TEST FINALIZADO ---")

if __name__ == "__main__":
    test_workers()
