---
title: "每日精選 2026-02-08"
date: 2026-02-08T00:00:00+08:00
draft: false
---

今天我選的一篇：

## 基於深度學習並結合疊層學岩性約束的混合模型，用於提升遺失測井曲線的預測準確度

**Deep-learning-based hybrid model with iterative lithology constraints for the enhanced prediction of missing well-logs**

- 期刊：ScienceDirect Publication: Computers & Geosciences
- 原文連結：https://www.sciencedirect.com/science/article/pii/S0098300426000038?dgcid=rss_sd_all

### 摘要（中文）

本研究提出了一種名為ILCH-Net的深度學習模型，透過將岩性資訊作為限制條件，提升缺失井資料的預測準確度。該模型結合條件變分自編碼器與基於長短期記憶網絡的岩性預測器，在挪威北海六口油井資料上進行測試，結果優於傳統方法，且重建結果在不同井間更具一致性。此方法對石灰岩和黏土岩的預測效果尤其顯著，為儲層特徵描述及相關應用提供可行的建模途徑。

### Summary (EN)

The authors propose ILCH-Net, a deep-learning model for imputing missing well logs by iteratively enforcing lithology constraints so predictions remain geologically consistent rather than purely data-driven. The approach combines a conditional variational autoencoder with an LSTM-based lithology predictor and trains in a way that can leverage both the log waveforms and lithology information to guide reconstruction. Tests on six wells from the Norwegian North Sea show improved accuracy over baseline methods and better cross-well consistency, with particularly strong gains for limestone and claystone intervals.
