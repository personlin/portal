---
title: "GeoSci 精選 2026-03-30"
date: 2026-03-30T12:00:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 3 篇）。

## [1024] SPIDER：用於雙差地震重定位的可擴展機率推論
**SPIDER: Scalable Probabilistic Inference for Differential Earthquake Relocation**

- 期刊：Earth and Space Science (AGU/Wiley) — eTOC
- Published：Wed, 25 Mar 2026 05:58:33 -0700
- DOI：10.1029/2025JB032769
- 原文連結：[連結](https://onlinelibrary.wiley.com/doi/10.1029/2025JB032769?af=R)

**Summary (EN)**
Seismicity catalogs have grown hugely, but Bayesian double‐difference earthquake relocation struggles to scale to the millions of parameters involved. The authors introduce SPIDER, a scalable Bayesian framework for double‐difference hypocenter relocation that pairs a physics‑informed neural network Eikonal solver with Stochastic Gradient Langevin Dynamics to generate posterior samples jointly for entire catalogs. SPIDER explicitly whitens residual correlations that traditional formulations neglect, is designed for multi‑GPU parallelization, and is demonstrated on a synthetic catalog and three real catalogs from California and Japan, with proposed tools to analyze high‑dimensional posteriors.

**重點摘要（繁中）**
地震目錄規模大幅增加，但傳統的貝式雙差定位在面對可能達百萬參數的問題時無法有效擴展。作者提出 SPIDER，一個可擴展的雙差震源定位貝式框架，結合物理導向的神經網路 Eikonal 解算器與隨機梯度朗之文動力學（SGLD）取樣器，以對整個地震目錄聯合取樣後驗分布。SPIDER 的方法會將傳統作法忽略的殘差相關進行白化，支援多 GPU 平行運算，並在合成與三個真實（加州與日本）目錄上示範，且提供多種分析高維後驗分布的工具。

## [1043] 來自全球新構造動力模型的斷層摩擦、板塊流變與地函力矩
**Fault Friction, Plate Rheology, and Mantle Torques From a Global Dynamic Model of Neotectonics**

- 期刊：Earth and Space Science (AGU/Wiley) — eTOC
- Published：Thu, 26 Mar 2026 23:54:13 -0700
- DOI：10.1029/2025JB032949
- 原文連結：[連結](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025JB032949?af=R)

**Summary (EN)**
Using an improved global thin‑shell finite‑element model, the study finds that modeled faults (other than subduction megathrusts) have very low effective friction (0.085 ± 0.034) and that the average down‑dip integral of shear traction on megathrusts is 1.3 ± 0.2 × 10^12 N/m. The results show continental crust dislocation‑creep strength about twice that of granodiorite (close to diorite), upper‑mantle creep strength similar to olivine‑rich peridotite, and that Byerlee's law friction (0.85) applies within plate interiors. Computed net slab‑pull is typically comparable to ridge‑push (up to five times larger in some cases), usually drives plates toward the trench, and basal tractions beneath large plates without slabs are 0.1–1.2 MPa; implications include weakened plate‑boundary faults from low‑friction minerals and high pore pressure, stronger plate interiors, and the need for faults, laboratory flow‑laws, and Mohr‑Anderson friction in future models.

**重點摘要（繁中）**
利用改良的全球薄殼有限元素模型，研究發現除隱沒巨推（megathrusts）外，模擬的斷層有效摩擦係數非常低（0.085 ± 0.034），而隱沒巨推的下探方向剪應力積分平均為1.3 ± 0.2 × 10^12 N/m。結果顯示大陸地殼的位移蠕變強度約為 granodiorite 的兩倍（接近 diorite），上地幔的蠕變強度則接近富橄欖石的 peridotite；板內活動斷層遵循 Byerlee 定律（摩擦係數0.85）。計算的板俯衝拉力通常與脊推相當（有時可達五倍），多數情況使板塊朝海溝移動，未連接俯衝板塊的大型板塊下方基底牽引為0.1–1.2 MPa；推論包括板界斷層因低摩擦礦物與孔隙壓力而被削弱、板內較為強健，以及未來模擬應加入斷層元素、採用實驗流變定律和 Mohr‑Anderson 摩擦模型。

## [1080] 用於三維地質建模與不確定性評估的 U 形多尺度特徵融合網路
**U-shaped multi-scale feature fusion network for three-dimensional geological modelling and uncertainty assessment**

- 期刊：Earth-Science Reviews (ScienceDirect)
- DOI：10.1016/j.enggeo.2026.108727
- 原文連結：[連結](https://www.sciencedirect.com/science/article/pii/S0013795226001869?dgcid=rss_sd_all)

**Summary (EN)**
The paper presents a hybrid deep learning model called the U-shaped multi-scale feature fusion network (UFFN) that combines CNN and Transformer elements to integrate geophysical and borehole data for 3D geological modelling. The UFFN uses a U-shaped encoder–decoder with parallel multi-scale feature extraction and hierarchical fusion to produce pixel-wise stratigraphic predictions that are reassembled into a volumetric model, and uncertainty is assessed via Monte Carlo dropout. Evaluation on a real engineering case shows the model delineated five stratigraphic units, detected sparsely distributed karst cavities near the limestone top, and achieved 74.68% accuracy for subsurface stratigraphic spatial extrapolation, with higher uncertainty near interfaces and cavity boundaries.

**重點摘要（繁中）**
本文提出一種名為 U-shaped multi-scale feature fusion network（UFFN）的混合深度學習模型，結合 CNN 與 Transformer 來整合地球物理與鑽孔資料以進行三維地層建模。UFFN 採用 U 型編碼器—解碼器結構，透過平行的多尺度特徵擷取與階層融合產生像素級地層預測，並將預測剖面重組為體積模型，同時以 Monte Carlo dropout 量化不確定性。實際工程案例結果顯示該模型描繪出五個地層單元、識別出石灰岩頂部附近的散佈喀斯特空洞，對地層外推的準確率為 74.68%，不確定性主要集中在地層界面及空洞邊界。
