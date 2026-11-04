"""Frame-by-frame anomaly detection on a video, with the measured latency and FPS (FR, section 6).

    python scripts/infer_video.py input.mp4 --model B_feature_ae --output reports/video/out.mp4
    python scripts/infer_video.py --frames data/raw/RoadAnomaly/frames --model A_deeplabv3plus

Each frame goes through the same Predictor as the notebooks and the API. The script reports what
it measured (mean / 95th percentile latency, FPS); it does not claim real time without that measure.
Without a video at hand, --frames builds a slideshow from a folder of images.
"""
import argparse
import sys
import time
from pathlib import Path

import imageio.v3 as iio
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # make `deployment` importable
from deployment import service  # noqa: E402


def frames_from(args):
    if args.frames:
        for path in sorted(Path(args.frames).glob("*.webp")) + sorted(Path(args.frames).glob("*.jpg")):
            yield iio.imread(path)[..., :3]
    else:
        yield from (frame[..., :3] for frame in iio.imiter(args.video))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", nargs="?", help="input video file")
    parser.add_argument("--frames", help="folder of images to use as frames instead of a video")
    parser.add_argument("--model", default=None, help=f"one of {service.model_names()} (default: {service.default_model()})")
    parser.add_argument("--output", default="reports/video/anomaly_overlay.mp4")
    parser.add_argument("--fps", type=float, default=10, help="frame rate of the output video")
    parser.add_argument("--max-frames", type=int, default=None)
    args = parser.parse_args()
    if not args.video and not args.frames:
        parser.error("give a video file or --frames")
    model = args.model or service.default_model()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    latencies, written = [], []
    for index, frame in enumerate(frames_from(args)):
        if args.max_frames and index >= args.max_frames:
            break
        start = time.perf_counter()
        result = service.analyse(model, frame)
        latencies.append(1000 * (time.perf_counter() - start))
        written.append(service.overlay(result["image"], result["mask"]))
    if not written:
        sys.exit("no frame read")
    iio.imwrite(output, np.stack(written), fps=args.fps, codec="libx264")

    steady = np.array(latencies[1:] or latencies)   # the first frame includes the model warm-up
    print(f"model {model}: {len(written)} frames -> {output}")
    print(f"latency per frame (pre-processing + model + post-processing): mean {steady.mean():.1f} ms, "
          f"95th percentile {np.percentile(steady, 95):.1f} ms -> {1000 / steady.mean():.1f} FPS "
          f"(first frame with warm-up: {latencies[0]:.0f} ms)")


if __name__ == "__main__":
    main()
