import os
from sqlalchemy import create_engine, text
import datetime

# Récupération sécurisée de l'URL
DB_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DB_URL) if DB_URL else None

def init_db():
    """Initialise les tables nécessaires dans PostgreSQL."""
    if not engine:
        print("⚠️ Pas de connexion Database définie.")
        return

    with engine.connect() as conn:
        # Table des Rapports IA
        # On utilise IF NOT EXISTS pour ne pas créer d'erreur si elle existe déjà
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_reports (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ticker TEXT,
                company_name TEXT,
                prompt_used TEXT,
                model_version TEXT,
                report_content TEXT
            );
        """))
        conn.commit()
        print("✅ Base de données initialisée (Table ai_reports prête).")

# --- FONCTION UTILISÉE PAR MAIN.PY (Full Report) ---
def save_ai_report(ticker, name, prompt, model, content):
    """Sauvegarde un rapport complet généré en base."""
    if not engine: return False
    
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO ai_reports (ticker, company_name, prompt_used, model_version, report_content)
                VALUES (:tick, :name, :p, :m, :c)
            """)
            conn.execute(query, {
                "tick": ticker, 
                "name": name, 
                "p": prompt, 
                "m": model, 
                "c": content
            })
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Erreur sauvegarde DB : {e}")
        return False

# --- FONCTIONS REQUISES PAR AI_ENGINE.PY (Pour corriger l'erreur d'import) ---

def get_cached_report(ticker):
    """
    Récupère le dernier rapport IA existant pour un ticker donné.
    Utilisé par ai_engine pour éviter de régénérer inutilement.
    """
    if not engine: return None
    
    try:
        with engine.connect() as conn:
            # On cherche le rapport le plus récent
            query = text("""
                SELECT report_content 
                FROM ai_reports 
                WHERE ticker = :tick 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            result = conn.execute(query, {"tick": ticker}).fetchone()
            
            if result:
                return result[0] # Retourne le texte du rapport
            return None
    except Exception as e:
        print(f"⚠️ Erreur lecture cache DB : {e}")
        return None

def save_report(ticker, content):
    """
    Version simplifiée de sauvegarde requise par ai_engine.py.
    Redirige vers save_ai_report avec des valeurs par défaut.
    """
    # On met des valeurs par défaut pour les champs manquants
    return save_ai_report(
        ticker=ticker,
        name=ticker, # On utilise le ticker comme nom par défaut
        prompt="Auto-generated via Cache Logic",
        model="Unknown",
        content=content
    )