"""Client de démonstration (IHM provisoire) : démarre le moteur, observe, l'arrête."""

import sys
import time
from datetime import datetime

from pymodbus.client import ModbusTcpClient

from tp_simu_auto import modbus_map as mm

HOTE = "127.0.0.1"
INTERVALLE = 0.2  # secondes entre deux affichages
DUREE_MARCHE = 7.0  # secondes d'observation moteur en marche
DUREE_ARRET = 12.0  # secondes d'observation pendant le retour au repos


def afficher_capteurs(client: ModbusTcpClient) -> None:
    """Lit la commande et les capteurs puis les affiche avec un horodatage."""
    coils = client.read_coils(mm.CO_MOTEUR, count=1, device_id=mm.DEVICE_ID)
    registres = client.read_input_registers(
        mm.IR_VITESSE, count=1, device_id=mm.DEVICE_ID
    )
    horodatage = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    if coils.isError() or registres.isError():
        print(f"{horodatage} | Erreur de lecture Modbus")
        return
    vitesse = mm.registre_vers_vitesse(registres.registers[0])
    etat = "ON " if coils.bits[0] else "OFF"
    print(f"{horodatage} | Moteur={etat} | Vitesse = {vitesse:6.1f} tr/min")


def observer(client: ModbusTcpClient, duree: float) -> None:
    """Affiche les capteurs à intervalle régulier pendant duree secondes."""
    debut = time.monotonic()
    n = 0
    while n * INTERVALLE <= duree:
        afficher_capteurs(client)
        n += 1
        # Echéance absolue : le temps de lecture ne fait pas dériver la cadence.
        time.sleep(max(0.0, debut + n * INTERVALLE - time.monotonic()))


def main() -> int:
    client = ModbusTcpClient(HOTE, port=mm.PORT)
    if not client.connect():
        print(f"Connexion impossible au serveur Modbus {HOTE}:{mm.PORT}")
        return 1
    try:
        urgence = client.read_coils(mm.CO_ARRET_URGENCE, count=1, device_id=mm.DEVICE_ID)
        if not urgence.isError() and urgence.bits[0]:
            print("Arret d'urgence enclenche : le moteur ne demarrera pas tant qu'il n'est pas rearme.")

        print("--- Demarrage du moteur ---")
        client.write_coil(mm.CO_MOTEUR, True, device_id=mm.DEVICE_ID)
        observer(client, DUREE_MARCHE)

        print("--- Arret du moteur ---")
        client.write_coil(mm.CO_MOTEUR, False, device_id=mm.DEVICE_ID)
        observer(client, DUREE_ARRET)
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
