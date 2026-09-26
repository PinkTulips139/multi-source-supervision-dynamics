# MLBD2026 supervision-transfer proxy：索引修复与受限分析

## 阶段裁决

**技术门禁 PASS；固定词面概率传递 proxy 未获得跨 learner、跨 seed、跨两端点的重复支持。** 本分析是已曝光 outcome 后的探索性分析。它不建立新的因果机制，不修改 H1–H6，也不授权 M3。

前两个 FAIL_CLOSED 阶段原样保留。本阶段仅修复 paired-tuple multiset validator 把布尔掩码当行号迭代的错误：真实 `truth_ids` 为 `(3000,) int64`，原 `y==t` 为 `(3000,) bool`；改为 `idx_t=np.flatnonzero(y==t)` 后，用含 arm 顺序、dtype、shape 与原 float32 行字节的 SHA256 digest `Counter` 检查每个 truth block。人工索引、配对置换、单独移位反例及单 bit 变化检查均 PASS。单步 truth-block cyclic shift、共同词面 bridge、q targets、local129 均未改变。详见 `ROOT_CAUSE_AND_PATCH_REPORT.md` 与 `VALIDATOR_INDEXING_TESTS.json`。

## Pre-outcome gate 与时间顺序

- CLINC150 记录、REAL/CONTROL targets、local129、16 份 prediction artifact 的完整哈希与 ID/schema/truth/label mapping 均通过。pre-outcome 阶段只读取 prediction metadata，不打开 logits 值。
- REAL、CONTROL、paired tuple 和 Δq 的 truth-block 多重集、39 个 changed paired rows、CONTROL donor permutation、q(true)、source correctness、行/类别边际均通过。float32 q 原件未重建或重归一化。
- 正式 B 的行和、same/cross 分解、类别守恒、uniform-block 抵消通过。原 Δq 行和、block class residual 均为 0。
- misaligned REAL 与 CONTROL q-row simplex、多重集及分别计算的两个 proxy arm 均通过。两 arm 的最小概率均为 `0.0006666666666666668`；最大 simplex residual 为 `1.19e-8`，低于冻结的 `1e-6`；`r_REAL_mis-r_CONTROL_mis=0.9 E_mis` 最大 residual 为 `1.39e-17`。
- 用旧反构式作**不参与选择的前置诊断**，其最小坐标为 `−0.006411721758`，非正坐标 7 个，进一步核实旧 probability-domain blocker。
- `FEATURE_BINDING.json` 于 `2026-09-23T10:31:22Z` 持久化，SHA256 为 `9e5de811330b6a70838ebee469879d22fd63240e1a8fad3a4111be6bed486c4e`；`OUTCOME_ARRAYS_READ_BEFORE_FEATURE_FREEZE=0`。outcome access 于 `10:31:55Z` 才开始。随后读取 16 份既有 logits，独立重算 Secondary/LocalNLL 与正式 CONTROL authority 的最大绝对差异为 `5.83e-16`，小于 `1e-12`。

## 正式 alignment：逐 learner × seed × endpoint

下表 `g0` 为对 zero predictor 的平均绝对误差改进，`gc` 为对 same-truth-only predictor 的改进。**正值才代表误差下降**。`ρ` 为 129 个 local 样本上的固定 tie 处理 Spearman；这些样本不是 129 个独立实验。完整 strict 三态 3×3 sign table 逐行保存在 `PREDICTIVE_CHECK_SUMMARY.csv`。

| Learner | Seed | Secondary ρ | Secondary g0 | Secondary gc | LocalNLL ρ | LocalNLL g0 = gc |
|---|---:|---:|---:|---:|---:|---:|
| RoBERTa | 167174636 | −0.041047 | −4.19e−6 | −1.32e−5 | −0.063126 | −0.057340 |
| RoBERTa | 1852328752 | +0.129677 | +1.79e−5 | +3.17e−6 | +0.063775 | −0.056371 |
| RoBERTa | 1231418446 | +0.025815 | −2.12e−5 | −2.58e−5 | −0.089138 | −0.041495 |
| RoBERTa | 1461753708 | +0.017675 | +8.87e−6 | −1.58e−6 | −0.005352 | −0.011731 |
| XLNet | 167174636 | +0.154867 | +2.89e−5 | +1.24e−5 | −0.083775 | −0.031117 |
| XLNet | 1852328752 | −0.099324 | −9.36e−6 | −1.60e−5 | −0.023017 | −0.058231 |
| XLNet | 1231418446 | +0.127518 | +2.77e−5 | +1.06e−5 | +0.212420 | −0.021843 |
| XLNet | 1461753708 | +0.044946 | +5.66e−7 | −8.10e−6 | +0.115035 | −0.013486 |

冻结的严格相容条件同时要求 `ρ_real>0`、`g0_real>0`、`ρ_real>ρ_mis`、`MAE_real<MAE_mis`。Secondary 仅 XLNet seeds `167174636`、`1231418446` 满足，RoBERTa 0/4、XLNet 2/4。LocalNLL 两 learner 均为 0/4。

## Paired-arm misalignment falsification

下表 `gmis=MAE_misaligned−MAE_formal`；正值表示 formal alignment 的误差较低。完整 misalignment `ρ`、`gain_zero`、strict sign table 和逐项胜负见 `MISALIGNMENT_FALSIFICATION.csv`。

| Learner | Seed | Secondary ρ_mis | Secondary gmis | LocalNLL ρ_mis | LocalNLL gmis |
|---|---:|---:|---:|---:|---:|
| RoBERTa | 167174636 | −0.052590 | +1.06e−5 | +0.063108 | −0.049431 |
| RoBERTa | 1852328752 | +0.204557 | −6.27e−6 | +0.015806 | −0.049690 |
| RoBERTa | 1231418446 | +0.116668 | −3.85e−5 | +0.096387 | −0.045794 |
| RoBERTa | 1461753708 | +0.097565 | −1.96e−5 | +0.037395 | −0.015305 |
| XLNet | 167174636 | +0.061024 | +1.49e−5 | +0.161821 | −0.037985 |
| XLNet | 1852328752 | −0.092553 | +2.19e−5 | +0.011031 | −0.052134 |
| XLNet | 1231418446 | −0.150853 | +3.42e−5 | +0.002411 | −0.027681 |
| XLNet | 1461753708 | +0.066406 | −2.22e−5 | +0.061457 | −0.019979 |

Secondary 中 misalignment 的 ρ 不低于 formal 为 5/8、MAE 不高于 formal 为 4/8；formal 同时在两项上更好仅 3/8。LocalNLL 中 misalignment 的 MAE 更低为 **8/8**，ρ 不低于 formal 为 5/8。单一 shift 的这些差异没有随机化检验或 p-value。该负对照同时打断 text 与 absolute paired q、以及 text 与 Δq 的对应；即使个别结果偏向 formal，也不能归因为“只有 Δq alignment”的因果作用。

## Bridge 覆盖、抵消与 cross-truth 边界

39/3000 training rows 有 Δq。129 个 local query 中，changed-weight mass 非零 126 个、精确零 3 个；其中位数 `0.01502`、均值 `0.01650`，无 empty neighborhood。按照预先冻结的“至少 65 个近零”规则，`BRIDGE_SUPPORT_LIMITED=false`。但**查询类别方向很稀疏**：Secondary 仅 41/129 有 nonzero queried-direction support，LocalNLL 仅 32/129；正式 E 非零分别为 38/129、31/129。Secondary 33 个、LocalNLL 19 个 query 同时有正负贡献；精确有符号抵消分别为 3、1。未按覆盖量筛样本。

由冻结不变量，`E_same[j,y_j]=0`。因此本 proxy 的非零 true-class prediction 必须来自 cross-truth 项；LocalNLL 的 `gain_cross` 与 `gain_zero` 代数相同，八项均为负。这是结构与预测价值检查，**不是** cross-truth 因果机制发现。Secondary 的 `gain_cross>0` 仅 3/8。

## 科学解释与限制

最强支持观察是 XLNet seed `1231418446` 的 Secondary：formal `ρ=+0.1275` 对 misalignment `−0.1509`，相对 zero 与 misalignment 的 MAE 均有小幅改善；XLNet seed `167174636` 也满足全部严格条件。最强反例是 LocalNLL **八项 `gain_zero<0` 且 misalignment MAE 全部更低**；RoBERTa Secondary 四 seed 也无一满足严格条件。

同一 CLINC150 q、Δq 和共同 B 在两 learner 间完全相同，Secondary 的严格相容模式却为 RoBERTa 0/4、XLNet 2/4，记录描述性 `COMMON_SUPERVISION_FEATURE_RESPONSE_HETEROGENEITY`。Learner、tokenizer、recipe 等同时变化，不能归因于纯架构。misalignment 在多格相当或更好，削弱 `TEXT_SUPERVISION_ALIGNMENT_INTERPRETATION`。训练端监督和既有 wrong-label consequence 的正式证据不因本 proxy 的阴性结果而消失。

**最终：`PROXY_EXPLANATION_NOT_SUPPORTED`，范围限于这一固定 lexical probability-mixture proxy 的跨 seed、跨 endpoint 一般解释。** 保留 XLNet 两个 Secondary seed 的局部相容性和全部反例；不得换 shift、kernel、threshold 或 learner-conditioned bridge 补救。分析为 post-outcome exploratory；没有 sample-level p-value/bootstrap、没有新的 causal claim。H1–H6 `UNCHANGED`，M3 `DESIGNED_NOT_AUTHORIZED`。本阶段 training/forward/backward/GPU/SSH/Git write 均为 0。
