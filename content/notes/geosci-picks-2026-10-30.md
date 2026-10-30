---
title: "GeoSci 精選 2026-10-30"
date: 2026-10-30T00:00:00+08:00
tags: ["geosci", "papers", "Seismology", "Earthquake", "Geophysics", "Remote Sensing", "Machine Learning"]
categories: ["notes"]
---

本日選文（共 3 篇）。

## [4579] 人工智慧就緒的井下微震基準資料庫（AMBER）
**The AI‐Ready Downhole Microseismic Benchmark Database (AMBER)**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Wed, 28 Oct 2026 00:00:00 GMT
- DOI：10.1785/0220260134/799184
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220260134/799184/The-AI-Ready-Downhole-Microseismic-Benchmark)

**Summary (EN)**
Microseismic monitoring is widely used at subsurface industrial sites but AI advances seen for surface seismology have not yet translated to downhole microseismic processing, largely due to a lack of public training data. The authors present AMBER, an AI‑ready benchmark database compiled from 10 downhole datasets that includes over 4,000 events with more than 150,000 manually verified P and S arrival picks and over 10,000 manually verified noise examples. The database is distributed in an AI‑ready format with Python functions for data ingestion and augmentation to support development of AI tools for downhole microseismic processing.

**重點摘要（繁中）**
微地震監測廣泛應用於地下工業場域，但與地表地震資料相比，人工智慧在井下微地震處理尚未普及，主要因缺乏公開可用的訓練資料。作者建立了 AMBER，一個由10個井下微地震資料集匯整的 AI 就緒基準資料庫，包含超過4,000個事件、共超過150,000個經人工驗證的P波與S波到時標記，並有超過10,000個人工驗證的無信號噪音樣本。資料庫以 AI 就緒格式提供，並附有供資料導入與資料增強使用的 Python 函式，以促進井下微地震 AI 工具的開發。

## [4569] 自動化 InSAR 推導之地震斷層面作為實測真值地震資料集
**Automatic InSAR derived earthquake fault planes as a ground-truth seismic data set**

- 期刊：GJI (OUP) — RSS
- Published：Tue, 06 Oct 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag420
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag420/8869240?rss=1)

**Summary (EN)**
The authors produce an independent ground-truth catalogue of 42 shallow Mw 5.5–6.5 earthquakes by automatically inverting InSAR surface deformation with a Bayesian processing pipeline. They use this InSAR-derived data set to evaluate how 3-D velocity models, station geometry, and pick errors affect hypocentre locations, finding the InSAR inversions provide a fully characterized independent reference. For their limited sample, applying traveltime corrections from a 3-D velocity model did not, on average, move seismic locations closer to the InSAR ground-truth, while manual picking with proper error handling substantially improved agreement with the InSAR fault planes.

**重點摘要（繁中）**
作者利用自動化的貝氏處理流程，從InSAR表面變形反演出一組包含42個淺源、規模Mw 5.5–6.5的獨立地面真值目錄。研究使用此InSAR衍生資料集評估3D速度模型、觀測站分布與到時拾取誤差對震源定位的影響，並指出InSAR反演能作為具有完整模型誤差表徵的獨立參考。對於本研究樣本，使用3D速度模型的走時校正未能平均改善至InSAR真值位置，但經人工重拾時相並妥善處理誤差後，定位明顯更接近InSAR斷層面。

## [4557] 舊金山灣區地震危害：一種評估區域內任一地點發生強烈震動之機率地震危害分析方法
**Earthquake hazards across the San Francisco Bay Area: a methodology for probabilistic seismic hazard analysis of strong shaking occurring anywhere in a region**

- 期刊：GJI (OUP) — RSS
- Published：Wed, 28 Oct 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag422
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag422/9003845?rss=1)

**Summary (EN)**
The paper develops a methodology to estimate the probability that ground shaking anywhere within a region will exceed a prescribed threshold, addressing needs for aftershock/induced‑seismicity hazard assessment, emergency planning, earthquake early warning targeting, and model validation. The authors benchmark several stochastic sampling algorithms, compare spatial covariance models (including a new model derived from dense aftershock observations of the 2019 Ridgecrest sequence), and determine minimum spatial discretization and computational strategies for regional hazard estimation. They apply the method to the San Francisco Bay Area to compute probabilities that peak ground acceleration exceeds 0.1g, 0.2g, 0.4g or 0.8g at least once over 1–30 year periods, and examine how short‑term versus long‑term earthquake rates, ground motion variability, and source selection affect those regional hazard estimates.

**重點摘要（繁中）**
本文提出一種方法，用以估算整個區域內任一地點超過特定地震加速度阈值的機率，滿足餘震或誘發地震短期危害評估、緊急應變規劃、地震速報警示範圍決定及模型驗證等需求。作者評估多種隨機抽樣演算法的效能，比較不同的空間共變模型（包含基於2019年Ridgecrest餘震密集觀測的新模型），並確定估算區域性危害所需的最小空間離散化與計算效率措施。以舊金山灣區為案例，計算在1至30年內任一處至少發生一次峰值地面加速度超過0.1g、0.2g、0.4g或0.8g的機率，並探討短期與長期地震發生率、地面運動變異性及震源選擇對估計結果的影響。
