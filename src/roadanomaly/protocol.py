"""Constants of the shared evaluation protocol, written once for every notebook and script.

Each value comes from a measurement in notebook 2 (Data Understanding); the section that
justifies it is given next to it. Change a value here only together with that evidence.
"""

SEED = 1337                    # seed of every training run (Python, NumPy, TensorFlow)
IMG_SIZE = (352, 640)          # working resolution (height, width), notebook 2 section 7

# Objects (notebook 2, sections 6 and 10)
MIN_OBJECT_PX_FULL = 16        # annotation speckle limit at the original 1280x720 resolution
MIN_OBJECT_PX = 4              # the same limit at 352x640: 16 * (352 / 720) ** 2 is about 4 px
SMALL_OBJECT_PX = round(1000 * (IMG_SIZE[0] / 720) ** 2)   # "small" = under 1000 px at full resolution
OBJECT_OVERLAP = 0.5           # an object counts as detected when at least half of it is predicted

# Threshold-free metrics (notebook 2, section 10)
FPR_LIMIT = 0.3                # integration limit of AUPRO, always reported with the score

# Boundary quality (FR section 10): Boundary IoU band = 2 % of the image diagonal (Cheng et al., 2021)
BOUNDARY_BAND_PX = round(0.02 * (IMG_SIZE[0] ** 2 + IMG_SIZE[1] ** 2) ** 0.5)   # 15 px at 352x640

# Uncertainty on the 9-image test split (notebook 2, section 10, decision 8)
BOOTSTRAP_SAMPLES = 2000
BOOTSTRAP_ALPHA = 0.05
