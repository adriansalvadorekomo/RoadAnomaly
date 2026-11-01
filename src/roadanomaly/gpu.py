"""GPU setup shared by all notebooks, scripts and the deployment.

The team trains on two cards: RTX 4060 (8 GB, Ada sm_89) and RTX 2060 (6 GB, Turing sm_75).
The 2060 is the reference: image size and batch size must fit in 6 GB.
Turing supports float16 mixed precision but NOT bfloat16, so only "mixed_float16" is offered.
"""
import tensorflow as tf


def setup_gpu(mixed_precision=False, memory_limit_mb=None):
    """Configure the first GPU, print what is available and return its name ("CPU" without a GPU).

    - default: memory growth (VRAM allocated on demand instead of all of it at start-up);
    - memory_limit_mb: a hard cap for this process instead, so several processes (the API and the
      demo, or a notebook next to them) can share one card; cuDNN otherwise grows a single
      inference process to several GB while autotuning.
    Must run before TensorFlow touches the GPU.
    """
    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        print("No GPU found: running on CPU")
        return "CPU"

    try:
        if memory_limit_mb:
            tf.config.set_logical_device_configuration(
                gpus[0], [tf.config.LogicalDeviceConfiguration(memory_limit=int(memory_limit_mb))])
        else:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError:
        pass   # the GPU was already initialised in this process: keep its configuration

    details = tf.config.experimental.get_device_details(gpus[0])
    name = details.get("device_name", "GPU")
    limit = f" | memory limit {int(memory_limit_mb)} MB" if memory_limit_mb else ""
    print("GPU:", name, "| compute capability:", details.get("compute_capability"), limit)

    if mixed_precision:
        # float16 works on both cards; bfloat16 would fail on the RTX 2060
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        print("Mixed precision policy: mixed_float16")
    return name
