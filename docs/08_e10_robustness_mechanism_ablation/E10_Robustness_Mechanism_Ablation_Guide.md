# Experiment 10: Online Robustness Mechanism Ablation Execution Guide

This package evaluates the mechanistic origins of Online adaptation's robustness advantage over FGLA ($+20.07$ percentage points, $74.94\%$ vs $54.87\%$) observed in the Phase-2B real-audio population.

The canonical Phase-2B preprocessing, initialization, STFT transforms, spectral geometry, FGLA minimax baseline, Ritz eigensolver, running-envelope policy, checkpoint safeguard, and GLA rollback are reused directly without alteration.

---

## 1. Scientific Variants

The six evaluated variants on exactly paired initializations and problems are:

1. **`fgla_oracle`**: Frozen optimal fixed-momentum FGLA parameter with true active dominant edge $\lambda_+$.
2. **`fixed_1e_oracle`**: Frozen one-edge minimax design $\Theta(0, \lambda_+)$.
3. **`online_raw`**: Passive $3 \times 3$ Ritz eigensolver estimate without running envelope and without checkpoint rollback.
4. **`online_env`**: Passive Ritz eigensolver with running-max envelope $\max_{t' \le t} \widehat{\lambda}_+(t')$, without rollback.
5. **`online_fallback`**: Passive Ritz raw edge with canonical checkpoint diagnostic and GLA rollback, without running-max envelope.
6. **`online_full`**: The canonical full Online policy combining both dynamic envelope and checkpoint rollback (`dynamic_envelope`).

All online variants retain the common safe GLA warmup (`warmup = 12`) required to populate passive secant history before eigensolver activation. The mechanistic ablation starts immediately after this shared warmup period.

---

## 2. Preflight Unit Verification

Before launching audio evaluations, run the preflight test suite:

```bash
python run_tests.py
```

The critical E10 test (`test_e10_full_switches_reproduce_canonical_online`) proves that `online_full` with both envelope and fallback active reproduces canonical `run_online_policy(..., policy='dynamic_envelope')` bit-for-bit to machine precision ($\text{diff} = 0.0$).

---

## 3. Local Smoke Test (2 Files)

To verify the paired ledger structure on a small subset:

```bash
python reproduce/run_e10_ablation.py \
  --audio-dir data/audio_samples \
  --out results/08_e10_robustness_mechanism_ablation_smoke \
  --max-files 2
```

Inspect `e10_run_ledger.csv`: every `run_key` must contain exactly six variant entries.

---

## 4. Full Frozen Execution (202 Files Population)

```bash
python reproduce/run_e10_ablation.py \
  --audio-dir /path/to/musan_202_wavs \
  --out results/08_e10_robustness_mechanism_ablation
```

- **Accounting**: Across the original Phase-2B population, 390 valid geometry cases $\times$ 6 initialization settings (3 transverse + 3 phase-jitter) $\times$ 2 random seeds yield **4,680 paired problem instances**.
- With 6 algorithm variants per problem instance, the complete run ledger contains **28,080 method rows**.

---

## 5. Clustered Bootstrap Analysis

```bash
python experiments/08_e10_robustness_mechanism_ablation/02_analyze_e10_ablation.py \
  results/08_e10_robustness_mechanism_ablation/e10_run_ledger.csv \
  --B 5000 --seed 20270920
```

Bootstrap resampling is clustered by source WAV audio file; all STFT profiles, initializations, seeds, and variants from any sampled audio source remain strictly together.

### Generated Deliverables:
1. `e10_run_ledger.csv`: Full 28,080-row execution ledger.
2. `e10_event_ledger.csv`: Block-by-block diagnostic and fallback events.
3. `e10_run_ledger.json`: Machine-readable JSON ledger.
4. `e10_success_summary.csv`: Overall success fraction and counts per variant.
5. `e10_contrasts.csv`: Paired contrast statistics (delta success, 95% bootstrap CI, rescue rate, loss rate, net rescue).

---

## 6. Scientific Discipline Rules

- `online_full` must reconcile with the frozen Phase-2B result ($74.94\%$).
- `fgla_oracle` must reconcile with the frozen FGLA result ($54.87\%$).
- No results may be interpreted if variant pairing is incomplete.
- Do not alter hyperparameters ($p=3, K=8$, warmup, checkpoint tolerances, horizons, STFT profiles, or initialization levels).
- Held-out MUSAN data is strictly forbidden during exploratory mechanism selection; it is reserved exclusively for a later pre-frozen confirmatory contrast.
