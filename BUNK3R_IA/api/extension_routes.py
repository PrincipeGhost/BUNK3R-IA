from flask import Blueprint, request, jsonify
from BUNK3R_IA.core.context_manager import ContextManager
import time

extension_bp = Blueprint('extension', __name__, url_prefix='/api/extension')

@extension_bp.route('/telemetry', methods=['POST'])
def receive_telemetry():
    """Receives console logs, network errors, etc. from browser"""
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400
    
    # Store in active context for AI to "see"
    # We use a special key "telemetry_stream"
    ContextManager.add_memory_item(
        "telemetry_stream", 
        {
            "timestamp": time.time(),
            "type": data.get("type", "log"),
            "content": data
        }
    )
    
    # Optional: Log specific errors to server console for dev visibility
    if data.get("type") == "error":
        print(f"[BROWSER-ERROR] {data.get('message', 'Unknown')}")
        
    return jsonify({"success": True})

@extension_bp.route('/context-menu', methods=['POST'])
def handle_context_menu():
    """Handles 'Ask BUNK3R' requests from right-click"""
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400
        
    # Store the element context as a "focus" item
    ContextManager.set_focus_item({
        "type": "dom_element",
        "html": data.get("html"),
        "text": data.get("text"),
        "page_url": data.get("url"),
        "timestamp": time.time()
    })
    
    print(f"[EXTENSION] Received context focus from {data.get('url')}")
    
    # We could trigger a WebSocket event here to open the chat
    # For now, storing it in context is enough; the next chat message will see it.
    
    return jsonify({"success": True, "action": "focus_set"})

@extension_bp.route('/poll', methods=['GET'])
def poll_commands():
    """Extension polls this to see if AI wants to do anything (click, scroll)"""
    # In a real implementation, this would pop commands from a queue
    # For now, return empty or mock
    commands = [] 
    # Logic to fetch pending commands for this user/session
    return jsonify({"commands": commands})

@extension_bp.route('/event', methods=['POST'])
def receive_event():
    """Generic event receiver (clicks, etc)"""
    data = request.json
    # Store generic events
    return jsonify({"success": True})
