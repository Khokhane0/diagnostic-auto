# diagnostic-auto
# 🚗 Diagnostic Auto - Application OBD-II

Application de diagnostic automobile complète développée en Python avec Flask.

## 📋 Fonctionnalités

- 🔌 Connexion via câble OBD-II vers USB (ELM327)
- 📊 Lecture en temps réel des données moteur (RPM, vitesse, température, etc.)
- 🔴 Diagnostic des codes d'erreur (DTC) pour tous les systèmes
- 🛞 Support des systèmes avancés : ABS, Airbag, Transmission
- 🔧 Services spéciaux : réinitialisation adaptations, vidange, freins
- 📈 Graphiques en temps réel
- ⚙️ Mode expert avec commandes personnalisées
- 🌐 Interface web responsive

## 🛠️ Technologies utilisées

- **Python 3.8+**
- **Flask** - Serveur web
- **python-OBD** - Communication OBD-II
- **Chart.js** - Graphiques
- **HTML/CSS/JavaScript** - Interface utilisateur

## 📦 Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-username/diagnostic-auto.git
cd diagnostic-auto

# 2. Créer un environnement virtuel
python -m venv .venv

# 3. Activer l'environnement virtuel
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Installer les dépendances
pip install obd flask pyserial

# 5. Lancer l'application
python app.py
🚀 Utilisation
Branchez le câble OBD-II sur votre véhicule et sur votre ordinateur

Ouvrez votre navigateur sur http://127.0.0.1:5000

Cliquez sur "Connecter"

Explorez les différents onglets :

Tableau de bord : Vue d'ensemble des données

Codes Erreur : Diagnostic DTC

Avancé : Commandes personnalisées

Services : Réinitialisations et tests

Live Data : Graphiques temps réel

📁 Structure du projet
text
diagnostic-auto/
├── app.py                 # Serveur Flask principal
├── obd_advanced.py        # Scanner OBD-II avancé
├── templates/
│   └── dashboard_advanced.html  # Interface utilisateur
├── .gitignore             # Fichiers à ignorer
├── README.md              # Documentation
└── requirements.txt       # Dépendances
🛒 Matériel requis
Câble OBD-II vers USB (ELM327 recommandé)

Véhicule compatible OBD-II (2000+)

⚠️ Avertissement
Cette application est fournie à des fins éducatives et de diagnostic. L'auteur décline toute responsabilité en cas d'utilisation inappropriée ou de dommages causés au véhicule.

📝 Licence
MIT License

🤝 Contribution
Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

text
