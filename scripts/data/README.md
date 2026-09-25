# Data Preparation Scripts

The `scripts/data/` directory provides utilities for audio dataset preparation, stratified subsampling, and manifest generation for large-scale experimental verification.

---

## Script Catalog

### `sample_musan_subset.py`
Performs stratified random sampling of the MUSAN audio corpus for Phase-2B real-audio basin transfer experiments.

**Features:**
- Samples at a specified ratio (default: 25% or 10%) across subcategories (speech, music, noise).
- Preserves acoustic distribution and balance across categories.
- Fixed random seed (`--seed 42`) guarantees 100% deterministic reproducibility.
- Exports `subset_manifest.tsv` with relative paths and byte sizes for auditing.
- Optional compression to a `.zip` archive.

**Usage:**
```bash
# 1. Extract a 25% stratified subset:
python scripts/data/sample_musan_subset.py \
    --src-root /path/to/musan \
    --dst-root data/musan_25 \
    --ratio 0.25 \
    --seed 42 \
    --zip-path data/musan_25.zip

# 2. Extract a 10% stratified subset:
python scripts/data/sample_musan_subset.py \
    --src-root /path/to/musan \
    --dst-root data/musan_10 \
    --ratio 0.10 \
    --seed 42
```
