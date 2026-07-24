# Correlation-Aware Recursive Training

**研究进行中 / Research in Progress**

本仓库记录一个正在推进中的研究项目。当前假设和方法设计尚未完成实证验证。

## 中文名称

面向稳定递归训练的多生成器错误相关性感知合成数据混合

## 完整研究方向

Beyond Source Diversity: Correlation-Aware Synthetic Data Mixing for Stable Recursive Training

## 一句话介绍

本项目研究在递归训练中，多个合成数据生成器之间的错误相关性是否可以帮助设计更稳定的数据混合策略。

## 当前状态

- 已完成核心文献初步筛选与研读。
- 已完成研究领域梳理。
- 已形成初步研究问题和研究假设。
- 已完成实验框架、基线和评价指标的初步设计。
- 尚未完成正式实验。
- 尚未验证核心假设。
- 尚未形成论文成果。

## 研究动机

递归使用模型生成数据进行训练，可能导致分布尾部丢失、错误传播和模型退化。很多已有工作用生成器数量、数据来源数量或合成数据比例描述多来源数据，但这些指标不一定代表真正独立的信息来源。

多个生成器可能来自相同基础模型、使用相似训练数据、具有相似知识边界，并在相同样本或能力区域共同犯错。因此，本项目关注生成器之间的错误相关结构，而不仅仅是来源数量。

## 核心研究问题

生成器之间的错误相关性，是否比生成器数量本身更能指导稳定递归训练中的合成数据混合？

## 初步研究假设

以下均为待验证假设，不是实验结论：

1. 多个生成器并不必然比单一生成器提供更多有效信息。
2. 生成器之间的错误相关性可能比生成器数量更能预测跨代模型退化。
3. 在相同生成器数量和数据预算下，错误相关性较低的来源组合可能具有更好的长期稳定性。
4. 根据错误相关结构动态调整不同来源的数据权重，可能优于等比例混合和随机混合。

## 初步方法框架

```text
Multiple Generators
-> Trusted Anchor-Set Evaluation
-> Error Correlation Matrix
-> Correlation-Aware Source Weighting
-> Recursive Retraining
-> Long-Term Stability Evaluation
```

初步优化形式可以写作：

```text
min_w  w^T R w + lambda * CoverageLoss(w)

subject to:
  w_i >= 0
  sum_i w_i = 1
```

其中 `R` 是生成器错误相关矩阵，`w` 是不同生成来源的混合权重。该表达式只是 preliminary formulation，不是最终算法。

## 当前进度清单

- [x] Initial literature mapping
- [x] Research problem formulation
- [x] Preliminary hypothesis design
- [x] Initial evaluation protocol
- [ ] Gaussian mixture simulation
- [ ] Multi-generator construction
- [ ] Correlation-aware mixing implementation
- [ ] Text classification experiments
- [ ] Ablation studies
- [ ] Final empirical conclusions

## 计划实验

1. 可控高斯混合实验
   - 控制生成器数量、单生成器错误率、生成器错误相关性、合成数据比例、头部和长尾比例、递归训练代数和随机种子。
2. 真实文本分类实验
   - 候选数据集：IMDb、SST-2、AG News。
   - 候选生成器构造方式：不同模型架构、不同训练数据子集、不同随机种子、不同训练检查点、不同提示或解码策略。

当前没有正式实验结果。

## 评价维度

计划评价 Accuracy / Macro-F1、每代性能变化、跨代退化斜率、生成器错误相关性、共同错误率、长尾 Recall、类别或语义簇覆盖、输出熵、分布漂移、错误遗传与放大、计算与数据成本。

## 仓库结构

请见英文 README 的 Repository Structure 部分。

## 复现原则

后续实验必须固定随机种子、保存配置、记录环境、保留可复现命令，并清楚区分研究假设和实验结果。

## 限制说明

本仓库目前处于研究规划和早期设计阶段，不包含已经验证的实验结论，不包含生产级代码，也不声称方法已经优于现有基线。