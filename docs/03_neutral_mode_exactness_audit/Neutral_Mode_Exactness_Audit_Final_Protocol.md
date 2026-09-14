# Neutral-Mode Exactness Audit --- Final Targeted Test v1

## ICLR 2027 --- Geometry Determines Acceleration in Phase Retrieval

### Mục tiêu

Đây là **targeted diagnostic cuối cùng** dành riêng cho hai MUSAN
real-audio cases đang có

``` text
neutral_count_topk = 2
```

với numerical classification hiện tại

``` text
phase_tol = 1e-7
```

Hai files:

``` text
noise-free-sound-0043.wav
noise-free-sound-0389.wav
```

**Không rerun toàn bộ 202 files. Không sửa core algorithm.**

Mục tiêu là phân biệt ba khả năng:

\[ `\textbf{A. Genuine 2D neutral symmetry:}`{=tex}`\qquad`{=tex}
`\lambda`{=tex}\_1=1,`\quad`{=tex}`\lambda`{=tex}\_2=1, \]

\[
`\textbf{B. One exact phase mode + one near-neutral transverse mode:}`{=tex}`\qquad`{=tex}
`\lambda`{=tex}\_1=1,`\quad`{=tex}`\lambda`{=tex}\_2=1-`\delta`{=tex},`\quad 0`{=tex}\<`\delta`{=tex}`\ll1`{=tex},
\]

hoặc

\[
`\textbf{C. Numerical eigensolver / threshold classification effect.}`{=tex}
\]

Distinction này quan trọng vì regularity assumption hiện tại của theory
là

\[
`\mathcal `{=tex}U`\cap `{=tex}T\_{c\^`\star`{=tex}}`\mathcal `{=tex}M_s
= `\operatorname{span}`{=tex}\_{`\mathbb `{=tex}R}{ic\^`\star`{=tex}},
\]

tức exact neutral phase space có dimension 1.

------------------------------------------------------------------------

# 1. Freeze trước khi chạy

Giữ nguyên như experiment 202-file: - audio files; - preprocessing; -
STFT configuration; - target solution; - matrix-free
Jacobian/operator; - normalization; - seed nếu có.

Không crop, đổi STFT, đổi signal hay điều chỉnh regularity criterion để
đạt kết quả mong muốn.

Output:

``` text
results/neutral_mode_exactness_audit/
```

------------------------------------------------------------------------

# 2. Test A --- High-Precision Top-Eigenvalue Extraction

Với mỗi file, tính ít nhất 8 eigenvalues lớn nhất

\[
`\lambda`{=tex}\_1`\ge`{=tex}`\lambda`{=tex}\_2`\ge`{=tex}`\cdots`{=tex}`\ge`{=tex}`\lambda`{=tex}\_8
\]

của đúng local spectral operator/Jacobian dùng trong original
experiment.

Primary solver setting:

``` text
eig_tol = 1e-12
```

Nếu solver không đạt được tolerance này, phải report achieved
residual/tolerance thay vì âm thầm nới tolerance.

Với mỗi eigenvalue tính

\[ `\delta`{=tex}\_j=1-`\lambda`{=tex}\_j. \]

Ba quantities quan trọng nhất:

\[
1-`\lambda`{=tex}\_1,`\qquad1`{=tex}-`\lambda`{=tex}\_2,`\qquad1`{=tex}-`\lambda`{=tex}\_3.
\]

Nếu có eigenpair residual, tính

\[ r_j= `\frac{\|Jv_j-\lambda_jv_j\|}`{=tex} {`\max`{=tex}(1,\|Jv_j\|)}.
\]

Xuất:

``` text
top_eigenvalues.csv
top_eigenvalues.json
```

với fields:

``` text
file_id
rank
eigenvalue
one_minus_eigenvalue
eig_tol
solver_residual
solver_status
```

------------------------------------------------------------------------

# 3. Test B --- Neutral-Count Tolerance Sweep

Không thay đổi operator/eigenvalues. Reclassify spectrum với

\[ `\texttt{phase\_tol}`{=tex}`\in`{=tex}
{10^{-5},10^{-6},10^{-7},10^{-8},10^{-9},10^{-10}}. \]

Classification rule giữ nguyên:

\[ `\lambda`{=tex}\_j`\ge1`{=tex}-`\texttt{phase\_tol}`{=tex}. \]

Record:

``` text
file_id
phase_tol
neutral_count
lambda_plus_after_neutral_removal
```

Xuất:

``` text
neutral_tolerance_sweep.csv
neutral_tolerance_sweep.json
```

### Diagnostic chính

Kiểm tra có xảy ra ổn định

\[ `\texttt{neutral\_count}`{=tex}:2`\rightarrow1`{=tex} \]

khi `phase_tol` giảm hay không.

Nếu có, second mode nên được hiểu là **extremely near-neutral transverse
mode**, không phải bằng chứng của second exact phase symmetry.

------------------------------------------------------------------------

# 4. Test C --- Solver Stability

Lặp high-precision eigensolve ít nhất tại:

``` text
eig_tol = 1e-10
eig_tol = 1e-12
```

Nếu chi phí thấp, thêm:

``` text
eig_tol = 1e-8
```

So sánh (`\lambda`{=tex}\_1,`\lambda`{=tex}\_2,`\lambda`{=tex}\_3) giữa
các runs và report

\[ \|`\lambda`{=tex}\_j\^{(a)}-`\lambda`{=tex}\_j\^{(b)}\|. \]

Không kết luận eigenvalue mathematically exact chỉ vì numerical printout
là `1.000000`.

------------------------------------------------------------------------

# 5. Test D --- Global-Phase Direction Verification

Với known phase tangent

\[ z\_{`\rm phase`{=tex}}=ic\^`\star`{=tex}, \]

tính normalized real-Hilbert alignment với leading eigenvector:

\[ a_1= `\frac{|\langle v_1,z_{\rm phase}\rangle_{\mathbb R}|}`{=tex}
{\|v_1\|\|z\_{`\rm phase`{=tex}}\|}. \]

Report (a_1).

Nếu top two eigenvalues gần degenerate khiến eigensolver trả arbitrary
rotated basis, tính thêm projection của phase direction lên

\[ E_2=`\operatorname{span}`{=tex}{v_1,v_2}: \]

\[ a\_{E_2} = `\frac{\|P_{E_2}z_{\rm phase}\|}`{=tex}
{\|z\_{`\rm phase`{=tex}}\|}. \]

Điều này tránh nhầm basis rotation với failure của phase-direction test.

------------------------------------------------------------------------

# 6. Test E --- Second-Mode Structural Diagnostic

\*\*Chỉ chạy Test E nếu Tests A--D vẫn cho thấy (`\lambda`{=tex}\_2)
numerically indistinguishable from 1.\*\*

Không mặc định rằng waveform có silence gap thì tồn tại independent
phase symmetry.

Cần cung cấp tối thiểu:

1.  waveform energy versus time;
2.  STFT magnitude/support map;
3.  eigenvector (v_2) trong natural time-frequency coordinates;
4.  evidence for/against disconnected measurement components.

Nếu claim genuine phase islands, phải chứng minh measurement structure
thực sự/effectively disconnected, không chỉ waveform nhìn thấy khoảng
lặng.

Nếu khả thi, xây time-frequency overlap/support graph và report
connected components.

------------------------------------------------------------------------

# 7. Decision Rules

## Outcome B --- Near-neutral transverse mode

Classify **near-neutral, regular-compatible** nếu evidence cho thấy: -
có một structural global-phase direction; - (`\lambda`{=tex}\_2\<1) ở
sufficiently accurate resolution; và/hoặc - `neutral_count` chuyển từ 2
xuống 1 khi tolerance chặt hơn; - eigenpair residual đủ nhỏ.

Recommended interpretation:

> The apparent second neutral mode at `phase_tol = 1e-7` is an extremely
> slow transverse mode rather than a second exact phase symmetry.

------------------------------------------------------------------------

## Outcome A --- Genuine additional neutral direction

Classify case là **nonregular with respect to the simple-neutral-mode
theorem assumption** nếu:

\[ `\lambda`{=tex}\_2=1 \]

đến numerical resolution cao **và** structural diagnostic hỗ trợ một
independent symmetry direction thứ hai.

Recommended interpretation:

> The case exhibits an additional neutral direction and therefore lies
> outside the simple-neutral-mode regularity assumption used by the main
> local theorem.

Đây **không phải algorithm failure**; report riêng như
exceptional/nonregular real-audio case.

------------------------------------------------------------------------

## Outcome C --- Numerically unresolved

Nếu precision hiện có không phân biệt được

\[ `\lambda`{=tex}\_2=1 \]

với

\[ `\lambda`{=tex}\_2=1-`\delta`{=tex}, \]

gắn verdict:

``` text
NEAR/EXACT NEUTRAL — NUMERICALLY UNRESOLVED
```

Không ép một theoretical interpretation.

------------------------------------------------------------------------

# 8. Claim Discipline

Không được suy ra từ current evidence:

> Silence gaps prove two independent phase symmetries.

Và rule

\[ `\lambda`{=tex}\_j`\ge1`{=tex}-10\^{-7} \]

chỉ là **numerical classification threshold**, không phải proof rằng

\[ `\lambda`{=tex}\_j=1. \]

Phải phân biệt rõ:

``` text
numerically near 1
```

và

``` text
structurally/exactly equal to 1.
```

------------------------------------------------------------------------

# 9. Required Final Table

  ---------------------------------------------------------------------------------------------------------------------------------------------------------
  File                            (1-`\lambda`{=tex}\_1)   (1-`\lambda`{=tex}\_2)   (1-`\lambda`{=tex}\_3)    neutral @     neutral @       phase verdict
                                                                                                             (10\^{-7})   (10\^{-10})   alignment 
  ----------------------------- ------------------------ ------------------------ ------------------------ ------------ ------------- ----------- ---------
  `noise-free-sound-0043.wav`                        TBD                      TBD                      TBD            2           TBD         TBD TBD

  `noise-free-sound-0389.wav`                        TBD                      TBD                      TBD            2           TBD         TBD TBD
  ---------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 10. Required Handoff

Return:

``` text
neutral_mode_exactness_audit.zip
├── README.md
├── summary.json
├── top_eigenvalues.csv
├── top_eigenvalues.json
├── neutral_tolerance_sweep.csv
├── neutral_tolerance_sweep.json
├── solver_stability.csv
├── phase_alignment.csv
├── figures/
├── structural_diagnostic/   # only if Test E is required
├── environment.txt
└── commands.txt
```

`summary.json` cần có:

``` text
file_id
verdict
lambda_1
lambda_2
lambda_3
gap_1
gap_2
gap_3
neutral_count_at_1e-7
neutral_count_at_1e-10
phase_alignment
eigenspace_phase_alignment
structural_test_required
notes
```

------------------------------------------------------------------------

# 11. Stop Rule

Sau Tests A--D:

**STOP và handoff package cho supervisor audit.**

Không tự động chạy Test E nếu A--D đã phân biệt được near-neutral và
exact-neutral.

Không rerun 200 MUSAN files còn lại.

Không thay đổi main algorithm.

------------------------------------------------------------------------

# 12. Scientific Objective

Mục tiêu không phải làm cho cả 202 cases đều thỏa regular theorem
assumptions.

Mục tiêu là xác định trung thực evidence hỗ trợ trường hợp nào:

\[
`\boxed{\text{one exact phase symmetry + an extremely slow transverse mode}}`{=tex}
\]

hoặc

\[
`\boxed{\text{a genuinely higher-dimensional neutral symmetry}}`{=tex}
\]

hoặc

\[
`\boxed{\text{numerically unresolved at the available precision}.}`{=tex}
\]

Cả ba outcomes đều scientifically acceptable nếu được report chính xác.
