"""Hand-computed cases for the shared metrics, the post-processing and the evaluation report."""
import numpy as np
import pytest

from roadanomaly import evaluation, metrics, postprocessing


def test_segmentation_scores_match_hand_computation():
    # DL notes, Cap. 10.7: prediction 80 px, truth 100 px, overlap 60 px -> IoU 0.5, Dice 0.667
    truth = np.zeros(200, np.uint8); truth[:100] = 1
    pred = np.zeros(200, np.uint8); pred[40:120] = 1
    scores = metrics.segmentation_scores(truth, pred)
    assert scores["iou"] == pytest.approx(0.5) and scores["dice"] == pytest.approx(120 / 180)
    assert metrics.segmentation_scores(truth, truth)["iou"] == 1.0
    assert metrics.segmentation_scores(truth, 1 - truth)["dice"] == 0.0
    assert metrics.segmentation_scores(np.zeros(5), np.zeros(5))["f1"] == 1.0


def test_object_scores_ignore_speckle():
    # a 36 px object half covered, a 9 px object missed, a 1 px speckle ignored, one false alarm
    gt = np.zeros((20, 20), np.uint8); gt[2:8, 2:8] = 1; gt[12:15, 12:15] = 1; gt[0, 19] = 1
    pred = np.zeros_like(gt); pred[2:8, 2:6] = 1; pred[16:20, 0:4] = 1
    o = metrics.object_scores(gt, pred, min_size=4)
    assert (o["gt_objects"], o["detected"], o["pred_objects"], o["false_alarms"]) == (2, 1, 2, 1)


def test_aupro_of_a_perfect_map_is_one():
    gt = np.zeros((1, 20, 20), bool); gt[0, 5:10, 5:10] = True
    assert metrics.aupro(list(gt), list(gt.astype(float)), min_size=4) == pytest.approx(1.0, abs=1e-6)


def test_bootstrap_is_deterministic_and_brackets_the_mean():
    values = [0.1, 0.5, 0.9, 0.4]
    assert metrics.bootstrap_ci(values) == metrics.bootstrap_ci(values)
    mean, low, high = metrics.bootstrap_ci(values)
    assert low <= mean <= high


def test_per_image_z_score():
    maps = np.random.default_rng(0).random((3, 8, 8)) * 10 + 5
    z = postprocessing.standardise_per_image(maps)
    assert np.allclose(z.mean(axis=(1, 2)), 0, atol=1e-5) and np.allclose(z.std(axis=(1, 2)), 1, atol=1e-4)


def test_upsample_keeps_full_size_maps_and_resizes_cells():
    assert postprocessing.upsample(np.zeros((1, 352, 640))).shape == (1, 352, 640)
    assert postprocessing.upsample(np.zeros((2, 22, 40))).shape == (2, 352, 640)


def test_to_masks_removes_small_blobs():
    scores = np.zeros((1, 10, 10)); scores[0, 0, 0] = 5; scores[0, 4:8, 4:8] = 5
    masks = postprocessing.to_masks(scores, threshold=1, min_blob=4)
    assert masks[0, 0, 0] == 0 and masks[0, 4:8, 4:8].all()


def test_select_threshold_finds_the_separating_value():
    gt = np.zeros((2, 10, 10), bool); gt[:, 2:6, 2:6] = True
    scores = gt.astype(float) + np.random.default_rng(0).random(gt.shape) * 0.1
    threshold, _, f1, _ = postprocessing.select_threshold(gt, scores, quantiles=np.linspace(0.5, 0.99, 50))
    assert f1 == 1.0 and 0.1 <= threshold <= 1.0


def test_report_of_a_perfect_prediction():
    gt = np.zeros((2, 16, 16), bool); gt[:, 4:10, 4:10] = True
    report = evaluation.mask_report(gt, gt.astype(np.uint8))
    assert report["pixel"]["per_image_mean"]["f1"] == 1.0
    assert report["objects"]["false_alarms"].sum() == 0 and report["confusion"]["fp"] == 0
    free = evaluation.threshold_free_scores(gt, gt.astype(float))
    assert free["AuPRC"] == pytest.approx(1.0) and free["AUROC"] == pytest.approx(1.0)
    row = evaluation.summary(free, report)
    assert row["objects detected"] == "2/2"


def test_boundary_metrics():
    gt = np.zeros((40, 40), bool); gt[10:30, 10:30] = True
    assert metrics.boundary_iou(gt, gt, band=3) == 1.0 and metrics.hd95(gt, gt) == 0.0
    shifted = np.roll(gt, 2, axis=1)
    assert 0 < metrics.boundary_iou(gt, shifted, band=3) < 1
    assert metrics.hd95(gt, shifted) == pytest.approx(2.0)
    assert np.isnan(metrics.hd95(gt, np.zeros_like(gt))) and metrics.hd95(np.zeros_like(gt), np.zeros_like(gt)) == 0.0


def test_fpr95():
    gt = np.array([0, 0, 0, 0, 1, 1], bool)
    assert evaluation.fpr_at_tpr(gt, np.array([0, .1, .2, .3, .8, .9])) == 0.0      # perfect separation
    assert evaluation.fpr_at_tpr(gt, np.array([.5, .6, .7, .95, .8, .9])) == 0.25   # one background above
