"""GPU setup shared by all notebooks.

The team trains on two cards: RTX 4060 (8 GB, Ada sm_89) and RTX 2060 (6 GB, Turing sm_75).
The 2060 is the reference: image size and batch size must fit in 6 GB.
Turing supports float16 mixed precision but NOT bfloat16, so only "mixed_float16" is offered.
"""
import tensorflow as tf


def setup_gpu(mixed_precision=False):
    """Enable memory growth on every GPU, print what is available and return the GPU name."""
    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        print("No GPU found: running on CPU")
        return "CPU"

    # Allocate VRAM on demand instead of grabbing all of it at start-up
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

    details = tf.config.experimental.get_device_details(gpus[0])
    name = details.get("device_name", "GPU")
    print("GPU:", name, "| compute capability:", details.get("compute_capability"))

    if mixed_precision:
        # float16 works on both cards; bfloat16 would fail on the RTX 2060
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        print("Mixed precision policy: mixed_float16")
    return name
