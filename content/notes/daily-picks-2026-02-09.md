---
title: "每日精選 2026-02-09"
date: 2026-02-09T08:00:00+08:00
draft: false
---

今天挑兩篇：

---

## 1) Seismic‐XR：在混合實境中模擬與視覺化地震地面運動

**Seismic‐XR: Simulating and Visualizing Seismic Ground Motions in Mixed Reality**

- 期刊：Seismological Research Letters Advance Access
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250169/725511/Seismic-XR-Simulating-and-Visualizing-Seismic)

### 摘要（中文）

Seismic-XR 是一個混合實境的教育工具，旨在可視化地震地面運動，讓使用者探索地震波如何與不同地形互動。針對烏塔拉坎地區一次地震的案例研究展示了計算建模、地理空間數據和 XR 技術的結合如何創造引人入勝的視覺體驗。儘管這提高了使用者的參與感，但 XR 對於提升概念理解的影響仍然不確定。

### Summary (EN)

Seismic-XR is a mixed-reality educational tool designed to visualize seismic ground motions, allowing users to explore how seismic waves interact with various landscapes. A case study from Uttarakhand illustrates how computational modeling, geospatial data, and XR visualization can be combined into an engaging visual experience. While the approach appears to improve engagement, the abstract notes that the effect of XR on deeper conceptual understanding remains uncertain.

---

## 2) 利用數據空間反演預測二氧化碳儲存中的斷層滑動傾向

**Prediction of fault slip tendency in CO₂ storage using data-space inversion**

- 期刊：ScienceDirect Publication: Computers & Geosciences
- 原文連結：[連結](https://www.sciencedirect.com/science/article/pii/S0098300426000312?dgcid=rss_sd_all)

### 摘要（中文）

作者提出一個以變分自編碼器（VAE，包含堆疊卷積式 LSTM 層）為核心的資料空間反演（DSI）框架，用以預測 CO2 儲存場域中的壓力、應變、有效法向應力與剪應力場，以及斷層滑動傾向。方法先以約 O(1000) 次先驗耦合流體—地力學模擬（包含一個帶兩條斷層的合成三維系統與非均質滲透率/孔隙度及不確定參數）訓練 VAE，然後直接從先驗模擬結果與監測井觀測資料推得後驗預測，不必生成後驗地質模型。結果顯示該框架能準確預測場量並降低關鍵地力與斷層參數的不確定性，但缺點是無法產出可供後續應用（如優化）使用的後驗地質模型。

### Summary (EN)

The authors propose a data-space inversion (DSI) framework built around a variational autoencoder (VAE) with convolutional LSTM layers to predict pressure, strain, and stress fields, as well as fault slip tendency, for CO₂ storage. The workflow is trained on a large ensemble of prior coupled flow–geomechanics simulations and then conditions predictions directly on monitoring-well observations, avoiding the expensive step of generating posterior geomodels. Synthetic experiments suggest accurate field predictions and reduced uncertainty in key geomechanical and fault parameters, with the trade-off that the method does not produce posterior models for downstream optimization tasks.
