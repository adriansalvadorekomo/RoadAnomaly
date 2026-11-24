# Deployment

Moved here from the README unchanged: the API, the product, the demo, the landing page, Docker and the video script in detail.

## Deployment
- **API** (`deployment/api/main.py`, default model `A_deeplabv3plus`): `GET /health`, `GET /models`, `POST /predict` (image → mask, overlay, score map, statistics), `POST /explain?model=…&method=gradcampp|gradcam` (the paired explanation: a Grad-CAM++ / Grad-CAM heatmap as base64 PNG, and the exact Shapley value of each image factor with its efficiency check and a one-sentence summary). Interactive docs at `http://localhost:8000/docs`.
- **Product, the customer MVP** (`deployment/product/`, in French like the marketing deck; `mise run product`, :8502). The technical demo below is for the jury; the product is what a customer of the deck would use:
  - **Positioning** (deck slide 19, unexpected obstacles *with* an explanation): no closed list of objects, a pixel mask, and on demand "Pourquoi ce signalement ?" (a Grad-CAM++ heatmap and the exact SHAP factors, in plain French).
  - **The two modes of the targeting slide** (22): *Détection maximale* = DeepLabV3+ and *Peu de fausses alarmes* = the feature autoencoder. Each mode quotes its own test numbers, read from `reports/results/test_results.json` (20/22 obstacles found with 38 false alarms, against 16/22 with 10).
  - **The plans of slides 14–15**: free trial (20 images), Bronze 50 DT, Silver 200 DT, Gold 600 DT, with quotas and features gated by the plan (explanation and report from Silver, API integration in Gold). The plan choice is simulated: no account, no payment. Prices and features have one source, `deployment/product/offer.py`.
  - Pages: *Analyser* (batch upload or validation examples; obstacles in orange, framed, numbered and located in the image), *Rapport* (CSV for spreadsheets and an illustrated HTML report to print as PDF), *Intégration* (live status of the API and code samples), *Offres*, *Guide* (with its limits stated).
  - Brand: the team's logo (`assets/`, cropped above its tagline, which is set as text), navy for actions and orange only for the obstacles, as in the deck's visual identity; theme in `deployment/product/.streamlit/config.toml`. Tests: `tests/test_product.py`.
- **Demo** (`deployment/app/streamlit_app.py`): upload an image or pick a validation example, Detect (every model side by side), Explain (where + what for one model), Compare (detections and factor shares of all models), Test results and Method tabs. Theme in `.streamlit/config.toml`.
- **Landing page** (`deployment/landing/`, Astro): static page whose numbers are read from `reports/results/test_results.json` and `xai_summary.json` at build time.
- **Docker:** `docker compose -f deployment/docker-compose.yml up --build` starts the API, the demo, the product (:8502) and the landing page (CPU TensorFlow; `models/` mounted read-only).
- **Video:** `python scripts/infer_video.py video.mp4` (DeepLabV3+ by default, or `--model B_feature_ae`) writes an overlay video and prints the measured latency and FPS.

