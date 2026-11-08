"""The commercial offer of the RoadAnomaly product: subscription plans and detection modes.

Single source for the prices, quotas, features and modes shown by the product app, its report and its tests.
The plans follow the marketing deck (slides 14-15: Bronze / Silver / Gold, prices in Tunisian dinars); the two
modes are the "offre adaptée" of the targeting slide (22): maximum detection, or few false alarms.
The test numbers quoted for each mode are read from reports/results/test_results.json (notebook 5), never typed.
"""
import json
from dataclasses import dataclass

from roadanomaly import data_pipeline as dp

TEST_RESULTS = dp.REPO_ROOT / "reports" / "results" / "test_results.json"
TRIAL_IMAGES = 20          # images in the free trial (deck: "essai gratuit limité")
MAX_IMAGES_PER_RUN = 10    # images analysed per click, so one batch stays interactive on a laptop GPU


@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    audience: str
    price_dt: int | None          # monthly price in Tunisian dinars; None = free
    monthly_images: int | None    # images analysed per month; None = unlimited
    explanation: bool             # "pourquoi l'obstacle a été signalé" (heatmap + factors)
    reports: bool                 # synthesis report (CSV + HTML)
    api: bool                     # integration into the client's own systems
    perks: tuple[str, ...]

    @property
    def price_label(self):
        return "Gratuit" if self.price_dt is None else f"{self.price_dt} DT / mois"


PLANS = {
    "essai": Plan(
        "essai", "Essai gratuit", "Pour tester RoadAnomaly sur vos propres images",
        None, TRIAL_IMAGES, explanation=True, reports=True, api=False,
        perks=(f"{TRIAL_IMAGES} images à analyser", "Les deux modes de détection",
               "Explication visuelle et rapport inclus", "Sans carte bancaire"),
    ),
    "bronze": Plan(
        "bronze", "Bronze", "Startups ADAS et laboratoires R&D",
        50, 500, explanation=False, reports=False, api=False,
        perks=("Jusqu'à 500 images analysées par mois", "Obstacle surligné sur chaque image",
               "Support standard par e-mail"),
    ),
    "silver": Plan(
        "silver", "Silver", "Gestionnaires de routes, flottes de transport, bureaux d'études",
        200, 5000, explanation=True, reports=True, api=False,
        perks=("Jusqu'à 5 000 images analysées par mois", "Explication visuelle : pourquoi l'obstacle a été signalé",
               "Rapports de synthèse sur les détections", "Support prioritaire"),
    ),
    "gold": Plan(
        "gold", "Gold", "Équipementiers (Tier-1) et constructeurs",
        600, None, explanation=True, reports=True, api=True,
        perks=("Volume d'images illimité", "Intégration dans vos propres systèmes (API, bêta)",
               "Accompagnement personnalisé sur devis"),
    ),
}
PAID_PLANS = ("bronze", "silver", "gold")


def cheapest_plan_with(feature):
    """Name of the cheapest paid plan that includes `feature` ('explanation', 'reports' or 'api')."""
    return next(PLANS[k].name for k in PAID_PLANS if getattr(PLANS[k], feature))


@dataclass(frozen=True)
class Mode:
    key: str
    name: str
    model: str        # folder in models/ (shared format)
    promise: str
    use_when: str


MODES = {
    "max": Mode("max", "Détection maximale", "A_deeplabv3plus", "Ne rien laisser passer.",
                "Recherche, annotation de données, revue de sécurité : une fausse alarme coûte moins "
                "qu'un obstacle manqué."),
    "sobre": Mode("sobre", "Peu de fausses alarmes", "B_feature_ae", "Des alertes plus rares et plus sûres.",
                  "Alerte conducteur, inspection de flotte : chaque fausse alarme coûte du temps ou de la confiance."),
}


def _fraction(text):
    """'20/22' -> (20, 22)."""
    found, total = (int(x) for x in str(text).split("/"))
    return found, total


def tested(mode, results_path=TEST_RESULTS):
    """What the mode's model did on the sealed test split, or None when notebook 5 has not run.

    Returns {"found", "obstacles", "false_alarms", "flagged", "photos"}: obstacles found out of the annotated ones,
    and false alarms out of the zones the model flagged.
    """
    if not results_path.exists():
        return None
    results = json.loads(results_path.read_text())
    summary = results["models"].get(mode.model, {}).get("summary")
    if summary is None:
        return None
    found, obstacles = _fraction(summary["objects detected"])
    false_alarms, flagged = _fraction(summary["false alarms / predicted blobs"])
    return {"found": found, "obstacles": obstacles, "false_alarms": false_alarms, "flagged": flagged,
            "photos": len(results["frames"])}


def tested_sentence(mode, results_path=TEST_RESULTS):
    """One plain French sentence with the mode's test numbers (empty when they are not available)."""
    t = tested(mode, results_path)
    if t is None:
        return ""
    return (f"Dans nos tests : {t['found']} obstacles repérés sur {t['obstacles']}, "
            f"{t['false_alarms']} fausses alarmes sur {t['flagged']} zones signalées.")
