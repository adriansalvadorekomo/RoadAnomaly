# Archive — earlier explorations (not part of the pipeline)

These files record how the final models were reached. They are kept **as they were run**, with their outputs, for traceability. They are **not** re-run, nothing in the pipeline imports from them, and their code may use older module names. The pipeline is in `notebooks/` (CRISP-DM phases 1–6) and `src/roadanomaly/`.

| File | Author | What it records | Used where |
|---|---|---|---|
| `A_deeplabv3plus_original_run_ines.ipynb` | Ines | Original DeepLabV3+ run (Windows, CPU, TF 2.21), including its own test evaluation, Seg-Grad-CAM and deletion / insertion; local paths replaced by `<local checkout>` | Reproduced in `notebooks/4_Modeling/A_DeepLabV3Plus.ipynb`; XAI moved to `notebooks/6_XAI.ipynb` |
| `B_feature_ae_and_backbone_study_adrian.ipynb` | Adrian | Pixel AE (v1), bottleneck search, feature-space AE (v2) with control experiments, and the comparison of 11 ImageNet backbones + a PaDiM-style Gaussian control (validation only) | Summarised in `notebooks/4_Modeling/B_Autoencoder.ipynb` (section 12) |
| `B_pixel_ae_loss_variants_khaled.ipynb` | Khaled | Pixel AE with MSE / MAE / MAE + VGG19 perceptual / SSIM losses, calibration on validation | Part 1 of `notebooks/4_Modeling/B_Autoencoder.ipynb` |
| `B_pixel_ae_final_evaluation_khaled.ipynb` | Khaled | Frozen-config evaluation of the pixel AE, Grad-CAM diagnostic | `notebooks/5_Evaluation.ipynb`, `notebooks/6_XAI.ipynb` |
| `B_pixel_ae_deployment_pipeline_khaled.ipynb` | Khaled | First inference pipeline (`AnomalyDetector`, config JSON) | Generalised to `src/roadanomaly/inference.py` (`Predictor`, shared model format) |
| `C_cnn_original_run_hejer.ipynb` | Hejer | Original PyTorch run (own category-based 40/10/10 split, 288×512): EDA, CNN baseline (val IoU 0.27), CNN + ImageNet ResNet18 encoder experiment (val IoU 0.56); test not used. `deep_learning1_cnn_final.ipynb`, an earlier subset of it, is not kept | Ported to Keras in `notebooks/4_Modeling/C_CNN_UNet.ipynb` (Part 1) |
| `C_unet_original_run_walid.ipynb` | Walid | Original PyTorch run (same split as Hejer): a small CNN (val IoU 0.28), a U-Net from scratch (val IoU 0.39, test 0.33) and a U-Net with an ImageNet ResNet34 encoder, focal + Tversky loss and flip-TTA (val IoU 0.815, test 0.731). The split is not group-aware, so near-duplicate scenes may cross it | Ported to Keras in `notebooks/4_Modeling/C_CNN_UNet.ipynb` (Parts 2–3; ResNet50 encoder) |
| `B_pixel_ae_train_script_khaled.py` | Khaled | Command-line training of the pixel AE | Training now runs in the modeling notebooks |

**Test-split usage recorded here** (disclosed in `notebooks/5_Evaluation.ipynb`):
- A original run: 1 evaluation.
- B pixel AE: 2 evaluations (ReLU code, linear code), plus Khaled's historical evaluation.
- B feature AE: 1 evaluation.
- C (Walid, on his own split): 2 evaluations (U-Net from scratch, U-Net ResNet34). Hejer: none.
