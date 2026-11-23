"""Serveur Modbus TCP simulant un automate qui pilote un moteur asynchrone.

Carte mémoire (CO : Coils, DI : Discrete Inputs, HR : Holding Registers, IR : Input Registers),
adresses définies dans tp_simu_auto.modbus_map, esclave 1, port 502 :
    CO 0        : commande marche/arrêt du moteur (retombe à False sur arrêt d'urgence)
    CO 1        : arrêt d'urgence (True = enclenché, False = réarmé)
    CO 2        : mode (False = automatique, True = manuel)
    CO 3 à 15   : réservés
    DI 0 à 15   : inutilisés
    HR 0        : consigne de vitesse du mode manuel en tr/min (0 à 1500, défaut 750)
    HR 1        : rampe d'accélération en tr/min/s (50 à 3000, défaut 300)
    HR 2        : rampe de décélération en tr/min/s (50 à 3000, défaut 150)
    IR 0        : vitesse de rotation mesurée en tr/min (1 registre, ex. 1500 = 1500 tr/min)
    IR 1        : consigne de vitesse suivie par l'automate en tr/min
Les HR hors plage sont ramenés dans leurs bornes par l'automate au cycle suivant.
"""

import asyncio

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice

from tp_simu_auto import modbus_map as mm
from tp_simu_auto.automate import Automate

PERIODE = 0.2  # secondes entre deux pas de simulation


def reglages_vers_registres(automate: Automate) -> list[int]:
    """Valeurs des holding registers de réglage, dans l'ordre des adresses."""
    registres = [0] * mm.NB_HOLDING_REGISTERS
    registres[mm.HR_CONSIGNE_MANUELLE] = mm.vitesse_vers_registre(automate.consigne_manuelle)
    registres[mm.HR_RAMPE_MONTEE] = mm.rampe_vers_registre(automate.vitesse_montee)
    registres[mm.HR_RAMPE_DESCENTE] = mm.rampe_vers_registre(automate.vitesse_descente)
    return registres


def build_device(automate: Automate) -> SimDevice:
    """Construit l'automate Modbus (4 blocs distincts : coils, DI, HR, IR)."""
    coils = [SimData(0, count=mm.NB_COILS, values=False, datatype=DataType.BITS)]
    # Les réglages démarrent sur les valeurs par défaut de l'automate.
    holding_registers = [
        SimData(0, values=reglages_vers_registres(automate), datatype=DataType.UINT16)
    ]
    input_registers = [
        SimData(0, count=mm.NB_INPUT_REGISTERS, values=0, datatype=DataType.UINT16)
    ]
    # Bloc non utilisé par le scénario : une entrée minimale suffit.
    discrete_inputs = [SimData(0, count=16, values=False, datatype=DataType.BITS)]
    return SimDevice(
        id=mm.DEVICE_ID,
        simdata=(coils, discrete_inputs, holding_registers, input_registers),
    )


async def simulation(server: ModbusTcpServer, automate: Automate) -> None:
    """Boucle de fond : coils et réglages -> physique -> registres capteurs."""
    loop = asyncio.get_running_loop()
    precedent = loop.time()
    while True:
        await asyncio.sleep(PERIODE)
        # dt mesuré plutôt que PERIODE : sleep() n'est pas exact, surtout sous Windows.
        maintenant = loop.time()
        dt, precedent = maintenant - precedent, maintenant

        # 1. Lire les coils de commande et les réglages
        coils = await server.async_getValues(
            mm.DEVICE_ID, mm.FC_READ_COILS, 0, mm.NB_COILS
        )
        automate.moteur_en_marche = bool(coils[mm.CO_MOTEUR])
        automate.arret_urgence = bool(coils[mm.CO_ARRET_URGENCE])
        automate.mode_manuel = bool(coils[mm.CO_MODE_MANUEL])

        reglages = await server.async_getValues(
            mm.DEVICE_ID, mm.FC_READ_HOLDING_REGISTERS, 0, mm.NB_HOLDING_REGISTERS
        )
        automate.consigne_manuelle = mm.registre_vers_vitesse(reglages[mm.HR_CONSIGNE_MANUELLE])
        automate.vitesse_montee = mm.registre_vers_rampe(reglages[mm.HR_RAMPE_MONTEE])
        automate.vitesse_descente = mm.registre_vers_rampe(reglages[mm.HR_RAMPE_DESCENTE])
        automate.borner_reglages()

        # 2. Avancer la physique
        automate.step(dt)

        # 3. Réécrire dans les registres Modbus ce que l'automate a décidé :
        #    capteurs, réglages ramenés dans leurs bornes, commande retombée sur arrêt d'urgence.
        await server.async_setValues(
            mm.DEVICE_ID,
            mm.FC_READ_INPUT_REGISTERS,
            0,
            [
                mm.vitesse_vers_registre(automate.vitesse),
                mm.vitesse_vers_registre(automate.consigne),
            ],
        )
        if (bornes := reglages_vers_registres(automate)) != list(reglages):
            await server.async_setValues(
                mm.DEVICE_ID, mm.FC_READ_HOLDING_REGISTERS, 0, bornes
            )
        if bool(coils[mm.CO_MOTEUR]) != automate.moteur_en_marche:
            await server.async_setValues(
                mm.DEVICE_ID, mm.FC_READ_COILS, mm.CO_MOTEUR, [automate.moteur_en_marche]
            )

        if automate.arret_urgence:
            etat = "AU "
        else:
            etat = "ON " if automate.moteur_en_marche else "OFF"
        print(
            f"Moteur={etat}"
            f" | Mode={'MANU' if automate.mode_manuel else 'AUTO'}"
            f" | Consigne = {automate.consigne:6.1f}"
            f" | Vitesse = {automate.vitesse:6.1f} tr/min"
        )


async def main() -> None:
    automate = Automate()
    server = ModbusTcpServer(build_device(automate), address=("0.0.0.0", mm.PORT))
    tache = asyncio.create_task(simulation(server, automate))
    print(f"Serveur Modbus TCP demarre sur le port {mm.PORT} (Ctrl+C pour arreter)")
    try:
        await server.serve_forever()
    finally:
        tache.cancel()
        await server.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Serveur arrete.")
