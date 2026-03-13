---
title: "GeoSci 精選 2026-03-13"
date: 2026-03-13T12:00:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 6 篇）。

## [809] DeepSubDAS：基於海底分布式聲學感測（DAS）資料的地震相位挑選器
**DeepSubDAS: an earthquake phase picker from submarine distributed acoustic sensing data**

- 期刊：GJI (OUP) — RSS
- Published：Mon, 09 Feb 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag061
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag061/8468857?rss=1)

**Summary (EN)**
Submarine Distributed Acoustic Sensing (DAS) can address the scarcity of seismometers in oceanic regions, but land-trained models perform poorly on submarine data. This study develops a DeepLab v3–based machine learning model specifically for submarine DAS to detect seismic events and pick P- and S-waves, trained and validated on nearly 57 million manually and semi-automatically labelled records from multiple global submarine sites. The model is designed to handle different cable lengths, configurations and channel spacings, providing an adaptable tool for automated earthquake analysis and with potential to support real-time monitoring and tsunami early warning.

**重點摘要（繁中）**
海域缺乏地震儀限制了傳統地震學的有效性，潛望式海底分散式聲學感測（DAS）可作為替代，但以陸地資料訓練的模型在海底資料上表現不佳。這項研究以 DeepLab v3 為基礎，開發專門針對海底 DAS 的機器學習模型，用於自動偵測地震事件並識別 P 波與 S 波，模型在來自多個全球海底站點、近 5700 萬筆人工與半自動標註的紀錄上進行訓練與驗證。該模型能適應不同光纜長度、配置和通道間距，提供可用於自動化地震分析的工具，並有助於強化即時監測與海嘯預警的能力。

## [804] 結合斷層位移與應變模型以自 GNSS 與 InSAR 重建三維同震變形場
**Integrated dislocation and strain models for 3-D coseismic deformation field from GNSS and InSAR**

- 期刊：GJI (OUP) — RSS
- Published：Tue, 24 Feb 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag073
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag073/8496063?rss=1)

**Summary (EN)**
The paper introduces Integrated Dislocation and Strain Models (IDSM) that fuse GNSS and InSAR by combining a surface-constrained strain model with a subsurface-constrained dislocation model and adaptively weighting data via Variance Component Estimation. Simulations show that when GNSS coverage is sparse, IDSM improves 3-D coseismic deformation recovery by 10–70% in vertical, north and east components compared with ESISTEM-VCE, with particularly large gains in the north component. Applied to the 2021 Yangbi (MW6.4) and Maduo (MW7.4) earthquakes, the method resolves distinct rupture patterns (Yangbi: right-lateral strike-slip with ~87 mm east–west extension and 59.8 mm subsidence; Maduo: left-lateral strike-slip with ~1.4 m east–west displacement) and yields substantial RMSE reductions at GNSS validation points versus ESISTEM–VCE.

**重點摘要（繁中）**
本文提出整合鬆弛體與應變模型（IDSM），將地表受約束的應變模型與地下受約束的斷層位錯模型結合，並以變異數成分估計自適應調整多來源資料權重來融合 GNSS 與 InSAR。模擬結果顯示，在 GNSS 站點稀疏情況下，IDSM 相較於 ESISTEM-VCE 可使垂直、北向與東向分量的變形恢復精度提升 10–70%，北向分量改善尤為顯著。應用於 2021 年洋碧（MW6.4）與瑪多（MW7.4）地震可分辨出不同破裂特徵（洋碧為右旋走滑，東西向最大張性位移約 87 mm、垂直下陷 59.8 mm；瑪多以左旋走滑為主，東西向位移達約 1.4 m），且在 GNSS 驗證點上相較 ESISTEM–VCE 有明顯的 RMSE 降低。

## [802] 模擬地震活動顯示 b 值為潛在地震前兆
**Simulated seismicity highlights the b-value as a potential earthquake precursor**

- 期刊：GJI (OUP) — RSS
- Published：Tue, 03 Mar 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag080
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag080/8504090?rss=1)

**Summary (EN)**
The paper compares observed seismicity in the central–northern Apennines (1987–2025) with a 10,000‑year physics‑based synthetic catalogue built from a 3D seismotectonic model and an elastic‑rebound nucleation framework to test short‑term b‑value changes. Using ±15‑day, 30‑km stacking around pivot events, the observed data show a significant b‑value drop before Mw ≥ 4.0 earthquakes with post‑event recovery, and the synthetic catalogue reproduces a comparable pre‑event decrease and post‑rupture increase for Mw ≥ 4.5 (robust across thresholds). The results indicate that physics‑based simulations can reproduce short‑term b‑value variations associated with earthquake nucleation, supporting the b‑value’s relevance as a potential earthquake precursor and a probe of underlying seismic processes.

**重點摘要（繁中）**
作者將中央—北部阿彭尼尼山脈（1987–2025 年）的觀測地震目錄，與一個基於三維地震構造模型和彈性回彈地震成核框架所生成的 10,000 年合成地震目錄進行比較，檢驗短期 b 值變化。以 ±15 天、30 公里範圍堆疊分析樞紐事件，觀測資料顯示 Mw ≥ 4.0 事件前 b 值顯著下降並於後事件回復，合成資料也再現了對於 Mw ≥ 4.5 事件的前置 b 值下降及事後上升，且在不同震級門檻下表現穩定。研究表明物理基礎的模擬能重現與地震成核相關的短期 b 值變化，支持 b 值作為潛在前兆及探究地震物理過程的指標。

## [805] 發掘單一臺站取代地震陣列的潛力
**Unlocking the potential of single stations to replace seismic arrays**

- 期刊：GJI (OUP) — RSS
- Published：Thu, 19 Feb 2026 00:00:00 GMT
- DOI：10.1093/gji/ggag070
- 原文連結：[連結](https://academic.oup.com/gji/article/doi/10.1093/gji/ggag070/8490468?rss=1)

**Summary (EN)**
The authors present Virtual Seismic Arrays, a deep-learning encoder–decoder system that predicts full array recordings from a single reference station by modeling the transfer of the seismic wavefield, enabling array-like multistation functionality without continuous deployment of all sensors. They train models on secondary ocean microseism recordings from the Gräfenberg array in Germany and assemble station-specific predictors into a Virtual Seismic Array. Beamforming comparisons between original and predicted waveforms across three source-regime scenarios show strong agreement when the dominant source regime in the test data was represented in the training data, demonstrating the approach's feasibility.

**重點摘要（繁中）**
作者提出「虛擬地震陣列」，利用深度學習的編碼器–解碼器模型從單一參考站預測整個陣列的記錄，透過模擬地震波場的傳遞，讓系統在不需同時部署所有儀器的情況下仍具多站功能，從而降低成本並解決後勤問題。研究以德國 Gräfenberg 陣列的次級海洋微震資料訓練每個站的預測模型，並將這些模型組合成虛擬陣列。透過對原始與預測波形進行波束形成並測試三種來源情況，結果顯示當測試中出現的主導來源類型已出現在訓練資料中時，預測與原始波束形成結果高度一致，證明此方法可行。

## [814] 考量多重地震動強度指標之地震誘發滑坡機率性危害分析
**Probabilistic Hazard Analysis of Earthquake-Induced Landslides considering Multiple Ground Motion Intensity measures**

- 期刊：Earth-Science Reviews (ScienceDirect)
- DOI：10.1016/j.enggeo.2026.108677
- 原文連結：[連結](https://www.sciencedirect.com/science/article/pii/S0013795226001365?dgcid=rss_sd_all)

**Summary (EN)**
The paper presents a new probabilistic framework for assessing earthquake-induced landslide hazard that allows multiple ground motion intensity measures (IMs) to be included in displacement hazard curves (DHCs). To avoid the complexity of full vector PSHA, the method uses a single ground motion prediction equation for the Fourier amplitude spectrum (FAS) to generate multiple, internally consistent IMs that preserve mutual correlations, which are then fed into a slope displacement model; Latin hypercube sampling accounts for uncertainties in slope and seismic parameters. The framework is validated with numerical examples by comparing the resulting DHCs to those from Monte Carlo simulations, showing its effectiveness and accuracy.

**重點摘要（繁中）**
本研究提出一套新的機率性地震致滑坡危害分析架構，可將多個地震動強度指標（IMs）納入位移危害曲線（DHCs）。為避免複雜的向量型PSHA，方法採用單一傅立葉振幅譜（FAS）的地震動預測關係來生成多個內部一致且保有相互關聯的IMs，並將這些IMs輸入位移模型；對坡體與地震參數的不確定性則以拉丁超立方抽樣處理。透過數值範例將所得DHCs與蒙地卡羅模擬結果比較，驗證了此框架的有效性與準確性。

## [798] 用於斷層帶井下地震資料詮釋之井管波半解析建模方法
**A Semi‐Analytical Approach to Model Borehole Tube Waves for Interpretation of Downhole Seismic Data in Fault Zones**

- 期刊：Earth and Space Science (AGU/Wiley) — eTOC
- Published：Wed, 11 Mar 2026 05:32:42 -0700
- DOI：10.1029/2025JB032363
- 原文連結：[連結](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025JB032363?af=R)

**Summary (EN)**
The paper presents a semi-analytical model to predict borehole pressure responses to a normally incident plane P wave in layered poroelastic media, explicitly including irregular borehole radius. The model incorporates three tube-wave generation mechanisms—elastic impedance contrasts, fluid infiltration from poroelastic layers, and borehole-radius changes—and uses a propagator-matrix formulation under low-frequency assumptions to derive closed-form amplitude expressions. Validated against finite-difference poroelastic simulations, the results show elastic boundaries produce tube waves of opposite polarity while thin porous and thin elastic layers yield asymmetric frequency spectra; the approach improves prior effective-source models by including tube-wave velocity contrasts and poroelastic consistency, enabling more efficient interpretation of VSP data for estimating local hydraulic properties in fault zones.

**重點摘要（繁中）**
本文提出一種半解析模型，用以預測分層孔隙彈性媒質中，垂直入射平面P波引起的井內壓力響應，並明確考慮井徑不規則性。該模型納入三種管波產生機制——彈性阻抗對比、由孔隙彈性層滲入流體以及井徑變化，並在低頻假設下以傳播矩陣形式導出閉合式振幅表達式。模型經有限差分孔隙彈性模擬驗證，結果顯示彈性邊界會產生相反極性的管波，而薄孔隙層與薄彈性層產生頻譜顯著不同且不對稱的響應；此方法較先前的有效源模型更完整考慮管波速度對比與孔隙彈性理論一致性，有助於更有效地解釋斷層區的VSP資料以估算局部水力性質。
