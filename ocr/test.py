import argparse

from gif import GifManager
from image_annotator import annotate_images


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-g", "--gif", required=True)
    args = ap.parse_args()

    gm = GifManager(args.gif)
    print("Saved:", gm.save_thumb())

    print(annotate_images(gm.images))
