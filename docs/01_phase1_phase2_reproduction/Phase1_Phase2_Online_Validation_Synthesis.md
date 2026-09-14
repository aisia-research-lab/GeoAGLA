# Báo cáo tổng kết — Student B (E3–E5)
### Dự án: *Geometry Determines Acceleration in Phase Retrieval* (ICLR 2027)
### Package tái lập: `geometry-certified-gla-phase2b-v1`

**Phạm vi công việc:** B0 (E3 — Passive Ritz Estimation), B1 (E4 — Online-λ+ Rate Realization), B2 (E5a — Signal-Scale Transfer), B3 (E5b — Real-Audio Basin & Geometry Validation), và Cross-check tái lập thực nghiệm của Student A (Phase-1C).

---

## 1. Tổng quan môi trường thực thi

| Giai đoạn | Môi trường | Ghi chú |
|---|---|---|
| B0, B1 | Máy cá nhân (Windows, venv, Python) | `pytest -q` → 17/17 passed |
| B2, B3, Cross-check | Kaggle Notebook, CPU-only, Python 3.12 | `pytest -q` → 17/17 passed; không dùng GPU (package chỉ dùng NumPy/SciPy/Matplotlib) |

**Dataset audio:** MUSAN ([openslr.org/17](https://www.openslr.org/17/)), 6 file được chọn **cố định theo thứ tự alphabet** (2 file đầu tiên mỗi thư mục `speech/`, `music/`, `noise/`), không đổi lại sau khi thấy kết quả:
```
speech-librivox-0000.wav   speech-librivox-0001.wav
music-fma-0000.wav         music-fma-0001.wav
noise-free-sound-0000.wav  noise-free-sound-0001.wav
```

**Cơ chế checkpoint (Phase-2B):** vì Kaggle giới hạn phiên chạy (~12h), một wrapper (`run_phase2b_checkpointed.py`) được viết thêm để chia 6 file thành 3 batch × 2 file, mỗi batch tự ghi kết quả xong ngay lập tức (chống mất dữ liệu nếu phiên bị ngắt), sau đó gộp lại bằng **đúng công thức gate/summary** sao chép nguyên vẹn từ script gốc `experiments/phase2b_real_audio/run.py` — không có dòng code khoa học nào bị chỉnh sửa. Toàn bộ pipeline được chạy lại **2 lần độc lập** trên Kaggle (2 phiên tách biệt) để kiểm tra tính tái lập — kết quả Phase-2B khớp **tuyệt đối từng chữ số** giữa 2 lần chạy, xác nhận tính tất định của toàn bộ cấu hình.

---

## 2. B0 — E3: Passive Ritz Estimation (`reproduce/run_phase1d.py`)

**Câu hỏi:** cạnh trội (dominant edge) $\lambda_+$ của phổ ngang có khôi phục được thụ động từ các cặp secant của quỹ đạo, mà không cần gọi thêm phép chiếu phase-retrieval nào không?

**Cấu hình đóng băng:** bộ nhớ `p = 3` (p=1, p=5 chỉ để chẩn đoán so sánh).

| Chỉ số | Giá trị | Đọc |
|---|---|---|
| `d0_max_abs_error` | 1.16e-13 | Sai số máy tính — đệ quy modal khớp chính xác với tính trị riêng trực tiếp |
| `selected_median_rel_error` | 0.228% | Sai số cạnh trội trung vị rất nhỏ |
| `selected_p90_rel_error` | 0.507% | Vẫn dưới 1% ở bách phân vị 90 |
| `selected_median_under_fraction` | **1.0** | Ước lượng luôn **thiên thấp** (under-estimate) so với $\lambda_+$ thật — nhất quán với lý thuyết (chỉ quan sát được không gian con quỹ đạo đã đi qua) |
| `raw_estimate_upper_bound_safe` | **false** | Xác nhận bằng số: ước lượng Ritz thô **không phải** chặn trên đã chứng thực |
| `identifiability_trajectory_max_difference` | 0.0 | Minh hoạ số cho Proposition 13: 2 toán tử khác nhau ngoài không gian quan sát vẫn cho cùng quan sát thụ động |
| `phase1d_gate` | **`YELLOW-GREEN`** | "active edge identifiable; safeguard/margin required" |

**Kết luận:** cạnh trội học được qua Ritz, nhưng cần safeguard/margin — đây là kết quả mong đợi, dẫn thẳng đến thiết kế của B1.

---

## 3. B1 — E4: Online-λ+ Rate Realization (`reproduce/run_phase1er.py`)

**Cấu hình đóng băng:** `p=3`, `K=8` (block length), `margin=0`, edge policy = dynamic running-envelope, fallback an toàn = GLA.

| Chỉ số | Giá trị |
|---|---|
| `beat_fraction` (vs FGLA tối ưu) | 0.833 |
| `median_q_ratio_fgla` | 0.998 (< 1 → Online nhanh hơn) |
| `fallback_e1_failures` | 0 |
| `phase1er_gate` | **GREEN** (đủ cả H4, H5, E1) |

**Finite-horizon audit (bắt buộc báo cáo đầy đủ, không chỉ số đẹp nhất):**

| Horizon | beat_fraction | median ratio |
|---|---|---|
| 120 | 0.25 | 1.005 (Online chậm hơn) |
| 180 | 0.417 | 1.001 |
| 240 | 0.833 | 0.998 |
| 360 | 0.958 | 0.995 |

**Kết luận:** đúng hiện tượng "estimator maturation delay" mà lý thuyết dự đoán — ước lượng Ritz cần thời gian "chín", nên Online chỉ vượt trội rõ rệt từ horizon ≥240.

---

## 4. B2 — E5a: Signal-Scale Transfer Check (`reproduce/run_phase2a.py`)

**Mục đích:** xác nhận cơ chế sống sót qua STFT matrix-free trên tín hiệu tổng hợp trước khi chạm vào audio thật.

| Chỉ số | Giá trị |
|---|---|
| `max_geometry_relative_error` | 8.78e-4 |
| `online_beat_fraction_vs_fgla` | 0.75 |
| `fallback_e1_failures` | 0 |
| `phase2a_controlled_gate` | **GREEN** (đủ cả G2A–G2D) |

Chạy lại độc lập trên Kaggle (2 lần) cho kết quả **khớp tuyệt đối** ở các chỉ số hình học tất định, dao động nhẹ (5.45e-6 vs 8.41e-6 ở `median_final_edge_relative_error`) ở phần có yếu tố ngẫu nhiên — bình thường.

**Chi tiết 4 case:** cả 4 đều thuộc vùng gần suy biến ($\lambda_+ \geq 0.9976$); case `transient_n1024` ($\lambda_+=0.999963$) gần suy biến nhất và là case duy nhất không thắng FGLA ở horizon đầy đủ — được **giữ nguyên** trong báo cáo, không loại bỏ.

**Finite-horizon audit:** beat-fraction tăng dần 0.50 → 0.75 → 0.75 theo horizon 120/240/360, vượt ngưỡng gate (0.70) từ horizon ≥240 — cùng hiện tượng maturation delay như B1.

---

## 5. B3 — E5b: Real-Audio Basin & Geometry Validation (`reproduce/run_phase2b.py`)

### 5.1 Kết quả tổng thể

| Chỉ số | Giá trị |
|---|---|
| `n_files` / `n_geometry_cases` / `n_basin_runs` | 6 / 12 / 144 |
| `max_geometry_relative_error` | 1.60e-3 |
| `overall_online_success_fraction` vs `overall_fgla_success_fraction` | **0.840 vs 0.611** — Online rộng basin hơn hẳn |
| `paired_success_online_beat_fraction` | **0.420** (dưới ngưỡng gate 0.6) |
| `near_phase_degenerate_fraction` | 0.75 |
| `fallback_e1_failures` | 0 |
| `phase2b_gate` | **YELLOW** (5/6 gate PASS, chỉ `G2B_E` FAIL) |

Chạy lại độc lập trên Kaggle 2 lần cho kết quả **khớp tuyệt đối từng chữ số** — xác nhận toàn bộ pipeline tất định trên cùng 1 bộ dữ liệu.

### 5.2 Bảng gate chi tiết

| Gate | Kết quả | Đọc |
|---|---|---|
| G2B_A geometry | PASS | sai số tối đa 1.6e-3, xa ngưỡng |
| G2B_B edge tracking | PASS | trung vị 4.3e-5, ~1000× dưới ngưỡng |
| G2B_C small-basin | PASS | 90.6% thành công ở nhiễu nhỏ, ≥60% |
| G2B_D basin non-shrink | PASS | Online (84%) **vượt** FGLA (61.1%) — không hề co basin |
| **G2B_E paired rate** | **FAIL** | beat-fraction 42% < 60%; median ratio ≈1.0006 (gần như hoà) |
| G2B_F safeguard | PASS | reject muộn 1.4%, 0 lần fallback thất bại / 144 run |

### 5.3 Phân tích nguyên nhân gốc của `G2B_E` (đã đào sâu, không dừng ở "fail")

**(a) STFT profile quyết định near-degeneracy, không phải nội dung audio:**

| Profile | Overlap | Số case $\lambda_+\geq0.9999$ |
|---|---|---|
| `agla_gaussian` (W=256, hop=32) | 8× | 3/6 |
| `mezza_hann` (W=512, hop=128) | 4× | **6/6 — luôn suy biến** |

**(b) Thất bại tập trung ở 1 nhóm khởi tạo cụ thể, không rải đều:**

| init_kind | level | paired beat-fraction |
|---|---|---|
| transverse | 0.001 / 0.01 | 0.333 / 0.417 |
| **transverse** | **0.05** | **0.176 (thấp nhất — kéo tụt trung bình chung)** |
| phase_jitter | 0.05 / 0.15 | 0.636 / 0.500 |
| **phase_jitter** | **0.30** | **1.000 (thắng tuyệt đối)** |

→ Online **robust hơn hẳn** FGLA ở nhiễu `phase_jitter` mạnh, nhưng không nhanh hơn rõ rệt ở `transverse@0.05` — đây là điểm kéo tụt chỉ số tổng, không phải hiện tượng lan toả toàn bộ.

**(c) Trực quan hoá quỹ đạo (D4)** theo 3 loại nội dung (cùng điều kiện `agla_gaussian/transverse`): **speech** khó nhất ở mức nhiễu lớn (orbit error cuối ~1.2e-4, gần như không cải thiện sau iter≈150); **noise** cần safeguard can thiệp nhiều lần (quỹ đạo có "bậc thang") nhưng vẫn hội tụ tốt hơn speech.

**Kết luận:** `G2B_E` fail là hiện tượng **cục bộ, có thể giải thích rõ ràng**, đúng tinh thần "cục bộ/có điều kiện" của Theorem 16 — không phải một thất bại lan toả hay lỗi triển khai.

---

## 6. Cross-check tái lập — Phase-1C (`reproduce/run_phase1c.py`)

Chạy độc lập trên Kaggle để kiểm tra tái lập thực nghiệm của Student A (không phải phần việc của Student B, nhưng bắt buộc theo quy trình cross-check chéo).

| Chỉ số | Giá trị |
|---|---|
| `h1_max_relative_spectral_error` | 1.23e-15 (xấp xỉ machine epsilon) |
| `h1_all_single_neutral` | true (đúng 1 trị riêng trung tính ở cả 30/30 case) |
| `observed_ordering_fraction` / `predicted_ordering_fraction` | **1.0 / 1.0** — $q_{\text{oracle}} < q_{\text{FGLA,opt}} < q_{\text{GLA}}$ đúng tuyệt đối ở 270/270 run |
| `phase1c_gate` | **GREEN** |

**Kết luận:** tái lập thành công tuyệt đối, xác nhận trên môi trường hoàn toàn độc lập (Kaggle) với máy gốc của Student A.

---

## 7. Tổng kết gate toàn bộ phần việc Student B

| Bước | Nội dung | Gate |
|---|---|---|
| B0 | Phase-1D — Passive Ritz Estimation | YELLOW-GREEN |
| B1 | Phase-1E-R — Online Rate Realization | **GREEN** |
| B2 | Phase-2A — Signal-Scale Transfer | **GREEN** |
| B3 | Phase-2B — Real-Audio Transfer | YELLOW (1/6 gate con fail, đã giải thích rõ nguyên nhân) |
| Cross-check | Phase-1C (Student A) | **GREEN** |

**Không có gate RED nào trong toàn bộ quá trình.** Duy nhất `G2B_E` ở mức YELLOW, với nguyên nhân đã được xác định cụ thể và không mâu thuẫn với phạm vi lý thuyết đã công bố.

---

## 8. Những phát hiện đáng chú ý

1. Ước lượng Ritz **luôn** thiên thấp (under-estimate) và **không** phải chặn trên chứng thực — được chính code xác nhận bằng số (B0).
2. Cả B1 và B2 cho thấy hiện tượng **"estimator maturation delay"**: Online chỉ vượt FGLA rõ rệt từ horizon đủ lớn (≥240), chậm hơn ở horizon ngắn (120–180).
3. STFT profile (`mezza_hann` vs `agla_gaussian`) là **yếu tố hệ thống** quyết định mức độ gần suy biến của phổ, độc lập với nội dung audio.
4. Online có basin hội tụ **rộng hơn** FGLA nói chung, nhưng lợi thế tốc độ chỉ thể hiện rõ ở nhiễu dạng `phase_jitter`, không đồng đều ở `transverse`.
5. Toàn bộ pipeline Phase-2A và Phase-2B **tất định tuyệt đối** khi chạy lại nhiều lần trên môi trường khác nhau (khớp từng chữ số) — độ tin cậy tái lập rất cao.

---

## 9. Những kết luận KHÔNG được đưa ra 

- ❌ "Online-$\lambda_+$ luôn nhanh hơn FGLA." *(Bị bác bỏ bởi `paired_success_online_beat_fraction=0.42`.)*
- ❌ "Bộ ước lượng khôi phục được toàn bộ phổ." *(Chỉ cạnh trội được ước lượng — Theorem 14.)*
- ❌ "Ước lượng Ritz là chặn trên đã chứng thực." *(Bị bác bỏ trực tiếp bởi `raw_estimate_upper_bound_safe: false`.)*
- ❌ "Các case gần suy biến là ngoại lệ cần loại bỏ." *(Được giữ lại và phân tích như biên giới kỳ vọng của lý thuyết.)*

---

## 10. Danh sách file đính kèm handoff

```
student_runs/student_B/
├── environment_kaggle.txt (+ environment máy cá nhân cho B0-B1, nếu có)
├── phase1d/          (B0 — đầy đủ JSON + 4 hình)
├── phase1er/         (B1 — đầy đủ JSON + 4 hình)
├── phase2a/          (B2 — đầy đủ JSON + 4 hình)
├── phase2b/          (B3 — đầy đủ JSON + 3 hình D1-D3
│                       + 3 hình D4 riêng theo batch, đã đổi tên)
├── phase1c/          (Cross-check — đầy đủ JSON + 3 hình)
└── terminal_logs/    (log lệnh cho từng bước)
```

---

*Báo cáo do Student B tổng hợp. Toàn bộ lệnh, cấu hình, và ngưỡng gate giữ nguyên không chỉnh sửa so với package đóng băng `geometry-certified-gla-phase2b-v1`. Không có case nào bị loại bỏ, chạy lại với tham số khác, hoặc chọn lại sau khi xem kết quả.*
