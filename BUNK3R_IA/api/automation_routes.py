"""
Automation Routes - API endpoints for browser extension
Handles CRUD operations for web automations
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import sqlite3
import os

automation_bp = Blueprint('automation', __name__)

# Database path (will be in user's database)
def get_db_path(user_id):
    """Get path to user's database"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_dir = os.path.join(base_dir, 'databases', 'users')
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, f'user_{user_id}.db')

def init_automations_table(user_id):
    """Initialize automations table in user database"""
    db_path = get_db_path(user_id)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS automations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            actions TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            execution_count INTEGER DEFAULT 0,
            last_executed TEXT,
            tags TEXT,
            category TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

@automation_bp.route('/api/automations', methods=['GET'])
def get_automations():
    """Get all automations for current user"""
    try:
        # TODO: Get user_id from session/auth
        user_id = request.headers.get('X-User-ID', 'demo_user')
        
        init_automations_table(user_id)
        db_path = get_db_path(user_id)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM automations 
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        automations = []
        
        for row in rows:
            automations.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'actions': json.loads(row['actions']),
                'enabled': bool(row['enabled']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'execution_count': row['execution_count'],
                'last_executed': row['last_executed'],
                'tags': json.loads(row['tags']) if row['tags'] else [],
                'category': row['category']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'automations': automations,
            'count': len(automations)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/automations/<automation_id>', methods=['GET'])
def get_automation(automation_id):
    """Get single automation by ID"""
    try:
        user_id = request.headers.get('X-User-ID', 'demo_user')
        
        db_path = get_db_path(user_id)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM automations WHERE id = ?', (automation_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'error': 'Automation not found'
            }), 404
        
        automation = {
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'actions': json.loads(row['actions']),
            'enabled': bool(row['enabled']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'execution_count': row['execution_count'],
            'last_executed': row['last_executed'],
            'tags': json.loads(row['tags']) if row['tags'] else [],
            'category': row['category']
        }
        
        return jsonify({
            'success': True,
            'automation': automation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/automations', methods=['POST'])
def create_automation():
    """Create new automation"""
    try:
        user_id = request.headers.get('X-User-ID', 'demo_user')
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('actions'):
            return jsonify({
                'success': False,
                'error': 'Name and actions are required'
            }), 400
        
        init_automations_table(user_id)
        db_path = get_db_path(user_id)
        
        automation_id = data.get('id', f"auto-{datetime.now().timestamp()}")
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO automations 
            (id, name, description, actions, enabled, created_at, tags, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            automation_id,
            data['name'],
            data.get('description', ''),
            json.dumps(data['actions']),
            1 if data.get('enabled', True) else 0,
            now,
            json.dumps(data.get('tags', [])),
            data.get('category', 'general')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'automation': {
                'id': automation_id,
                'name': data['name'],
                'created_at': now
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/automations/<automation_id>', methods=['PUT'])
def update_automation(automation_id):
    """Update existing automation"""
    try:
        user_id = request.headers.get('X-User-ID', 'demo_user')
        data = request.get_json()
        
        db_path = get_db_path(user_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE automations 
            SET name = ?, description = ?, actions = ?, 
                enabled = ?, updated_at = ?, tags = ?, category = ?
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('description', ''),
            json.dumps(data.get('actions', [])),
            1 if data.get('enabled', True) else 0,
            now,
            json.dumps(data.get('tags', [])),
            data.get('category', 'general'),
            automation_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'automation': {
                'id': automation_id,
                'updated_at': now
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/automations/<automation_id>', methods=['DELETE'])
def delete_automation(automation_id):
    """Delete automation"""
    try:
        user_id = request.headers.get('X-User-ID', 'demo_user')
        
        db_path = get_db_path(user_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM automations WHERE id = ?', (automation_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Automation deleted'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/automations/<automation_id>/execute', methods=['POST'])
def execute_automation(automation_id):
    """Log automation execution"""
    try:
        user_id = request.headers.get('X-User-ID', 'demo_user')
        
        db_path = get_db_path(user_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE automations 
            SET execution_count = execution_count + 1,
                last_executed = ?
            WHERE id = ?
        ''', (now, automation_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'executed_at': now
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/automations/generate', methods=['POST'])
def generate_automation():
    """Generate automation using AI"""
    try:
        from BUNK3R_IA.core.ai_service import get_ai_service
        
        data = request.get_json()
        description = data.get('description', '')
        page_context = data.get('page_context', {})
        
        if not description:
            return jsonify({
                'success': False,
                'error': 'Description is required'
            }), 400
        
        # Build prompt for AI
        prompt = f"""
Genera una automatización web basada en esta descripción:
"{description}"

Contexto de la página:
URL: {page_context.get('url', 'N/A')}
Título: {page_context.get('title', 'N/A')}

Responde SOLO con un JSON válido en este formato:
{{
  "name": "Nombre descriptivo",
  "description": "Descripción detallada",
  "actions": [
    {{"type": "click", "selector": "#button"}},
    {{"type": "fill", "selector": "#input", "value": "texto"}},
    {{"type": "wait", "duration": 1000}}
  ],
  "category": "productividad"
}}

Tipos de acciones disponibles: click, fill, select, wait, extract, navigate, scroll
"""
        
        # Get AI service (simplified - you'll need proper initialization)
        # ai_service = get_ai_service(None)
        # response = ai_service.chat('system', prompt)
        
        # For now, return a template
        automation = {
            "name": f"Automatización: {description[:50]}",
            "description": description,
            "actions": [
                {"type": "wait", "duration": 1000}
            ],
            "category": "generated"
        }
        
        return jsonify({
            'success': True,
            'automation': automation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/api/automations/stats', methods=['GET'])
def get_stats():
    """Get automation statistics"""
    try:
        user_id = request.headers.get('X-User-ID', 'demo_user')
        
        db_path = get_db_path(user_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM automations')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as enabled FROM automations WHERE enabled = 1')
        enabled = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(execution_count) as executions FROM automations')
        executions = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'enabled': enabled,
                'executions': executions
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
