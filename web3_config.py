from web3 import Web3
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Charge les variables depuis .env

# 1. Connexion à Sepolia via un RPC public
SEPOLIA_RPC = "https://ethereum-sepolia.publicnode.com"
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))

# Vérifie la connexion
if not w3.is_connected():
    raise Exception("Impossible de se connecter à Sepolia")

print(f"Connecté à Sepolia : bloc {w3.eth.block_number}")

# 2. Configuration du contrat
CONTRACT_ADDRESS = "0xTonAdresseDeContrat"  # Remplace par l'adresse réelle
# Remplace [...] par ton ABI complet (depuis Remix par exemple)
CONTRACT_ABI = json.loads('''
[
    {
        "inputs": [
            {"internalType": "address","name": "user_address","type": "address"},
            {"internalType": "string","name": "report_type","type": "string"},
            {"internalType": "int256","name": "latitude","type": "int256"},
            {"internalType": "int256","name": "longitude","type": "int256"},
            {"internalType": "string","name": "description","type": "string"}
        ],
        "name": "createReport",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
''')  # Attention : assure-toi que l'ABI correspond exactement à ton contrat

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# 3. Clé privée (à mettre dans .env, jamais en clair)
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # ex: "0x123abc..."
if not PRIVATE_KEY:
    raise Exception("PRIVATE_KEY non définie dans .env")

# Déduire l'adresse publique associée à cette clé
account = w3.eth.account.from_key(PRIVATE_KEY)
MY_ADDRESS = account.address
print(f"Sponsor wallet : {MY_ADDRESS}")

# 4. Fonction pour créer un signalement sponsorisé
def create_report_on_chain(user_address, report_type, lat, lng, description):
    # Construire la transaction
    nonce = w3.eth.get_transaction_count(MY_ADDRESS)
    tx = contract.functions.createReport(
        user_address,
        report_type,
        int(lat * 1_000_000),    # Exemple : conversion pour éviter les floats
        int(lng * 1_000_000),
        description
    ).build_transaction({
        'from': MY_ADDRESS,
        'nonce': nonce,
        'gas': 300000,           # Marge de sécurité
        'gasPrice': w3.to_wei('3', 'gwei')  # Prix du gaz (ajustable)
    })
    
    # Signer avec TA clé privée
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    
    # Envoyer la transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash.hex()
