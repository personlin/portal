---
title: "GeoSci 精選 2026-11-25"
date: 2026-11-25T00:00:00+08:00
tags: ["geosci", "papers", "Seismology", "Machine Learning", "Earthquake", "Tectonics", "Tsunami", "Landslide", "Geodesy"]
categories: ["notes"]
---

本日選文（共 2 篇）。

## [4983] 顯式座標編碼至關重要：用於微地震監測初至波拾取的座標驅動架構
**Explicit coordinate encoding matters: a coordinate-driven framework for first-arrival picking in microseismic monitoring**

- 期刊：GJI (OUP) — RSS
- Published：Fri, 30 Oct 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag469
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag469/9005631?rss=1)

**Summary (EN)**
The study presents a U-Net-based framework for automatic microseismic first-arrival picking that adds pixel coordinates as two input channels, allowing the model to use absolute spatial positions alongside waveform features. On real data, coordinate encoding improved picking accuracy with only a 0.015% increase in model parameters: the P-arrival excellent rate rose from 73.06% to 92.24%, and average error fell from 9.51 to 3.36 ms. Ablation tests identified coordinate convolution as the main source of improvement, and the model outperformed a retrained PhaseNet baseline.

**重點摘要（繁中）**
本研究提出一種以 U-Net 為基礎的微震初至自動拾取框架，將像素座標作為兩個額外輸入通道，使模型能同時利用波形特徵與絕對空間位置。實際資料測試顯示，模型參數僅增加 0.015%，P 波初至的優良率便從 73.06% 提升至 92.24%，平均誤差則由 9.51 毫秒降至 3.36 毫秒。消融實驗指出，座標卷積是改善效果的主要來源；相較於以同一資料集重新訓練的 PhaseNet，該模型也有更高的優良率與更低的平均誤差。

## [4989] 即時破裂特徵化：改善紐西蘭大型地震的快速 ShakeMapNZ（震動圖層）
**Real‐Time Rupture Characterization to Improve Rapid ShakeMapNZ (Shaking Layers) for Aotearoa New Zealand’s Large Earthquakes**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Mon, 23 Nov 2026 00:00:00 GMT
- DOI：10.1785/0220260298/800019
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220260298/800019/Real-Time-Rupture-Characterization-to-Improve)

**Summary (EN)**
This study tests whether rapid estimates of earthquake rupture extent can improve New Zealand’s real-time ShakeMaps, using historical events and synthetic scenarios. For large M 7+ earthquakes, approximate 3D rupture models substantially reduce underestimation of near-source shaking, while also improving estimates for M 6+ events; the preferred approach, FinDer, produces estimates within minutes and helped in the case studies even when its geometry was inaccurate. Finite-fault information can also strengthen downstream impact products, such as exposed-population estimates and landslide forecasts, supporting faster and more accurate assessment of major earthquakes.

**重點摘要（繁中）**
本研究利用歷史地震與合成情境，檢驗快速估計地震破裂範圍是否能改善紐西蘭即時 ShakeMap。對 M 7 以上的大地震，近似的三維破裂模型可大幅減少近震源地區震動的低估，也能改善 M 6 以上事件的震動估計；研究建議採用 FinDer，該工具可在數分鐘內提供破裂估計，且在案例中即使幾何形狀不準確仍有助於改善結果。有限斷層資訊也能提升人口暴露估計與山崩預報等後續影響產品，協助更快速、準確地評估重大地震的影響。
