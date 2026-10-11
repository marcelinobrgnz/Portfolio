from datasets import load_dataset
import datasets

# Keep HF logs quiet
datasets.logging.set_verbosity_error()

# Store everything on D:
CACHE_DIR = "D:/hf_datasets"

# 1) Interactions with history (train/valid/test) – ELECTRONICS
interactions = load_dataset(
    "McAuley-Lab/Amazon-Reviews-2023",
    "0core_timestamp_w_his_Electronics",
    trust_remote_code=True,
    cache_dir=CACHE_DIR,
)

# 2) Item metadata – ELECTRONICS
meta = load_dataset(
    "McAuley-Lab/Amazon-Reviews-2023",
    "raw_meta_Electronics",
    split="full",
    trust_remote_code=True,
    cache_dir=CACHE_DIR,
)

# 3) (Optional) full reviews text – ELECTRONICS
reviews = load_dataset(
    "McAuley-Lab/Amazon-Reviews-2023",
    "raw_review_Electronics",
    trust_remote_code=True,
    cache_dir=CACHE_DIR,
)

print("Done. Cached in:", CACHE_DIR)