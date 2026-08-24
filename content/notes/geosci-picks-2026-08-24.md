---
title: "GeoSci 精選 2026-08-24"
date: 2026-08-24T12:00:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 2 篇）。

## [3407] 一種基於注意力的深度學習方法，用於連續區間地震相位挑選
**An Attention‐Based Deep Learning Method for Continuous‐Interval Seismic Phase Picking**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Thu, 20 Aug 2026 00:00:00 GMT
- DOI：10.1785/0220250382/736237
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250382/736237/An-Attention-Based-Deep-Learning-Method-for)

**Summary (EN)**
The authors present an attention-augmented modification of PhaseNet that adds LSTM units in the encoder, parallel attention on skip connections, and a convolutional block attention module in the decoder, and they introduce interval labels for P and S segments. Trained on STEAD and evaluated on STEAD, INSTANCE and the Texas dataset, the model achieved an S-wave F1 of 0.980 at 0.5 s tolerance on STEAD (versus 0.869 for retrained PhaseNet, 0.969 for SEA, and 0.974 for EQTransformer), and P/S F1 scores of 0.909/0.803 on INSTANCE (versus 0.863/0.741 for PhaseNet). Tests with missing components show the model maintains useful performance with one component removed but degrades notably when two components are missing, particularly without the vertical channel, indicating improved picking versus PhaseNet but sensitivity to cross-dataset shifts and severe channel loss.

**重點摘要（繁中）**
作者提出一種改良的 PhaseNet，於編碼器加入 LSTM、在 skip 連接加入平行注意力，並在解碼器使用卷積區塊注意力模組，同時採用 P/S 的區間標籤。模型在 STEAD 訓練並於 STEAD、INSTANCE 與德州資料集上評估：在 STEAD（0.5 秒容差）達到 S 波 F1 = 0.980（改訓 PhaseNet 為 0.869，SEA 為 0.969，EQTransformer 為 0.974），在 INSTANCE 的 P/S F1 為 0.909/0.803（PhaseNet 為 0.863/0.741）。缺少一個分量時模型仍有實用表現，但缺兩個分量尤其無垂直分量時性能下降明顯，顯示相較 PhaseNet 有改善但對資料集差異與嚴重通道遺失仍較敏感。

## [3424] 以分布式聲學感測資料進行地震干涉分析所揭示的震動誘發小幅地震速度變化
**Shaking‐Induced Small Seismic Velocity Changes as Revealed From Seismic Interferometry Analysis of Distributed Acoustic Sensing Data**

- 期刊：Journal of Geophysical Research: Solid Earth (AGU/Wiley)
- Published：Fri, 21 Aug 2026 21:03:45 -0700
- DOI：10.1029/2025JB031867
- 原文連結：[連結](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025JB031867?af=R)

**Summary (EN)**
Using seismic interferometry on distributed acoustic sensing (DAS) data, the authors mapped coseismic velocity changes from a M4.1 earthquake 40 km from Sakurajima volcano with high spatial resolution. They found up to 1.0% velocity decreases in the 2–3 Hz band concentrated in sedimentary or old-lava areas with low S-wave velocity, and by stacking ambient-noise cross-correlation functions from many channel pairs achieved a 30-minute temporal resolution for relative velocity estimates. Although observed peak ground velocities were only about one-tenth of values in previous studies, the DAS-derived velocity reductions and recovery rates were comparable for roughly 12 hours after the earthquake, highlighting DAS's potential for dense spatial and improved temporal monitoring of seismic velocity changes.

**重點摘要（繁中）**
研究以分布式光纖震測（DAS）結合地震干涉分析，高空間解析度描述發生於櫻島火山40公里外的M4.1地震所引起的震速變化。結果顯示在2–3 Hz頻段中，沉積層或舊熔岩區等S波速度較低的地帶出現最大約1.0%的震速下降，並透過對大量通道對的環境噪音互相關函數堆疊，達成30分鐘的時間解析度以估算相對震速變化。儘管觀測到的峰值地面速度僅為先前研究的約十分之一，但震速降低與約12小時內的恢復速率相當，突顯DAS在高密度空間取樣與改善時間監測上的應用潛力。
