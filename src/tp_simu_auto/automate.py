"""Modèle physique de l'automate : un moteur asynchrone et son capteur de vitesse."""

from dataclasses import dataclass


def _borner(valeur: float, mini: float, maxi: float) -> float:
    return min(max(valeur, mini), maxi)


@dataclass
class Automate:
    """Etat et physique du procédé simulé."""

    # Actionneur et commandes
    moteur_en_marche: bool = False
    arret_urgence: bool = False
    mode_manuel: bool = False

    # Capteur 1 : vitesse de rotation (tr/min)
    vitesse: float = 0.0
    vitesse_min: float = 0.0
    vitesse_max: float = 1500.0  # vitesse nominale, visée en mode automatique

    # Réglages modifiables par l'opérateur
    consigne_manuelle: float = 750.0  # tr/min, visée en mode manuel
    vitesse_montee: float = 300.0  # tr/min par seconde
    vitesse_descente: float = 150.0  # tr/min par seconde, arrêt normal

    # Bornes des rampes réglables et freinage d'urgence (non réglable)
    rampe_min: float = 50.0
    rampe_max: float = 3000.0
    freinage_urgence: float = 1500.0  # tr/min par seconde

    def borner_reglages(self) -> None:
        """Ramène les réglages dans leurs bornes (un client peut écrire n'importe quoi)."""
        self.consigne_manuelle = _borner(self.consigne_manuelle, self.vitesse_min, self.vitesse_max)
        self.vitesse_montee = _borner(self.vitesse_montee, self.rampe_min, self.rampe_max)
        self.vitesse_descente = _borner(self.vitesse_descente, self.rampe_min, self.rampe_max)

    @property
    def consigne(self) -> float:
        """Vitesse actuellement visée par l'automate."""
        if self.arret_urgence or not self.moteur_en_marche:
            return self.vitesse_min
        return self.consigne_manuelle if self.mode_manuel else self.vitesse_max

    def step(self, dt: float) -> None:
        """Avance la simulation de dt secondes."""
        # L'arrêt d'urgence retombe la commande : il faudra redemander la marche après réarmement.
        if self.arret_urgence:
            self.moteur_en_marche = False

        cible = self.consigne
        if self.vitesse < cible:
            self.vitesse = min(self.vitesse + self.vitesse_montee * dt, cible)
        elif self.vitesse > cible:
            descente = self.freinage_urgence if self.arret_urgence else self.vitesse_descente
            self.vitesse = max(self.vitesse - descente * dt, cible)
        self.vitesse = _borner(self.vitesse, self.vitesse_min, self.vitesse_max)
