---
title: "每日精選 2026-02-08（II）"
date: 2026-02-08T12:00:00+08:00
draft: false
---

今天我挑了三篇：

---

## 1) Seismic‐XR：在混合實境中模擬與視覺化地震地面運動

**Seismic‐XR: Simulating and Visualizing Seismic Ground Motions in Mixed Reality**

- 期刊：Seismological Research Letters Advance Access
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250169/725511/Seismic-XR-Simulating-and-Visualizing-Seismic)

### 摘要（中文）

Seismic-XR 是一個混合實境的教育工具，旨在可視化地震地面運動，讓使用者探索地震波如何與不同地形互動。針對烏塔拉坎地區一次地震的案例研究展示了計算建模、地理空間數據和 XR 技術的結合如何創造引人入勝的視覺體驗。儘管這提高了使用者的參與感，但 XR 對於提升概念理解的影響仍然不確定。

### Summary (EN)

Seismic-XR is a mixed-reality educational tool that visualizes ground motion so users can explore how seismic waves interact with terrain. The paper demonstrates the workflow with a case study from Uttarakhand, combining computational modeling, geospatial data, and XR visualization to create an engaging learning experience. While the approach appears promising for engagement, the abstract notes that the impact of XR on conceptual understanding still needs clearer evaluation.

---

## 2) 利用數據空間反演預測二氧化碳儲存中的斷層滑動傾向

**Prediction of fault slip tendency in CO₂ storage using data-space inversion**

- 期刊：ScienceDirect Publication: Computers & Geosciences
- 原文連結：[連結](https://www.sciencedirect.com/science/article/pii/S0098300426000312?dgcid=rss_sd_all)

### 摘要（中文）

作者提出一個以變分自編碼器（VAE，包含堆疊卷積式 LSTM 層）為核心的資料空間反演（DSI）框架，用以預測 CO2 儲存場域中的壓力、應變、有效法向應力與剪應力場，以及斷層滑動傾向。方法先以約 O(1000) 次先驗耦合流體—地力學模擬（包含一個帶兩條斷層的合成三維系統與非均質滲透率/孔隙度及不確定參數）訓練 VAE，然後直接從先驗模擬結果與監測井觀測資料推得後驗預測，不必生成後驗地質模型。結果顯示該框架能準確預測場量並降低關鍵地力與斷層參數的不確定性，但缺點是無法產出可供後續應用（如優化）使用的後驗地質模型。

### Summary (EN)

The authors propose a data-space inversion workflow using a VAE (with convolutional LSTM layers) to predict pressure/strain/stress fields and fault slip tendency for CO₂ storage. The key idea is to train on a large ensemble of prior coupled flow–geomechanics simulations and then condition predictions on monitoring-well observations directly in data space, avoiding costly posterior geomodel generation. Synthetic tests suggest accurate field predictions and reduced uncertainty in key parameters, with the trade-off that no posterior models are produced for downstream tasks.

---

## 3) 地貌單元的重要性：結合土壤剖面特性與可解釋人工智慧強化崩塌預測

**Catena matters: Enhancing landslide prediction with soil profile characteristics and explainable AI**

- 期刊：ScienceDirect Publication: Engineering Geology
- 原文連結：[連結](https://www.sciencedirect.com/science/article/pii/S001379522600058X?dgcid=rss_sd_all)

### 摘要（中文）

本研究將深度依賴的土壤工礦與水文特性（10、110、210 公分）納入隨機森林模型，並以 SHAP 的可解釋式人工智慧解析模型。以印度南部西高止山脈 Muthirapuzha 流域為例，加入土壤剖面後的模型較僅用地形變數的模型準確且減少過度預測；重要預測變數包括田間持水量、風化化學指數、液限、非飽和導水率，以及坡度與地形濕潤指數等。結果暗示在地形—土壤沿坡序列（catena）框架下納入土壤剖面資訊，有助於提升崩塌預測的可靠度與解釋性。

### Summary (EN)

This work improves landslide susceptibility prediction by adding depth-dependent soil geotechnical and hydrological properties to a Random Forest model and interpreting the results with SHAP. Using a watershed in the Western Ghats (India), the soil-profile-enhanced model is more accurate and reduces overprediction compared with terrain-only baselines. Key drivers include field capacity, chemical weathering index, liquid limit, unsaturated hydraulic conductivity, and slope-related terrain indices, highlighting the value of catena-informed soil information for explainable hazard modelling.
