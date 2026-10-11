from datasets import load_dataset
import datasets
from pathlib import Path


def main() -> None:
    datasets.logging.set_verbosity_error()

    # Existing HF cache locations
    CACHE_INTERACTIONS_DIR = "D:/hf_datasets"              # has 0core_timestamp_w_his_Electronics
    CACHE_META_DIR = "D:/IIMA/Amazon Reviews"              # has raw_meta_Electronics etc.

    OUT_DIR = Path("D:/IIMA/Amazon Reviews/amazon_electronics_processed")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Interactions with history – use D:/hf_datasets
    interactions_hf = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "0core_timestamp_w_his_Electronics",
        trust_remote_code=True,
        cache_dir=CACHE_INTERACTIONS_DIR,
    )

    for split in ["train", "valid", "test"]:
        ds_split = interactions_hf[split]
        out_dir = OUT_DIR / f"electronics_interactions_{split}"
        print(f"Writing {split} split to Parquet at {out_dir} ...")
        ds_split.to_parquet(str(out_dir))
        print(f"Finished {split} split.")

    # 2) Item metadata – use D:/IIMA/Amazon Reviews
    meta_hf = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_meta_Electronics",
        split="full",
        trust_remote_code=True,
        cache_dir=CACHE_META_DIR,
    )

    items_out_dir = OUT_DIR / "electronics_items"
    print(f"Writing item metadata to Parquet at {items_out_dir} ...")
    meta_hf.to_parquet(str(items_out_dir))
    print("Finished item metadata.")

    print("All Parquet exports completed.")
    print("Output directory:", OUT_DIR)


if __name__ == "__main__":
    main()