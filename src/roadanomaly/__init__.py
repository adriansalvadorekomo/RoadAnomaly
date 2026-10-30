"""Shared code for the RoadAnomaly project, imported by every binôme's notebook.

- data_pipeline : load frames + binary masks, split manifest, tf.data DataLoader
- metrics       : pixel-level segmentation metrics (Precision, Recall, F1, IoU, Dice)
- gpu           : GPU setup that works on both RTX 4060 (8 GB) and RTX 2060 (6 GB)
"""
