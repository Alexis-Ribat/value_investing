import subprocess
import json
import os
import platform

def get_sec_data_rust(ticker):
    """
    Appelle le binaire Rust 'edgar_fetcher' pour récupérer les données SEC.
    Compatible avec Docker (Linux) et le développement local (Windows).
    """
    # 1. Détection intelligente du binaire Rust
    binary_name = "edgar_fetcher"
    
    if platform.system() == "Windows":
        # En dev local Windows, on cherche souvent dans target/release
        binary_path = os.path.join("rust_engine", "target", "release", f"{binary_name}.exe")
        # Fallback si on ne le trouve pas compilé
        if not os.path.exists(binary_path):
             # Optionnel : Retourner None ou mocker si on n'a pas Rust installé en local
             print(f"⚠️ Binaire Rust non trouvé en local : {binary_path}")
             return None
    else:
        # Chemin défini dans votre Dockerfile
        binary_path = f"/usr/local/bin/{binary_name}"

    # 2. Exécution du moteur Rust
    try:
        # On appelle l'exécutable avec le ticker comme argument
        result = subprocess.run(
            [binary_path, ticker], 
            capture_output=True, 
            text=True,     # Pour récupérer des strings directements
            check=True     # Lève une erreur si le code de retour != 0
        )
        
        # 3. Parsing de la réponse JSON du moteur Rust
        output_str = result.stdout.strip()
        if not output_str:
            return None
            
        return json.loads(output_str)

    except FileNotFoundError:
        # Cas où le binaire n'est pas compilé ou pas présent
        print(f"❌ Erreur : L'exécutable '{binary_path}' est introuvable.")
        return None
        
    except subprocess.CalledProcessError as e:
        # Le moteur Rust a renvoyé une erreur (ex: Ticker introuvable)
        print(f"⚠️ Erreur du moteur Rust pour {ticker} : {e.stderr}")
        return None
        
    except json.JSONDecodeError:
        print(f"❌ Erreur : Le moteur Rust n'a pas renvoyé un JSON valide.")
        return None