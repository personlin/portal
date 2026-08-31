---
title: "GeoSci 精選 2026-08-31"
date: 2026-08-31T08:13:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 4 篇）。

## [3497] SCMLPick：一個在 SeisComP 中實作機器學習相位挑選以支援即時地震監測的模組
**SCMLPick: A SeisComP Module Implementing Machine Learning Phase Picking for Real‐Time Seismic Monitoring**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Thu, 27 Aug 2026 00:00:00 GMT
- DOI：10.1785/0220250368/752591
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250368/752591/SCMLPick-A-SeisComP-Module-Implementing-Machine)

**Summary (EN)**
The paper describes SCMLPick, a SeisComP module that integrates machine learning phase picking into real-time seismic monitoring. It notes that ML algorithms outperform traditional detectors but that real-time deployment is challenged by substantial computational demands and integration with operational workflows. Since 2023 the Texas Seismological Network has used an ML-based picker, increasing detection rates of low-magnitude earthquakes and yielding high consistency in arrival-time estimates; region-specific tuning further improved detection accuracy and operational reliability.

**重點摘要（繁中）**
本文介紹 SCMLPick，一個將機器學習地震相檢測整合到 SeisComP 實時監測的模組。作者指出，機器學習方法在自動辨識地震相方面優於傳統方法，但因為計算負擔大且難以與作業流程整合，實時部署具有挑戰性。自 2023 年起，德州地震網（TexNet）採用此 ML 撿相器，提高了低震級地震的檢測率並在到時估計上保持高度一致性；區域性調校進一步提升了檢測準確度與營運可靠性。

## [3498] DASView：基於 PyQt 的分布式聲學感測（DAS）資料視覺化與處理工具
**DASView: A PyQt‐Based Visualization and Processing Tool for Distributed Acoustic Sensing Data**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Thu, 27 Aug 2026 00:00:00 GMT
- DOI：10.1785/0220250438/752590
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250438/752590/DASView-A-PyQt-Based-Visualization-and-Processing)

**Summary (EN)**
The paper introduces DASView, a PyQt-based interactive visualization and processing tool for distributed acoustic sensing (DAS) data. It combines classical seismic workflows (data slicing, filtering, spectral analysis) with DAS-specific functions (denoising, channel attribute analysis), and provides core features such as 2D waterfall visualization, interactive single-channel waveform and spectrum inspection, flexible figure export, plus modules for travel-time extraction and automated traffic signal tracking. Open example datasets are provided to facilitate validation, and the tool aims to lower technical barriers and accelerate DAS data exploration and adoption.

**重點摘要（繁中）**
本論文提出 DASView，一款基於 PyQt 的互動式分布式聲學感測（DAS）資料視覺化與處理工具。它整合傳統地震資料處理流程（如切片、濾波、頻譜分析）與 DAS 專屬功能（去噪、通道屬性分析），並提供 2D 瀑布圖、互動單通道波形與頻譜檢視、彈性圖形匯出，以及行波到時提取與自動交通訊號追蹤模組。工具附帶公開範例資料集，旨在降低 DAS 資料分析門檻，促進研究與應用普及。

## [3509] 以分布式聲學感測（DAS）與列車振動推估近地表剪切波速度
**Near‐Surface Shear‐Wave Velocity from Train Vibrations with Distributed Acoustic Sensing**

- 期刊：Bulletin of the Seismological Society of America — Advance Access
- Published：Fri, 28 Aug 2026 00:00:00 GMT
- DOI：10.1785/0120260132/753329
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/bssa/article/doi/10.1785/0120260132/753329/Near-Surface-Shear-Wave-Velocity-from-Train)

**Summary (EN)**
The authors used distributed acoustic sensing (DAS) on a 14.7 km buried fiber to image near‑surface shear‑wave velocity (VS) using train traffic in Del Mar, California. By applying interferometry, cross‑correlation, beamforming, and 1D inversions at each channel they assembled a 2D tomographic VS profile that reveals low‑velocity zones in the San Dieguito Valley and Los Peñasquitos Lagoon consistent with thicker alluvial and lagoonal sediments. They also find VS30 correlates with elevation and low VS30 at the coastal cliff is associated with sand content and sediment thickness, while diurnal DAS strain patterns reflect temperature changes and can help locate fiber spools. The study demonstrates DAS as a high‑resolution, cost‑effective tool for shallow subsurface imaging and environmental monitoring in complex coastal settings.

**重點摘要（繁中）**
作者在美國德爾馬以埋設長14.7公里的光纖，利用列車振動與分佈式聲學感測（DAS）進行近地表剪切波速（VS）成像。透過干涉測量、互相關、波束形成及對每個通道的一維反演，組合成二維層析VS剖面，發現San Dieguito Valley與Los Peñasquitos Lagoon的低速區，對應較厚的沖積與潟湖沉積物。研究也指出VS30與地形高程有明顯相關，海崖處的低VS30與沙含量及沉積物厚度有關，且DAS記錄到的日變應變與溫度變化相關，可協助識別光纖盤放位置。此工作展示了DAS在複雜海岸環境中提供高解析、低成本淺層地球物理成像與環境監測的潛力。

## [3510] Amploc：基於振幅定位的完整 Python 工作流程
**Amploc: A Complete Python Workflow for Amplitude‐Based Locations**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Fri, 28 Aug 2026 00:00:00 GMT
- DOI：10.1785/0220260128/753332
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220260128/753332/Amploc-A-Complete-Python-Workflow-for-Amplitude)

**Summary (EN)**
Amploc is a complete Python workflow for amplitude-based seismic source location that bundles station corrections, established amplitude-based algorithms, and interactive review tools aimed at real-time use. While the algorithms themselves are not new, Amploc integrates several published methods into a unified operational framework and provides a browser-based graphical interface for reviewing results in formats familiar to observatories. By combining calibration, location algorithms, and visualization, Amploc aims to lower the barrier to operational adoption and improve characterization of long-duration, migrating sources such as debris flows, avalanches, rockfall, volcanic tremor, and long-period earthquakes.

**重點摘要（繁中）**
Amploc 是一套完整的 Python 工作流程，用於基於振幅的地震定位，整合了台站校正、既有的振幅定位演算法與互動式審查工具，適用於即時監測。雖然演算法本身並非新創，Amploc 將多種已發表的方法整合成統一的運作框架，並提供瀏覽器介面的圖形工具，讓觀測站以熟悉的格式檢視定位結果。透過結合校準、定位與視覺化，Amploc 可降低實務採用門檻並改善對長時間、可能隨時間移動之源（如碎屑流、雪崩、落石、火山顫動及長週期地震）的特性描述。
