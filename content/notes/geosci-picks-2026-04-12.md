---
title: "GeoSci 精選 2026-04-12"
date: 2026-04-12T12:00:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 1 篇）。

## [1317] CapsNet 強化之地震事件分類：在 DiTing 2.0 資料集上的基準測試與系統部署
**CapsNet-enhanced seismic event classification: benchmarking and system deployment on the DiTing 2.0 data set**

- 期刊：GJI (OUP) — RSS
- Published：Fri, 03 Apr 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag129
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag129/8586473?rss=1)

**Summary (EN)**
This study provides the first systematic benchmark of mainstream deep learning models (CNNs, Transformer-based architectures, and Capsule Networks) on the large-scale DiTing 2.0 seismic dataset, which contains 19,384 three-component waveforms labeled as natural earthquakes, quarry blasts, or mine collapses. Optimized CapsNet variants, particularly a CapsNet+Res model using MFCC features and data augmentation, achieved 91.08% accuracy (weighted F1 = 91.10%) on the held-out test set; multi-station voting raised event-level accuracy to 97.52%, and a companion noise-event classifier reached 98.47% accuracy. Demonstration tests on continuous records show reliable end-to-end operation in a transferable, user-friendly system, and the authors highlight large-scale continuous-data evaluation, cross-regional transfer, and adaptive learning as important future directions.

**重點摘要（繁中）**
本研究在大規模 DiTing 2.0 地震資料集上首次系統性地對主流深度學習模型（CNN、Transformer 類架構與膠囊網路）進行基準測試；該資料集包含19,384筆三分量波形，標示為天然地震、採石場爆破或礦井塌陷三類。經優化的 CapsNet 變體（CapsNet+Res，使用 MFCC 特徵與資料增強）在保留測試集上達到91.08%準確率（加權 F1 = 91.10%）；多站投票將事件層級準確率提升至97.52%，搭配的噪音事件分類器則達98.47%準確率。示範連續記錄的功能測試顯示系統能可靠地端到端運作且具可移植性與友好性，作者並指出大規模連續資料評估、跨區域遷移驗證與自適應學習為後續重要研究方向。
