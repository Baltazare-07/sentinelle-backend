from flask import Flask, request, jsonify
from flask_cors import CORS
from web3 import Web3
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# ---- Configuration blockchain ----
RPC_URLS = [
    "https://rpc.sepolia.org",
    "https://ethereum-sepolia.publicnode.com",
    "https://sepolia.gateway.tenderly.co",
    "https://eth-sepolia.public.blastapi.io",
]

def get_web3_connection():
    """Tente de se connecter à un des RPC Sepolia."""
    for rpc in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if w3.is_connected():
                print(f"✅ Connecté à Sepolia via {rpc}")
                return w3
        except Exception as e:
            print(f"❌ Impossible de se connecter à {rpc}: {str(e)}")
            continue
    return None

w3 = get_web3_connection()
if not w3:
    print("❌ Aucun RPC Sepolia disponible. Vérifie ta connexion internet.")

SPONSOR_PRIVATE_KEY = os.environ.get('SPONSOR_PRIVATE_KEY', '')
SPONSOR_ADDRESS = os.environ.get('SPONSOR_ADDRESS', '')
CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS', '')

# ---- Charger l'ABI du contrat ----
ABI_PATH = 'SignalementABI.json'
contract_abi = []
if os.path.exists(ABI_PATH):
    with open(ABI_PATH, 'r') as f:
        contract_abi = json.load(f)
else:
    print("⚠️ SignalementABI.json non trouvé. Vérifiez le chemin.")

# ---- Stockage local (en mémoire) ----
signalements_db = []

# ---- Routes ----
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'blockchain_connected': w3.is_connected() if w3 else False,
        'sponsor_configured': bool(SPONSOR_PRIVATE_KEY)
    })

@app.route('/api/sponsor', methods=['POST'])
def sponsor_transaction():
    """
    Reçoit les données du signalement, construit, signe et envoie la transaction
    via le compte sponsor.
    """
    try:
        data = request.json
        print("🔔 Requête reçue sur /api/sponsor")
        print("Données:", data)

        report_type = data.get('type')
        description = data.get('description')
        quartier = data.get('quartier')
        lat = data.get('lat')
        lng = data.get('lng')
        citizen_address = data.get('user_address')

        # Validations
        if not report_type or not quartier or lat is None or lng is None or not citizen_address:
            return jsonify({'error': 'Données manquantes'}), 400

        if not w3 or not w3.is_connected():
            return jsonify({'error': 'Pas de connexion à la blockchain'}), 500

        if not SPONSOR_PRIVATE_KEY or not CONTRACT_ADDRESS or not contract_abi:
            return jsonify({'error': 'Configuration blockchain incomplète'}), 500

        # Conversion des coordonnées (ex: * 10**6 pour conserver 6 décimales)
        lat_int = int(float(lat) * 10**6)
        lng_int = int(float(lng) * 10**6)

        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

        # Récupérer le nonce et le prix du gaz
        nonce = w3.eth.get_transaction_count(SPONSOR_ADDRESS, 'pending')
        gas_price = w3.eth.gas_price

        # Construire la transaction
        tx = contract.functions.createReport(
            citizen_address,
            report_type,
            description,
            quartier,
            lat_int,
            lng_int
        ).build_transaction({
            'from': SPONSOR_ADDRESS,
            'nonce': nonce,
            'gas': 500000,
            'gasPrice': gas_price
        })

        # Signer et envoyer
        tx_signed = w3.eth.account.sign_transaction(tx, SPONSOR_PRIVATE_KEY)
        tx_hash_bytes = w3.eth.send_raw_transaction(tx_signed.raw_transaction)
        # Assurer que le hash commence par 0x (et est en hexadécimal)
        if isinstance(tx_hash_bytes, bytes):
            tx_hash_hex = '0x' + tx_hash_bytes.hex()
        else:
            # Déjà une chaîne hexadécimale (anciennes versions)
            tx_hash_hex = tx_hash_bytes if tx_hash_bytes.startswith('0x') else '0x' + tx_hash_bytes

        print(f"✅ Transaction envoyée : {tx_hash_hex}")
        return jsonify({'success': True, 'tx_hash': tx_hash_hex})

    except Exception as e:
        print("❌ Erreur interne:")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/signalements', methods=['GET'])
def get_signalements():
    """Retourne la liste locale des signalements (persistance mémoire)"""
    return jsonify(signalements_db)

@app.route('/api/signalements', methods=['POST'])
def post_signalement():
    """
    Stocke un signalement localement (optionnel).
    Le frontend peut appeler cette route s'il souhaite sauvegarder.
    """
    try:
        data = request.json
        new_id = f"LOCAL-{len(signalements_db)+1:03d}"
        data['id'] = new_id
        data['created_at'] = datetime.now().isoformat()
        signalements_db.append(data)
        return jsonify({'id': new_id, 'success': True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Retourne le solde du compte sponsor"""
    try:
        if not w3 or not w3.is_connected():
            return jsonify({'address': SPONSOR_ADDRESS, 'balance_eth': '0'}), 500
        balance = w3.eth.get_balance(SPONSOR_ADDRESS)
        balance_eth = w3.from_wei(balance, 'ether')
        return jsonify({'address': SPONSOR_ADDRESS, 'balance_eth': str(balance_eth)})
    except Exception as e:
        return jsonify({'address': SPONSOR_ADDRESS, 'balance_eth': '0', 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Backend sponsor démarré sur http://localhost:5000")
    if w3 and w3.is_connected():
        print(f"✅ Connecté à Sepolia RPC")
        print(f"Dernier bloc: {w3.eth.block_number}")
    else:
        print("❌ Impossible de se connecter à Sepolia RPC")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
