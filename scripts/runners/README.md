# Execution Pipeline Runners

The `scripts/runners/` directory provides end-to-end automation pipelines for full experimental reproduction. These runners are ideal for headless execution on compute workstations, servers, or cloud environments without manual notebook interaction.

---

## Runner Catalog

### `run_full_pipeline.py`
Automates the full experimental reproduction pipeline:
1. **Environment Verification:** Executes `run_tests.py` to ensure all unit tests pass before launching computational runs.
2. **Environment Provenance:** Records Python version and pip package freeze (`environment_info.txt`).
3. **Phase 1D:** Online Ritz dominant-edge tracking.
4. **Phase 1E-R:** Contraction rate realization and horizon policy analysis.
5. **Phase 2A:** Synthetic signal-scale transfer.
6. **Phase 2B Checkpointed:** Real-audio basin sweep with batch chunking, automatic resumption, and deadline control.
7. **Phase 1C Verification:** Controlled multi-STFT grid sweep verification.
8. **Integrity Audit & Packaging:** Verifies output files and generates a compressed `.zip` results bundle.

**Usage:**
```bash
# 1. Run the complete pipeline:
python scripts/runners/run_full_pipeline.py \
    --audio-dir data/audio_samples \
    --out-dir results/pipeline_runs \
    --run-pilot --batch-size 2 --zip-bundle

# 2. Run only Phase 2B (skipping synthetic Phases 1D, 1E-R, 2A):
python scripts/runners/run_full_pipeline.py \
    --audio-dir data/audio_samples \
    --out-dir results/pipeline_runs \
    --skip-phase1-phase2a --batch-size 2
```
