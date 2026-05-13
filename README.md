# Sentinelle.CI Backend

Backend pour la plateforme de signalement citoyen sur blockchain.

## 🚀 Fonctionnalités

- Transaction blockchain sur Sepolia (via sponsor wallet)
- Mode démo pour les tests
- API RESTful pour Streamlit frontend

## 📡 Endpoints

### GET `/api/health`
Vérification de l'état du service

### POST `/api/sponsor`
Créer un signalement sur blockchain

### GET `/api/contract-info`
Informations du contrat blockchain

## 🔧 Configuration

Variables d'environnement :

- `SPONSOR_PRIVATE_KEY`: Clé privée du sponsor (optionnel)
- `SPONSOR_ADDRESS`: Adresse du sponsor
- `USE_REAL_TX`: `true` pour transactions réelles, `false` pour mode démo
- `PORT`: Port du serveur (défaut: 5000)

## 🐳 Déploiement

Déployé sur Render : [https://sentinelle-backend.onrender.com](https://sentinelle-backend.onrender.com)

## 📝 Licence

MIT
