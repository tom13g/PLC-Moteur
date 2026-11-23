# Simulation d'automate en Modbus TCP

Ce projet simule un automate industriel (PLC) qui pilote un moteur asynchrone et expose son capteur de vitesse en Modbus TCP, avec Python et pymodbus. Il est prévu pour servir de backend à une IHM graphique : toute la logique passe par des coils et registres Modbus.

## Scénario simulé

- **Actionneur** : moteur asynchrone, commandé en marche/arrêt par un coil.
- **Capteur** : vitesse de rotation en tr/min.
- **Mode automatique** (par défaut) : en marche, la vitesse monte vers la vitesse nominale de 1500 tr/min.
- **Mode manuel** : en marche, la vitesse rejoint la consigne choisie par l'opérateur (0 à 1500 tr/min). Si la consigne baisse en cours de marche, le moteur ralentit jusqu'à elle.
- **Rampes réglables** : accélération (300 tr/min/s par défaut) et décélération (150 tr/min/s par défaut), de 50 à 3000 tr/min/s.
- **Arrêt d'urgence** : le moteur freine à 1500 tr/min/s (non réglable) et la commande de marche retombe. Tant que l'arrêt d'urgence n'est pas réarmé, toute demande de marche est refusée. Après réarmement, le moteur ne repart pas seul : il faut redemander la marche.

Cet arrêt d'urgence est une simulation logicielle. Sur une installation réelle, un arrêt d'urgence est câblé et ne passe ni par une IHM ni par Modbus.

## Table d'échange Modbus

| Type | Adresse | Accès client | Description | Échelle |
|------|---------|--------------|-------------|---------|
| Coil | 0 | Lecture/écriture | Commande marche/arrêt du moteur | - |
| Coil | 1 | Lecture/écriture | Arrêt d'urgence (vrai = enclenché, faux = réarmé) | - |
| Coil | 2 | Lecture/écriture | Mode (faux = automatique, vrai = manuel) | - |
| Holding Register | 0 | Lecture/écriture | Consigne de vitesse du mode manuel | 1 point = 1 tr/min |
| Holding Register | 1 | Lecture/écriture | Rampe d'accélération | 1 point = 1 tr/min/s |
| Holding Register | 2 | Lecture/écriture | Rampe de décélération | 1 point = 1 tr/min/s |
| Input Register | 0 | Lecture seule | Vitesse de rotation mesurée | 1 point = 1 tr/min |
| Input Register | 1 | Lecture seule | Consigne de vitesse suivie par l'automate | 1 point = 1 tr/min |

L'automate ramène lui-même les réglages dans leurs bornes : une valeur hors plage écrite dans un holding register est corrigée dans le registre au cycle suivant.

Le serveur écoute sur le port 502 et répond à l'identifiant d'esclave 1. Ces valeurs sont définies dans `src/tp_simu_auto/modbus_map.py`, importé par le serveur et par le client : aucune adresse n'est écrite en dur ailleurs.

## Installation

Prérequis : [uv](https://github.com/astral-sh/uv), qui installe lui-même Python 3.13.

```bash
# Sur Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sur Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Puis, dans le dossier du projet :

```bash
uv sync
```

Cette commande crée l'environnement virtuel `.venv`, installe pymodbus et installe le paquet `tp_simu_auto` en mode éditable.

## Utilisation

Dans un premier terminal, lancer le serveur :

```bash
uv run server.py
```

Dans un second terminal, lancer le client de démonstration :

```bash
uv run client.py
```

Le client démarre le moteur, affiche la vitesse toutes les 0,2 s pendant 7 s, arrête le moteur, puis affiche la vitesse pendant le retour au repos :

```
--- Demarrage du moteur ---
09:31:30.299 | Moteur=ON  | Vitesse =    0.0 tr/min
09:31:30.501 | Moteur=ON  | Vitesse =  321.0 tr/min
09:31:30.700 | Moteur=ON  | Vitesse =  650.0 tr/min
...
--- Arret du moteur ---
09:31:32.500 | Moteur=OFF | Vitesse = 1500.0 tr/min
09:31:32.701 | Moteur=OFF | Vitesse = 1392.0 tr/min
...
```

Le serveur s'arrête avec Ctrl+C.

### IHM graphique

Toujours avec le serveur lancé :

L'IHM est un flow Node-RED, installé localement dans le dossier `nodered/` (prérequis : [Node.js](https://nodejs.org/)).

Une seule fois, pour installer Node-RED et ses palettes :

```bash
cd nodered
npm install
```

Puis, toujours avec le serveur Python lancé :

```bash
cd nodered
npm start
```

Le démarrage prend de quelques secondes à une trentaine de secondes. Ensuite :

- IHM : <http://127.0.0.1:1880/dashboard/moteur>
- Éditeur du flow : <http://127.0.0.1:1880/>

L'IHM, en thème sombre, comporte quatre zones :

- **Synoptique et commande** : dessin du moteur dont le ventilateur et l'accouplement tournent selon la vitesse, phase en cours, vitesse et consigne suivie, sélecteur de mode Auto / Manuel, boutons Marche et Arrêt, bouton d'arrêt d'urgence (remplacé par un bouton de réarmement quand il est enclenché), état de la liaison avec l'automate.
- **Vitesse de rotation** : jauge et courbe sur la dernière minute.
- **Réglages** : trois curseurs (consigne du mode manuel, rampe d'accélération, rampe de décélération) et un bouton de retour aux valeurs par défaut. Les curseurs affichent les valeurs relues dans l'automate.
- **Détails** : commande, mode, consigne suivie, vitesse, accélération, vitesse max atteinte, temps de marche, nombre de démarrages et d'arrêts d'urgence.

Le flow relit les coils et les input registers toutes les 0,2 s, les réglages toutes les 0,5 s. L'arrêt d'urgence, le mode et les réglages sont gérés par l'automate ; l'IHM ne fait que les écrire et les relire. La phase, l'accélération et les compteurs sont en revanche calculés dans le nœud « Calculs » du flow, et les compteurs repartent de zéro quand Node-RED redémarre.

Le flow utilise les palettes `node-red-contrib-modbus` et `@flowfuse/node-red-dashboard`. Ses adresses Modbus sont saisies dans le flow (lectures dans les trois nœuds Modbus Read, écritures dans le nœud « Table d'écriture ») : en cas de changement dans `modbus_map.py`, il faut les reporter à la main.

## Structure du projet

```
├── server.py                  # Serveur Modbus TCP + boucle de simulation
├── client.py                  # Client de démonstration en console
├── nodered/
│   ├── flows.json             # Flow de l'IHM (Modbus + dashboard)
│   ├── package.json           # Node-RED et palettes, script `npm start`
│   └── settings.js            # Réglages Node-RED (valeurs par défaut)
├── src/tp_simu_auto/
│   ├── modbus_map.py          # Adresses Modbus et facteurs d'échelle
│   └── automate.py            # Modèle physique (dataclass Automate, méthode step)
├── pyproject.toml             # Configuration uv et dépendances
├── uv.lock                    # Versions verrouillées
└── LICENSE
```

### Fonctionnement du serveur

`server.py` crée un `ModbusTcpServer` à partir d'un `SimDevice` et garde une référence à cet objet. Une tâche asyncio s'exécute toutes les 0,2 s :

1. elle lit les coils (marche, arrêt d'urgence, mode) et les réglages avec `server.async_getValues(...)` ;
2. elle appelle `automate.step(dt)` ;
3. elle écrit avec `server.async_setValues(...)` la vitesse et la consigne suivie dans les input registers, les réglages s'ils ont dû être bornés, et le coil de marche s'il est retombé sur arrêt d'urgence.

## Version de pymodbus

Le code est écrit pour pymodbus 3.15. L'API de pymodbus change entre versions mineures : ici le datastore est décrit avec `SimData` / `SimDevice` (module `pymodbus.simulator`), qui remplacent `ModbusSequentialDataBlock` / `ModbusDeviceContext` des versions précédentes. Avant de monter de version, vérifier le code source installé dans `.venv/Lib/site-packages/pymodbus`.

## Dépannage

**Port 502 indisponible.** Sous Linux, les ports inférieurs à 1024 demandent les droits administrateur (`sudo uv run server.py`). Sinon, changer `PORT` dans `src/tp_simu_auto/modbus_map.py`.

**Le client affiche « Connexion impossible ».** Le serveur n'est pas lancé, ou un pare-feu bloque le port.

## Ressources

- [Documentation pymodbus](https://pymodbus.readthedocs.io/)
- [Documentation uv](https://docs.astral.sh/uv/)
- [Spécification Modbus](https://modbus.org/specs.php)
