"""RoadAnomaly, the product (MVP): the customer-facing web app of the marketing deck.

What the deck promises, and where it lives here:
- positioning (slide 19): unexpected obstacles, no closed list of objects, *with* an explanation -> Analyser page;
- the "offre adaptée" of the targeting slide (22): two modes, maximum detection or few false alarms (offer.MODES);
- the Bronze / Silver / Gold plans (slides 14-15): quotas and features gated by the plan (offer.PLANS);
- product (slide 13): import a photo, the obstacle is highlighted; user guide; synthesis reports;
- integration into the client's systems, Gold only (the FastAPI service of deployment/api).

The technical demo for the jury (six models, metrics, XAI internals) stays in deployment/app/streamlit_app.py.
Run from this folder so its own theme (.streamlit/config.toml) is used: `mise run product`.
"""
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import httpx
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))   # make `deployment` importable
from deployment import service  # noqa: E402
from deployment.product import findings, offer  # noqa: E402
from roadanomaly import data_pipeline as dp  # noqa: E402

LOGO, EMBLEM = HERE / "assets" / "logo.png", HERE / "assets" / "emblem.png"
TAGLINE = "L'IA qui repère l'inattendu sur la route"
API_URL = os.environ.get("ROADANOMALY_API_URL", "http://localhost:8000")
DEMO_JSON = dp.REPO_ROOT / "deployment" / "landing" / "public" / "demo" / "demo.json"

st.set_page_config(page_title=f"RoadAnomaly · {TAGLINE}", page_icon=str(EMBLEM), layout="wide",
                   initial_sidebar_state="expanded")

# What the theme cannot express: the hero, the positioning chips, verdict badges, plan cards
st.markdown("""
<style>
  .block-container { padding-top: 2.4rem; max-width: 1240px; }
  .ra-hero { display: flex; justify-content: space-between; align-items: flex-end; gap: 2rem; flex-wrap: wrap;
             border-bottom: 3px solid #ee6011; padding-bottom: 1.1rem; margin-bottom: 1.4rem; }
  .ra-hero h1 { font-size: 2.3rem; line-height: 1.15; margin: 0 0 .5rem; padding: 0; }
  .ra-hero p { font-size: 1.08rem; max-width: 46rem; margin: 0; color: #3b4660; }
  .ra-chips { display: flex; gap: .5rem; flex-wrap: wrap; margin: 0; padding: 0; list-style: none; }
  .ra-chips li { background: #ffffff; border: 1px solid #e6dcc3; border-radius: 999px; padding: .3rem .8rem;
                 font-size: .9rem; color: #2d3a5a; }
  .ra-chips li::before { content: "✓ "; color: #b8460b; font-weight: 700; }
  .ra-verdict { display: inline-block; border-radius: 6px; padding: .2rem .65rem; font-weight: 700; }
  .ra-alert { background: #fde3d2; color: #9a3a08; }
  .ra-clear { background: #e3e8f2; color: #2d3a5a; }
  .ra-plan { font-size: 1.45rem; font-weight: 700; color: #1f2a44; margin-bottom: .35rem; }
  .ra-price { font-size: 1.35rem; font-weight: 700; color: #2d3a5a; margin: .3rem 0 .4rem; white-space: nowrap; }
  .ra-muted { color: #5b6478; font-size: .92rem; }
  .ra-audience { min-height: 4.8em; color: #5b6478; font-size: .92rem; }
  .ra-tagline { text-align: center; color: #b8460b; font-weight: 700; letter-spacing: .02em; margin: -.4rem 0 1rem; }
  [data-testid="stImageCaption"] { color: #5b6478; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ session: the customer's account (simulated)
def init_session():
    defaults = {"plan": "essai", "used": 0, "analyses": {}, "explanations": {}, "history": [], "shown": []}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def current_plan():
    return offer.PLANS[st.session_state["plan"]]


def remaining_images():
    """Images left this month, or None when the plan is unlimited."""
    quota = current_plan().monthly_images
    return None if quota is None else max(quota - st.session_state["used"], 0)


# ------------------------------------------------------------------ inputs
@st.cache_data(show_spinner=False)
def example_catalogue():
    """Openly licensed validation photographs (the sealed test split never appears in the product)."""
    titles = {i["frame"]: i["title"] for i in json.loads(DEMO_JSON.read_text())["images"]} if DEMO_JSON.exists() else {}
    frames = [row["frame"] for row in dp.read_manifest() if row["split"] == "val"]
    return {f: titles.get(f, f.split("_", 1)[-1].replace("_", " ")) for f in frames}


@st.cache_data(show_spinner=False)
def load_example(frame):
    image, _ = dp.load_frame(frame)
    return image


def collect_inputs(source):
    """The images the customer chose: list of (id, label, RGB uint8 array). Unreadable uploads are reported."""
    if source == "Exemples":
        catalogue = example_catalogue()
        frames = st.multiselect("Photos d'exemple (routes réelles, licences libres)", list(catalogue),
                                default=list(catalogue)[:2], format_func=catalogue.get,
                                max_selections=offer.MAX_IMAGES_PER_RUN)
        return [(f"ex:{f}", catalogue[f], load_example(f)) for f in frames]
    uploads = st.file_uploader("Vos photos de route (JPEG, PNG ou WebP, 15 Mo maximum)", accept_multiple_files=True,
                               type=["jpg", "jpeg", "png", "webp"])
    inputs = []
    for upload in (uploads or [])[: offer.MAX_IMAGES_PER_RUN]:
        data = upload.getvalue()
        try:
            inputs.append((f"up:{hashlib.sha1(data).hexdigest()[:16]}", upload.name, service.decode_image(data)))
        except service.InputError as error:
            st.error(f"« {upload.name} » ne peut pas être analysée : {error}.")
    if uploads and len(uploads) > offer.MAX_IMAGES_PER_RUN:
        st.warning(f"Seules les {offer.MAX_IMAGES_PER_RUN} premières images sont analysées à chaque lancement.")
    return inputs


# ------------------------------------------------------------------ analysis
def analyse(image_id, label, image, mode):
    """Run the mode's model once per (image, mode); count it against the quota; keep it in the history."""
    key = f"{image_id}|{mode.key}"
    if key in st.session_state["analyses"]:
        return key
    left = remaining_images()
    if left == 0:
        return None
    result = service.analyse(mode.model, image)
    obstacles = findings.find_obstacles(result["mask"])
    annotated = findings.annotate(result["image"], result["mask"], obstacles)
    st.session_state["analyses"][key] = {"label": label, "mode": mode.key, "source": image, "image": result["image"],
                                         "annotated": annotated, "obstacles": obstacles, "stats": result["stats"]}
    st.session_state["used"] += 1
    st.session_state["history"].append({
        "image": label, "mode": mode.name, "obstacles": len(obstacles), "obstacle_list": obstacles,
        "flagged_percent": result["stats"]["anomaly_percent"], "latency_ms": result["stats"]["latency_ms"],
        "analysed_at": datetime.now().strftime("%d/%m/%Y %H:%M"), "annotated": annotated})
    return key


def explanation_chart(rows):
    df = pd.DataFrame([{"Facteur": r["label"].capitalize(), "Part": r["share"],
                        "Effet": "renforce l'alerte" if r["raises"] else "atténue l'alerte"} for r in rows])
    return alt.Chart(df).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Part:Q", title="part de l'explication", axis=alt.Axis(format="%")),
        y=alt.Y("Facteur:N", sort=None, title=None, axis=alt.Axis(labelFontSize=13, labelLimit=240)),
        color=alt.Color("Effet:N", scale=alt.Scale(domain=["renforce l'alerte", "atténue l'alerte"],
                                                   range=["#ee6011", "#2d3a5a"]),
                        legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["Facteur", alt.Tooltip("Part:Q", format=".0%"), "Effet"],
    ).properties(height=210)


def show_explanation(key, analysis):
    mode = offer.MODES[analysis["mode"]]
    if key not in st.session_state["explanations"]:
        with st.spinner("RoadAnomaly prépare l'explication (une quinzaine de secondes)…"):
            _, e = service.explain(mode.model, analysis["source"])
        rows, sentence = findings.explanation(e["what"]["phi"])
        heat = service.blend(analysis["image"], service.heatmap_rgb(e["where"], "inferno"))
        st.session_state["explanations"][key] = {"heat": heat, "rows": rows, "sentence": sentence}
    x = st.session_state["explanations"][key]
    where, what = st.columns([1.15, 1], gap="large")
    where.image(x["heat"], width="stretch", caption="Où le modèle a regardé : plus c'est clair, plus la zone a pesé")
    with what:
        st.markdown("**Ce qui a déclenché l'alerte**")
        st.altair_chart(explanation_chart(x["rows"]), width="stretch")
        st.info(x["sentence"])
    st.caption("Une explication décrit le raisonnement du modèle ; ce n'est pas une preuve. Vérifiez toujours l'image.")


def locked(feature, needs):
    """Upsell card for a feature the current plan does not include."""
    with st.container(border=True):
        needed = offer.cheapest_plan_with(needs)
        st.markdown(f":material/lock: **{feature}** : disponible à partir de l'offre **{needed}** "
                    "(et pendant l'essai gratuit).")
        st.page_link(PAGES["offres"], label="Comparer les offres", icon=":material/workspace_premium:")


def show_result(key):
    a = st.session_state["analyses"][key]
    mode, obstacles = offer.MODES[a["mode"]], a["obstacles"]
    with st.container(border=True):
        badge = "ra-alert" if obstacles else "ra-clear"
        st.markdown(f"#### {a['label']}\n<span class='ra-verdict {badge}'>{findings.verdict(len(obstacles))}</span>"
                    f"&nbsp; <span class='ra-muted'>Mode {mode.name.lower()} · analysée en "
                    f"{a['stats']['latency_ms']:.0f} ms</span>", unsafe_allow_html=True)
        original, flagged = st.columns(2, gap="medium")
        original.image(findings.to_uint8(a["image"]), caption="Votre photo", width="stretch")
        flagged.image(a["annotated"], caption="Obstacles inattendus surlignés en orange", width="stretch")
        if obstacles:
            st.dataframe(pd.DataFrame([{"N°": o.number, "Position dans l'image": o.position,
                                        "Surface": o.area_percent} for o in obstacles]),
                         hide_index=True, width="stretch",
                         column_config={"Surface": st.column_config.ProgressColumn(
                             "Surface (% de l'image)", format="%.2f %%", min_value=0,
                             max_value=max(o.area_percent for o in obstacles))})
            if current_plan().explanation:
                if key in st.session_state["explanations"] or st.button(
                        "Pourquoi ce signalement ?", key=f"why:{key}", icon=":material/psychology_alt:"):
                    show_explanation(key, a)
            else:
                locked("L'explication visuelle (pourquoi l'obstacle a été signalé)", "explanation")
        else:
            st.caption("Rien d'inattendu dans ce mode. En cas de doute, relancez en mode détection maximale.")


# ------------------------------------------------------------------ pages
def analyser():
    st.markdown("""
<div class="ra-hero">
  <div>
    <h1>Repérez l'inattendu sur la route.</h1>
    <p>RoadAnomaly signale, au pixel près, les obstacles qu'aucune liste d'objets ne prévoit (animaux, rochers,
       chargements perdus, engins) et montre pourquoi il les a signalés.</p>
  </div>
  <ul class="ra-chips"><li>Sans liste fermée d'objets</li><li>Masque au pixel</li><li>Explication visuelle</li></ul>
</div>""", unsafe_allow_html=True)

    if not service.model_names():
        st.error("Le service n'est pas prêt : aucun modèle entraîné dans `models/`.")
        st.stop()

    pick, choose = st.columns([1.25, 1], gap="large")
    # the mode column is filled first: the analyse button of the image column needs the chosen mode
    with choose:
        st.markdown("##### 2 · Le mode")
        mode_key = st.radio("Mode de détection", list(offer.MODES), format_func=lambda k: offer.MODES[k].name,
                            captions=[f"{m.promise} {offer.tested_sentence(m)}" for m in offer.MODES.values()],
                            label_visibility="collapsed")
        mode = offer.MODES[mode_key]
        st.caption(f"Quand l'utiliser : {mode.use_when}")

    with pick:
        st.markdown("##### 1 · Vos images")
        source = st.segmented_control("Source", ["Mes photos", "Exemples"], default="Exemples",
                                      label_visibility="collapsed") or "Exemples"
        inputs = collect_inputs(source)
        left = remaining_images()
        blocked = left == 0
        count = len(inputs)
        if st.button(f"Analyser {count} image{'s' if count > 1 else ''}", type="primary", key="analyse",
                     disabled=count == 0 or blocked, icon=":material/center_focus_strong:"):
            shown, skipped = [], 0
            progress = st.progress(0.0, text="Analyse en cours…")
            for i, (image_id, label, image) in enumerate(inputs, start=1):
                key = analyse(image_id, label, image, mode)
                if key is None:
                    skipped += 1
                else:
                    shown.append(key)
                progress.progress(i / count, text=f"{i} / {count} images analysées")
            progress.empty()
            st.session_state["shown"] = shown
            if skipped:
                st.warning(f"{skipped} image(s) non analysée(s) : le quota de votre offre est atteint.")
        if blocked:
            st.warning(f"Vous avez utilisé toutes les images de l'offre {current_plan().name}.")
            st.page_link(PAGES["offres"], label="Passer à une offre supérieure", icon=":material/upgrade:")

    shown = [k for k in st.session_state["shown"] if k in st.session_state["analyses"]]
    if shown:
        total = sum(len(st.session_state["analyses"][k]["obstacles"]) for k in shown)
        flagged = sum(1 for k in shown if st.session_state["analyses"][k]["obstacles"])
        st.markdown(f"##### 3 · Résultats : {len(shown)} image{'s' if len(shown) > 1 else ''}, "
                    f"{total} obstacle{'s' if total > 1 else ''} signalé{'s' if total > 1 else ''} "
                    f"sur {flagged} image{'s' if flagged > 1 else ''}")
        for key in shown:
            show_result(key)


def rapport():
    st.title("Rapport de synthèse")
    plan = current_plan()
    if not plan.reports:
        locked("Le rapport de synthèse", "reports")
        return
    history = st.session_state["history"]
    if not history:
        st.info("Aucune image analysée pour l'instant : commencez par la page Analyser.")
        st.page_link(PAGES["analyser"], label="Analyser des images", icon=":material/center_focus_strong:")
        return
    k = st.columns(4)
    k[0].metric("Images analysées", len(history))
    k[1].metric("Obstacles signalés", sum(r["obstacles"] for r in history))
    k[2].metric("Images avec obstacle", sum(1 for r in history if r["obstacles"]))
    k[3].metric("Temps moyen par image", f"{sum(r['latency_ms'] for r in history) / len(history):.0f} ms")
    st.dataframe(pd.DataFrame([{"Image": r["image"], "Mode": r["mode"], "Obstacles": r["obstacles"],
                                "Surface signalée": r["flagged_percent"], "Analysée le": r["analysed_at"]}
                               for r in history]),
                 hide_index=True, width="stretch",
                 column_config={"Surface signalée": st.column_config.NumberColumn(format="%.1f %%")})
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    csv_col, html_col = st.columns(2)
    csv_col.download_button("Télécharger le tableau (CSV)", findings.report_csv(history),
                            file_name=f"roadanomaly_rapport_{stamp}.csv", mime="text/csv",
                            icon=":material/table_view:", width="stretch")
    html_col.download_button(
        "Télécharger le rapport illustré (HTML)",
        findings.report_html(history, plan.name, LOGO.read_bytes(), datetime.now().strftime("%d/%m/%Y à %H:%M")),
        file_name=f"roadanomaly_rapport_{stamp}.html", mime="text/html", icon=":material/description:",
        width="stretch")
    st.caption("Le rapport illustré s'ouvre dans un navigateur et s'imprime en PDF.")


def api_status():
    try:
        return httpx.get(f"{API_URL}/health", timeout=1.5).status_code == 200
    except httpx.HTTPError:
        return False


def integration():
    st.title("Intégration à vos systèmes")
    if not current_plan().api:
        locked("L'intégration par API", "api")
        st.markdown("**Programme pilote.** Deux à trois startups ADAS et laboratoires reçoivent la démo et l'API "
                    "gratuitement, en échange de leurs retours. Contactez l'équipe RoadAnomaly pour candidater.")
        return
    online = api_status()
    st.markdown(f"Service : `{API_URL}` · " + (":green[:material/check_circle: en ligne]" if online
                                                else ":orange[:material/error: hors ligne (lancez `mise run api`)]"))
    st.markdown("Envoyez une photo, recevez le masque des obstacles, les statistiques et, sur demande, "
                "l'explication. Choisissez le mode avec le paramètre `model` :")
    st.dataframe(pd.DataFrame([{"Mode": m.name, "model": m.model} for m in offer.MODES.values()]),
                 hide_index=True)
    curl, python = st.tabs(["curl", "Python"])
    curl.code(f'curl -F "file=@photo.jpg" "{API_URL}/predict?model={offer.MODES["max"].model}&include_images=false"',
              language="bash")
    python.code(f"""import httpx

with open("photo.jpg", "rb") as f:
    r = httpx.post("{API_URL}/predict", params={{"model": "{offer.MODES['sobre'].model}"}},
                   files={{"file": f}}, timeout=60)
stats = r.json()["stats"]          # anomaly_percent, blobs, latency_ms...
mask_png = r.json()["mask_png"]    # obstacle mask, PNG in base64""", language="python")
    st.caption(f"Documentation interactive de l'API : {API_URL}/docs. Intégration embarquée : sur devis (bêta).")


def offres():
    st.title("Offres")
    st.markdown("Une tarification adaptée à la taille de votre organisation et au volume d'images analysées. "
                "Commencez gratuitement, sans engagement.")
    for col, plan in zip(st.columns(len(offer.PLANS), gap="small"), offer.PLANS.values(), strict=True):
        with col.container(border=True, height="stretch"):
            st.markdown(f"<div class='ra-plan'>{plan.name}</div><div class='ra-audience'>{plan.audience}</div>"
                        f"<div class='ra-price'>{plan.price_label}</div>", unsafe_allow_html=True)
            st.markdown("\n".join(f"- {p}" for p in plan.perks))
            current = st.session_state["plan"] == plan.key
            if st.button("Offre actuelle" if current else f"Choisir {plan.name}", key=f"plan:{plan.key}",
                         disabled=current, type="secondary" if current else "primary", width="stretch"):
                st.session_state["plan"] = plan.key
                st.rerun()
    st.markdown("**Réductions** : abonnement annuel et gros volumes. **Programme pilote** : démo et API gratuites "
                "pour deux à trois startups et laboratoires.")
    st.caption("Démonstration : le choix d'une offre est simulé, aucun paiement n'est demandé.")


def guide():
    st.title("Guide d'utilisation")
    steps = st.columns(3, gap="large")
    steps[0].markdown("##### 1 · Importez\nDes photos prises depuis la route (caméra embarquée, inspection, "
                      f"smartphone). Jusqu'à {offer.MAX_IMAGES_PER_RUN} images par lancement.")
    steps[1].markdown("##### 2 · Choisissez le mode\n**Détection maximale** pour ne rien manquer, **peu de fausses "
                      "alarmes** quand une alerte inutile coûte cher.")
    steps[2].markdown("##### 3 · Lisez le résultat\nChaque obstacle est surligné en orange, encadré et numéroté. "
                      "« Pourquoi ce signalement ? » montre ce qui a déclenché l'alerte.")
    st.divider()
    st.subheader("Ce que RoadAnomaly fait différemment")
    st.markdown("""
- **Pas de liste fermée d'objets.** Les systèmes ADAS reconnaissent ce qu'on leur a appris (voiture, piéton,
  panneau). RoadAnomaly signale **tout ce qui ne ressemble pas à une route normale**, même un objet jamais vu.
- **Au pixel près.** Le résultat est un masque : vous voyez la forme et la taille de l'obstacle, pas seulement
  une boîte.
- **Avec une explication.** Une carte de chaleur montre où le modèle a regardé ; un graphique dit si l'alerte
  vient de l'obstacle lui-même, de sa couleur, de son contraste ou de la scène autour.
""")
    st.subheader("Les deux modes, chiffres de nos tests")
    for m in offer.MODES.values():
        st.markdown(f"- **{m.name}** : {m.use_when} {offer.tested_sentence(m)}")
    st.subheader("Limites, en toute transparence")
    t = offer.tested(offer.MODES["max"])
    test_set = f"**{t['photos']} photos de test ({t['obstacles']} obstacles)**" if t else "**un petit jeu de test**"
    st.markdown(f"""
- RoadAnomaly est un **outil d'aide à la décision** : un signalement se vérifie, il ne commande pas un véhicule.
- Les chiffres viennent de {test_set}, tenues à l'écart pendant tout le développement :
  ils donnent un ordre de grandeur, pas une garantie.
- Le modèle a appris sur un petit nombre de photos de routes : une scène très différente (nuit, neige, pluie
  forte) peut dégrader le résultat. La vidéo se traite image par image.
- La position est donnée **dans l'image** (gauche, centre, droite ; premier plan, arrière-plan), pas en mètres.
- Vos images sont analysées en mémoire et **ne sont pas enregistrées** sur disque.
""")
    st.subheader("Support")
    st.markdown("Documentation en ligne pour tous ; e-mail (Bronze), prioritaire (Silver), accompagnement "
                "personnalisé (Gold).")


# ------------------------------------------------------------------ shell
init_session()
PAGES = {
    "analyser": st.Page(analyser, title="Analyser", icon=":material/center_focus_strong:", default=True),
    "rapport": st.Page(rapport, title="Rapport", icon=":material/summarize:"),
    "integration": st.Page(integration, title="Intégration", icon=":material/api:"),
    "offres": st.Page(offres, title="Offres", icon=":material/workspace_premium:"),
    "guide": st.Page(guide, title="Guide", icon=":material/menu_book:"),
}
navigation = st.navigation(list(PAGES.values()), position="top")

navigation.run()

# the account panel is drawn after the page, so the quota includes the images analysed in this run
with st.sidebar:
    st.image(str(LOGO), width="stretch")
    st.markdown(f"<p class='ra-tagline'>{TAGLINE}</p>", unsafe_allow_html=True)
    st.markdown("**Mon espace**")
    plan = current_plan()
    st.markdown(f"Offre **{plan.name}** · {plan.price_label}")
    left = remaining_images()
    if left is None:
        st.progress(1.0, text="Images illimitées")
    else:
        st.progress(min(st.session_state["used"] / plan.monthly_images, 1.0),
                    text=f"{st.session_state['used']} / {plan.monthly_images} images utilisées")
    st.page_link(PAGES["offres"], label="Changer d'offre", icon=":material/workspace_premium:")
    st.divider()
    st.caption("Version MVP. Outil d'aide à la décision : vérifiez toujours un signalement.")
