"""Table d'échange Modbus de l'automate.

Seule source de vérité pour les adresses : le serveur ET le client importent
ce module, aucune adresse Modbus ne doit apparaître en dur ailleurs.
"""

# -------- Liaison --------
PORT = 502
DEVICE_ID = 1

# -------- Codes fonction (désignent le bloc visé lors de l'accès direct au datastore du serveur) --------
FC_READ_COILS = 1
FC_READ_HOLDING_REGISTERS = 3
FC_READ_INPUT_REGISTERS = 4

# -------- Coils (lecture/écriture) --------
# Les coils sont stockés par mots de 16 bits côté serveur.
NB_COILS = 16
CO_MOTEUR = 0  # commande marche/arrêt du moteur asynchrone
CO_ARRET_URGENCE = 1  # True = arrêt d'urgence enclenché (reste actif jusqu'au réarmement)
CO_MODE_MANUEL = 2  # False = automatique (vitesse nominale), True = manuel (consigne opérateur)

# -------- Holding registers (lecture/écriture) : réglages, en uint16 --------
NB_HOLDING_REGISTERS = 3
HR_CONSIGNE_MANUELLE = 0  # consigne de vitesse en mode manuel
HR_RAMPE_MONTEE = 1  # accélération
HR_RAMPE_DESCENTE = 2  # décélération à l'arrêt normal

# -------- Input registers (lecture seule pour le client), en uint16 --------
NB_INPUT_REGISTERS = 2
IR_VITESSE = 0  # vitesse de rotation mesurée
IR_CONSIGNE = 1  # consigne de vitesse réellement suivie par l'automate

# -------- Facteurs d'échelle : valeur registre = valeur physique * échelle --------
ECHELLE_VITESSE = 1  # 1 point = 1 tr/min (vitesse et consignes)
ECHELLE_RAMPE = 1  # 1 point = 1 tr/min par seconde


def vitesse_vers_registre(vitesse: float) -> int:
    """Convertit une vitesse en tr/min en valeur de registre."""
    return round(vitesse * ECHELLE_VITESSE)


def registre_vers_vitesse(registre: int) -> float:
    """Convertit une valeur de registre en vitesse en tr/min."""
    return registre / ECHELLE_VITESSE


def rampe_vers_registre(rampe: float) -> int:
    """Convertit une rampe en tr/min/s en valeur de registre."""
    return round(rampe * ECHELLE_RAMPE)


def registre_vers_rampe(registre: int) -> float:
    """Convertit une valeur de registre en rampe en tr/min/s."""
    return registre / ECHELLE_RAMPE
