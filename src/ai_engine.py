import os
import google.generativeai as genai
import streamlit as st
import re
from src.database import get_cached_report, save_report
import json

# --- API KEY ROTATION ---
API_KEYS = []
if os.environ.get("GEMINI_API_KEY"):
    API_KEYS.append(os.environ.get("GEMINI_API_KEY"))

i = 1
while True:
    key = os.environ.get(f"GEMINI_API_KEY_{i}")
    if not key: break
    API_KEYS.append(key)
    i += 1
API_KEYS = list(set(API_KEYS))

def run_with_retry(func_generate, *args, **kwargs):
    last_error = None
    for key in API_KEYS:
        try:
            genai.configure(api_key=key)
            return func_generate(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "quota" in error_msg:
                print(f"Quota reached for key ...{key[-4:]}. Switching.")
                last_error = e
                continue
            else: raise e
    raise last_error if last_error else Exception("All API keys exhausted.")

# --- SEARCH FALLBACK (LITE) ---
@st.cache_data(show_spinner=False, ttl="24h")
def resolve_ticker_with_ai_cached(user_query):
    if len(user_query) < 3: return None
    print(f"DEBUG: Semantic search for '{user_query}'")
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        prompt = f"""
        Identify the stock ticker for this company/description: "{user_query}".
        Return ONLY the ticker symbol (e.g. AAPL, MSFT, MC.PA).
        If it is a French company, append .PA.
        If unknown, return NULL.
        """
        resp = run_with_retry(model.generate_content, prompt)
        clean_ticker = re.sub(r'[^A-Z0-9\.]', '', resp.text.strip().upper())
        if len(clean_ticker) > 1 and clean_ticker != "NULL": return clean_ticker
        return None
    except Exception as e:
        print(f"AI Search Error: {e}")
        if "429" in str(e): return "ERROR_QUOTA"
        return None

# --- FRENCH PROFILE (LITE) ---
@st.cache_data(show_spinner=False, ttl="7d")
def get_company_profile_french(ticker, name):
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        
        # Nouveau Prompt Structuré "Value Investing"
        prompt = f"""
        Analyse l'entreprise {name} ({ticker}) pour un investisseur fondamental.
        Rédige une synthèse en Français structurée exactement comme suit (utilise le Markdown gras) :
        
        **1. Business Model :** Comment l'entreprise génère son chiffre d'affaires (segments clés).
        **2. Moat (Avantage Concurrentiel) :** Pourquoi est-elle difficile à concurrencer (Marque, Coût, Effet de réseau, Switch cost) ?
        **3. Risques Majeurs :** Les 2 ou 3 plus grandes menaces actuelles.

        Contraintes :
        - Reste concis (maximum 3-4 phrases par point).
        - Ton factuel et professionnel.
        - Pas d'introduction ni de conclusion, juste les 3 points.
        """
        
        resp = run_with_retry(model.generate_content, prompt)
        return resp.text.strip()
    except: return None

# --- FULL ANALYSIS (FLASH) ---
def generate_ai_insight(ticker, name, df):
    AI_MODEL_VERSION = 'models/gemini-flash-latest'
    
    # Check Cache via src.database
    cached = get_cached_report(ticker)
    if cached:
        st.success("Report loaded from memory (0 Token used) 💾")
        return cached

    # Load Prompt
    try:
        with open('prompt.txt', "r", encoding="utf-8") as f: template = f.read()
        cols_to_analyze = ['Revenue', 'Net_Income', 'Revenue_Growth_YoY', 'Net_Margin', 'ROE', 'ROCE', 'Total_Debt', 'FCF']
        valid_cols = [c for c in cols_to_analyze if c in df.columns]
        data_str = df[valid_cols].tail(5).to_csv()
        prompt = template.format(name=name, ticker=ticker, data_str=data_str)
    except: return "Critical Error: Prompt file missing."

    # Generate
    try:
        model = genai.GenerativeModel(AI_MODEL_VERSION)
        resp = run_with_retry(model.generate_content, prompt)
        if resp.text:
            save_report(ticker, resp.text, AI_MODEL_VERSION, prompt)
            return resp.text
    except Exception as e:
        return f"Analysis Error: {e}"
    return "Empty response."
    
# --- REVENUE SPLIT (JSON GENERATION) ---
@st.cache_data(show_spinner=False, ttl="30d")
def get_revenue_split_ai(ticker, name):
    """
    Asks Gemini for the revenue breakdown and returns a Python list of dicts.
    Format: [{'label': 'iPhone', 'value': 52}, {'label': 'Services', 'value': 22}, ...]
    """
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        
        prompt = f"""
        Estimate the revenue breakdown by segment for {name} ({ticker}) for the last fiscal year.
        Return ONLY a raw JSON array. Do not use Markdown blocks (```json).
        Format example:
        [
            {{"label": "Segment A", "value": 40}},
            {{"label": "Segment B", "value": 35}},
            {{"label": "Other", "value": 25}}
        ]
        """
        
        resp = run_with_retry(model.generate_content, prompt)
        text_resp = resp.text.strip()
        
        # Cleanup: Remove markdown code blocks if Gemini puts them despite instructions
        text_resp = text_resp.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(text_resp)
        return data
    except Exception as e:
        print(f"Revenue Split Error: {e}")
        return None
        
        
import os
import google.generativeai as genai

# ... (gardez vos autres fonctions existantes) ...

def analyze_earnings_sentiment(ticker, raw_text):
    """
    Analyse le sentiment via Google Gemini avec Rotation de Clés (Failover).
    """
    # 1. RECUPERATION DYNAMIQUE DES CLES
    # On cherche toutes les variables d'env qui commencent par GEMINI_API_KEY_
    api_keys = []
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            api_keys.append(key)
            i += 1
        else:
            # On s'arrête dès qu'on ne trouve plus de clé (ex: pas de _5)
            break
    
    if not api_keys:
        return "⚠️ **Erreur Config :** Aucune clé `GEMINI_API_KEY_x` trouvée dans le fichier .env"

    # 2. BOUCLE DE TENTATIVES (KEY ROTATION)
    last_error = ""
    
    for index, api_key in enumerate(api_keys):
        try:
            # On configure avec la clé actuelle
            genai.configure(api_key=api_key)
            
            # Modèle demandé
            model = genai.GenerativeModel('gemini-2.5-flash') 

            # Prompt
            text_sample = raw_text[:30000]
            prompt = f"""
            Tu es un analyste financier expert senior chez BlackRock. 
            Agis comme un "Bullshit Detector". Ton style est direct, critique et factuel.

            Analyse cette transcription (ou news) concernant l'entreprise {ticker}.
            
            TEXTE A ANALYSER :
            "{text_sample}..."
            
            Tâche : Produis un rapport d'analyse comportementale et stratégique au format Markdown.
            
            STRUCTURE REQUISE :
            ### 🎭 Psychologie & Ton
            * **Score de Confiance (0-10) :** [Note basée sur la clarté et l'assurance des propos]
            * **Ton Général :** [ex: Défensif, Visionnaire, Prudent, Euphorique...]
            * **Analyse Sémantique :** [Quels mots reviennent ? Sont-ils vagues (headwinds) ou précis ?]
            
            ### ⚠️ Risques Dissimulés (Red Flags)
            * [Identifie 2-3 risques que le management tente de minimiser]
            * [Lis entre les lignes : Problèmes de demande ? Marges sous pression ?]
            
            ### 🎤 Analyse Q&A (Si applicable)
            * [Comment répondent-ils aux questions difficiles des analystes ?]
            
            ### 💎 Conclusion Value
            * [Est-ce que le management semble aligné avec les actionnaires ? Est-ce une opportunité ou un piège ?]
            """

            # Génération
            response = model.generate_content(prompt)
            
            # Si on arrive ici, c'est que ça a marché !
            # (Optionnel : On pourrait logger quelle clé a fonctionné)
            # print(f"Succès avec la clé n°{index+1}")
            return response.text

        except Exception as e:
            error_str = str(e)
            # On détecte les erreurs de Quota (429 ou ResourceExhausted)
            if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                print(f"⚠️ Clé n°{index+1} épuisée. Bascule vers la clé suivante...")
                last_error = error_str
                continue # On passe à l'itération suivante de la boucle for (clé suivante)
            else:
                # Si c'est une autre erreur (ex: bug de code), on arrête tout de suite
                return f"❌ Erreur technique Gemini (Clé {index+1}) : {error_str}"

    # Si on sort de la boucle, c'est que TOUTES les clés sont épuisées
    return f"❌ **Service Indisponible :** Toutes les clés API ({len(api_keys)}) ont atteint leur quota journalier.\nDernière erreur : {last_error}"    """
    Analyse le sentiment via Google Gemini.
    """
    # 1. CONFIGURATION API (Mettez votre clé Google AI Studio ici)
    # Récupérez votre clé ici : https://aistudio.google.com/app/apikey
    api_key = "AIzaSy...VOTRE_CLE_GOOGLE_ICI" 
    
    if "VOTRE_CLE" in api_key:
        return "⚠️ **Erreur :** Veuillez coller votre clé API Google dans `src/ai_engine.py`."

    try:
        genai.configure(api_key=api_key)
        
        # 2. INITIALISATION DU MODELE
        # Vous avez demandé 'gemini-2.5-flash-lite'. 
        # Si cela ne fonctionne pas, remplacez par 'gemini-1.5-flash' (le standard actuel).
        model_name = 'gemini-2.5-flash' # Je mets le 1.5 par sécurité, changez le si vous avez accès au 2.5
        model = genai.GenerativeModel(model_name)

        # 3. PREPARATION DU PROMPT
        # Gemini gère très bien les très longs textes, on peut lui donner plus de contexte.
        text_sample = raw_text[:30000] # On peut aller plus loin avec Gemini Flash
        
        prompt = f"""
        Tu es un analyste financier expert senior chez BlackRock. 
        Agis comme un "Bullshit Detector". Ton style est direct, critique et factuel.

        Analyse cette transcription (ou news) concernant l'entreprise {ticker}.
        
        TEXTE A ANALYSER :
        "{text_sample}..."
        
        Tâche : Produis un rapport d'analyse comportementale et stratégique au format Markdown.
        
        STRUCTURE REQUISE :
        ### 🎭 Psychologie & Ton
        * **Score de Confiance (0-10) :** [Note basée sur la clarté et l'assurance des propos]
        * **Ton Général :** [ex: Défensif, Visionnaire, Prudent, Euphorique...]
        * **Analyse Sémantique :** [Quels mots reviennent ? Sont-ils vagues (headwinds) ou précis ?]
        
        ### ⚠️ Risques Dissimulés (Red Flags)
        * [Identifie 2-3 risques que le management tente de minimiser]
        * [Lis entre les lignes : Problèmes de demande ? Marges sous pression ? Stocks qui montent ?]
        
        ### 🎤 Analyse Q&A (Si applicable)
        * [Comment répondent-ils aux questions difficiles des analystes ? Ont-ils esquivé ?]
        
        ### 💎 Conclusion Value
        * [Est-ce que le management semble aligné avec les actionnaires ? Est-ce une opportunité ou un piège ?]
        """

        # 4. GENERATION
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        return f"Erreur lors de l'appel Gemini : {str(e)}"
        
        
def generate_custom_analysis(final_prompt):
    """
    Envoie un prompt à Google Gemini et retourne la réponse + métadonnées.
    """
    # 1. RECUPERATION DYNAMIQUE DES CLES
    api_keys = []
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            api_keys.append(key)
            i += 1
        else:
            break
    
    if not api_keys:
        return {"error": "⚠️ **Erreur Config :** Aucune clé `GEMINI_API_KEY_x` trouvée."}

    last_error = ""
    model_name = 'gemini-2.5-flash' # Le modèle utilisé

    # 2. BOUCLE DE TENTATIVES
    for index, api_key in enumerate(api_keys):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # Appel API
            response = model.generate_content(final_prompt)
            
            # Récupération des métriques de tokens
            # (Google renvoie usage_metadata)
            usage = response.usage_metadata
            tokens_input = usage.prompt_token_count
            tokens_output = usage.candidates_token_count
            total_tokens = usage.total_token_count
            
            # On retourne un DICTIONNAIRE riche
            return {
                "success": True,
                "content": response.text,
                "model_used": model_name,
                "key_index": index + 1, # Pour savoir que c'est la clé 1, 2, ou 3...
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "tokens_total": total_tokens
            }

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                print(f"⚠️ Clé n°{index+1} épuisée. Bascule...")
                last_error = error_str
                continue 
            else:
                return {"success": False, "error": f"❌ Erreur technique Gemini (Clé {index+1}) : {error_str}"}

    return {"success": False, "error": f"❌ **Service Indisponible :** Toutes les clés épuisées.\nDernière erreur : {last_error}"}