# Table d'échange Modbus de l'automate

Copie de la section 3 du [README](README.md) : table d'échange Modbus de l'automate simulé (moteur asynchrone).

Serveur : **port 502**, **esclave n°1**. Adresses à partir de 0. **Toutes les variables Modbus du projet sont dans ce tableau unique.**

| Table Modbus | Nature | Accès client | Codes fonction | Adr. | Notation hist. | Variable | Constante Python (`modbus_map.py`) | Attribut Python (`Automate`) | Topic Node-RED (écriture) | Unité | Plage | Défaut |
|--------------|--------|--------------|----------------|------|----------------|----------|------------------------------------|------------------------------|---------------------------|-------|-------|--------|
| Coil | Bit TOR — commande | Lecture / écriture | 1, 5, 15 | 0 | 00001 | Marche / arrêt du moteur (`True` = marche). **Remis à `False` par l'automate en arrêt d'urgence** | `CO_MOTEUR` | `moteur_en_marche` | `marche` | — | `False` / `True` | `False` |
| Coil | Bit TOR — commande | Lecture / écriture | 1, 5, 15 | 1 | 00002 | Arrêt d'urgence (`True` = enclenché, `False` = réarmé) | `CO_ARRET_URGENCE` | `arret_urgence` | `urgence` | — | `False` / `True` | `False` |
| Coil | Bit TOR — commande | Lecture / écriture | 1, 5, 15 | 2 | 00003 | Mode (`False` = automatique, `True` = manuel) | `CO_MODE_MANUEL` | `mode_manuel` | `manuel` | — | `False` / `True` | `False` |
| Coil | Bit TOR | Lecture / écriture | 1, 5, 15 | 3 à 15 | 00004 à 00016 | Réservés, non utilisés | — | — | — | — | `False` / `True` | `False` |
| Discrete Input | Bit TOR — état | Lecture seule | 2 | 0 à 15 | 10001 à 10016 | Non utilisées (zone présente mais vide) | — | — | — | — | `False` | `False` |
| Holding Register | Mot 16 bits — paramètre / consigne | Lecture / écriture | 3, 6, 16 | 0 | 40001 | Consigne de vitesse du mode manuel. **Bornée par l'automate** | `HR_CONSIGNE_MANUELLE` | `consigne_manuelle` | `consigne` | tr/min | 0 à 1500 | 750 |
| Holding Register | Mot 16 bits — paramètre | Lecture / écriture | 3, 6, 16 | 1 | 40002 | Rampe d'accélération. **Bornée par l'automate** | `HR_RAMPE_MONTEE` | `vitesse_montee` | `rampe_montee` | tr/min/s | 50 à 3000 | 300 |
| Holding Register | Mot 16 bits — paramètre | Lecture / écriture | 3, 6, 16 | 2 | 40003 | Rampe de décélération (arrêt normal). **Bornée par l'automate** | `HR_RAMPE_DESCENTE` | `vitesse_descente` | `rampe_descente` | tr/min/s | 50 à 3000 | 150 |
| Input Register | Mot 16 bits — mesure | Lecture seule | 4 | 0 | 30001 | Vitesse de rotation mesurée | `IR_VITESSE` | `vitesse` | — (lecture seule) | tr/min | 0 à 1500 | 0 |
| Input Register | Mot 16 bits — mesure | Lecture seule | 4 | 1 | 30002 | Consigne de vitesse réellement suivie par l'automate | `IR_CONSIGNE` | `consigne` (propriété) | — (lecture seule) | tr/min | 0 à 1500 | 0 |

**Notes :**

- **Coil 0** : l'automate peut l'écrire lui-même. Si l'arrêt d'urgence est enclenché, il le remet à `False` au cycle suivant : une demande de marche pendant l'arrêt d'urgence est donc annulée.
- **Bornage des holding registers** : un client peut écrire n'importe quelle valeur de 0 à 65 535. L'automate ramène la valeur dans sa plage et **réécrit le registre corrigé** au cycle suivant. Exemple : écrire 5000 dans le holding register 1 donne 3000 à la relecture.
- **Consigne suivie (IR 1) ≠ consigne manuelle (HR 0)** : la consigne suivie est la vitesse que l'automate vise réellement en ce moment, en tenant compte du mode, de la commande de marche et de l'arrêt d'urgence (voir la [section 4 du README](README.md#4-comportement-de-lautomate)).
- **Topic Node-RED** : nom de l'ordre envoyé par un bouton ou un curseur de l'IHM ; la fonction « Table d'écriture » le traduit en écriture Modbus (code 5 pour un coil, code 6 pour un holding register) à l'adresse indiquée.

