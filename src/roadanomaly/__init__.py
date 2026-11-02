"""Shared code for the RoadAnomaly project (CRISP-DM), imported by every notebook, script and app.

- protocol       : constants of the evaluation protocol (seed, resolution, object limits)
- data_pipeline  : paths, frame + binary mask loading, split manifest, tf.data DataLoader
- splitting      : how the frozen split was made, and its checks
- normal_regions : anomaly-free patches / feature cells for the autoencoders (Binôme B)
- postprocessing : score map -> anomaly mask (smoothing, per-image z-score, threshold)
- metrics        : pixel and object metrics, AUPRO, bootstrap intervals
- evaluation     : the shared evaluation report used for every model
- inference      : the shared model format (models/<name>/) and the Predictor
- xai            : the paired explanation: Grad-CAM++ / Grad-CAM on the predicted region (where) and exact
                   Shapley values over five image factors (what), plus the deletion / insertion check
- losses         : BCE + Dice, focal and focal-Tversky losses (Binôme C)
- gpu            : GPU setup that works on both RTX 4060 (8 GB) and RTX 2060 (6 GB)
- models         : one builder module per approach
"""
