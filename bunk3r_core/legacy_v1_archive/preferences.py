import logging
from datetime import datetime
from bunk3r_backend.models import db, UserPreferenceModel

logger = logging.getLogger(__name__)

class PreferenceTracker:
    """
    Analiza las interacciones para aprender el estilo del usuario.
    """
    
    def learn_from_edit(self, file_path, content_snippet):
        """Detecta patrones de estilo en los cambios confirmados."""
        # Ejemplo: ¿Usa comillas simples o dobles?
        if "'" in content_snippet and '"' not in content_snippet:
            self._update_preference("quote_style", "single")
        elif '"' in content_snippet and "'" not in content_snippet:
            self._update_preference("quote_style", "double")
            
        # Ejemplo: ¿Imports en una línea o múltiples?
        if "from" in content_snippet and "(" in content_snippet:
            self._update_preference("import_style", "multiline")

    def _update_preference(self, key, value):
        try:
            pref = UserPreferenceModel.query.get(key)
            if not pref:
                pref = UserPreferenceModel(key=key, value=value, confidence=0.1)
                db.session.add(pref)
            else:
                if pref.value == value:
                    pref.confidence = min(1.0, pref.confidence + 0.1)
                else:
                    pref.confidence = max(0.0, pref.confidence - 0.2)
                    if pref.confidence < 0.2:
                        pref.value = value # Switch preference if confidence is low
            
            pref.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating preference {key}: {e}")

    def get_style_context(self):
        """Retorna un prompt con las preferencias detectadas."""
        prefs = UserPreferenceModel.query.all()
        if not prefs:
            return ""
            
        summary = "PREFERENCIAS DEL USUARIO DETECTADAS:\n"
        for p in prefs:
            if p.confidence > 0.6:
                summary += f"- {p.key}: {p.value}\n"
        return summary

preference_tracker = PreferenceTracker()
