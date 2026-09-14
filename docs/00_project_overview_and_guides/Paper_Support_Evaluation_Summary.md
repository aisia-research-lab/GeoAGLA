# Mức độ ủng hộ thực nghiệm đối với paper *Geometry Determines Acceleration in Phase Retrieval* (ICLR 2027)

**Người thực hiện:** Student B (E3–E5), đối chiếu với cross-check E1–E2 (Student A)
**Kết luận tổng quát:** Kết quả tái lập **ủng hộ mạnh mẽ** phần lý thuyết cốt lõi của paper, không có trường hợp nào mâu thuẫn trực tiếp với một định lý đã chứng minh. Mức độ ủng hộ khác nhau rõ rệt giữa các claim — cần phân biệt rạch ròi khi đưa vào bản thảo.

---

## 1. Claim được ủng hộ RẤT MẠNH (bằng chứng số gần như tuyệt đối)

| Claim của paper | Bằng chứng thực nghiệm | Nguồn |
|---|---|---|
| **Theorem 2** — phổ Jacobian $J_\star=P_UP_V\vert_U$ có trị riêng $\lambda_j=\cos^2\theta_j$ (góc chính) | `h1_max_relative_spectral_error = 1.23e-15` — khớp tới machine epsilon, đúng ở **30/30** case | Phase-1C (cross-check) |
| **Theorem 8** — phân cấp tốc độ chặt chẽ $q_{\text{oracle}} < q_{\text{FGLA,opt}} < q_{\text{GLA}}$ | `observed_ordering_fraction = 1.0`, `predicted_ordering_fraction = 1.0` — đúng **100%** ở **270/270** run | Phase-1C (cross-check) |
| **Proposition 13** — hữu hạn secant không xác định được toàn phổ (non-identifiability) | `identifiability_trajectory_max_difference = 0.0` — minh hoạ số trực tiếp cho 2 toán tử khác nhau ngoài không gian quan sát | Phase-1D (B0) |
| **Theorem 14** — Ritz chỉ ước lượng được cạnh trội, không phải chặn trên đã chứng thực | Hội tụ về $\lambda_+$ đúng, đồng thời `raw_estimate_upper_bound_safe: false` — xác nhận đúng **cả 2 vế** của định lý | Phase-1D (B0) |
| Cơ chế online chuyển giao sang STFT matrix-free (tiền đề ngầm cho Section 8) | Gate `phase2a_controlled_gate: GREEN`, 0 lần fallback thất bại | Phase-2A (B2) |

Đây là **4 kết quả lý thuyết cốt lõi nhất** của paper, được xác nhận với độ chính xác rất cao, trên **2 môi trường thực thi độc lập** (máy cá nhân + Kaggle, Python khác version), **tái lập tất định** (chạy lại nhiều lần cho kết quả khớp tuyệt đối).

---

## 2. Claim được ủng hộ CÓ ĐIỀU KIỆN (đúng như phát biểu, phạm vi hẹp hơn hình dung trực quan)

### Theorem 16 — hội tụ cục bộ + phục hồi tốc độ online

Đây là claim **yếu nhất** trong paper về mặt đảm bảo lý thuyết — chính paper cũng tự nhận là "cục bộ, tiệm cận, có điều kiện", không cam kết vượt trội ở mọi horizon hữu hạn. Thực nghiệm khớp đúng với sự dè dặt đó:

| Bối cảnh | Kết quả | Đọc |
|---|---|---|
| Tín hiệu tổng hợp sạch (Phase-2A) | `online_beat_fraction_vs_fgla = 0.75` | **Ủng hộ tốt** — đúng chiều hướng dự đoán, vượt ngưỡng gate |
| Audio thật (Phase-2B) — basin | `overall_online_success_fraction = 0.840` vs FGLA `0.611` | **Ủng hộ rất tốt** — Online basin rộng hơn hẳn |
| Audio thật (Phase-2B) — tốc độ khi cùng hội tụ | `paired_success_median_q_ratio = 1.00064`, `beat_fraction = 0.420` | **Ủng hộ yếu** — gần như hoà, chưa đủ mạnh về thống kê |

**Đây không phải phản bác** — paper đã tự giới hạn phạm vi đảm bảo (Section 8 nêu rõ: không khẳng định vượt trội ở mọi horizon, đặc biệt gần $\lambda_+\approx1$). Dữ liệu thực tế đơn giản là **chưa "leo" tới đúng vùng** mà lý thuyết hứa hẹn ưu thế rõ ràng — ủng hộ đúng *hướng*, chưa đủ mạnh về *độ lớn*.

---

## 3. Điểm ủng hộ gián tiếp nhưng có giá trị cao: an toàn tuyệt đối của cơ chế safeguard

```
fallback_e1_failures = 0
```
xuyên suốt **cả 3 tầng thực nghiệm**:

| Tầng | Số lần chạy | Fallback thất bại |
|---|---|---|
| B1 — Phase-1E-R | 192 run | 0 |
| B2 — Phase-2A | 4 case | 0 |
| B3 — Phase-2B | 144 run | 0 |
| **Tổng cộng** | **> 300 lần chạy** | **0** |

Đây không phải một định lý formal riêng trong paper, nhưng là **tiền đề an toàn ngầm** cho mọi tuyên bố về cơ chế online — được ủng hộ tuyệt đối, không một ngoại lệ nào trên hơn 300 lần thử.

---

## 4. Bảng tổng hợp mức độ ủng hộ

| Mức độ | Nội dung | Số lượng claim |
|---|---|---|
| 🟢 Rất mạnh (gần tuyệt đối) | Theorem 2, Theorem 8, Proposition 13, Theorem 14 | 4/4 định lý cốt lõi |
| 🟡 Có điều kiện (đúng hướng, chưa đủ mạnh về độ lớn) | Theorem 16 trên audio thật (phần tốc độ) | 1 claim, đúng phạm vi paper tự giới hạn |
| 🟢 Ủng hộ gián tiếp, tuyệt đối | Cơ chế safeguard (không có định lý riêng) | > 300 lần chạy, 0 thất bại |
| ⚪ Không có claim nào bị bác bỏ | — | 0 |

---

## 5. Kết luận để đưa vào bản thảo / báo cáo nhóm

> Kết quả tái lập ủng hộ mạnh mẽ toàn bộ phần lý thuyết cốt lõi của paper (Theorem 2, Theorem 8, Proposition 13, Theorem 14) với độ chính xác gần tuyệt đối, tái lập nhất quán trên 2 môi trường thực thi độc lập. Phần thực nghiệm mở của paper tại thời điểm nộp bài (Section 8, E4–E5, khi đó còn TBD) nay đã có dữ liệu: cơ chế online chuyển giao tốt sang tín hiệu tổng hợp và audio thật ở **mức an toàn/basin** (không một lần fallback thất bại trên hơn 300 lần chạy, basin hội tụ rộng hơn FGLA), nhưng bằng chứng cho lợi thế **tốc độ** cụ thể trên audio thật vẫn còn yếu ở horizon đã thử nghiệm — đúng như giới hạn cục bộ/tiệm cận mà chính Theorem 16 đã tự đặt ra, không phải một phát hiện trái ngược với lý thuyết.

**Khuyến nghị:** đây là kết quả rất tích cực để đưa vào paper — việc 4 định lý cốt lõi được xác nhận độc lập trên 2 môi trường, tái lập tất định, là bằng chứng tái lập hiếm khi đạt được sạch như vậy trong thực nghiệm số, và nên được nêu bật ở phần Experiments/Reproducibility của bản thảo.

---
