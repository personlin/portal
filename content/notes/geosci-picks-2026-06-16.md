---
title: "GeoSci 精選 2026-06-16"
date: 2026-06-16T08:42:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 3 篇）。

## [2267] 物理監督下之生成式人工智慧自動裂隙反演建模
**Physics‐Supervised Autonomous Inverse Fracture Modeling via Generative Artificial Intelligence**

- 期刊：JGR: Solid Earth (AGU/Wiley) — eTOC
- Published：Thu, 11 Jun 2026 06:03:00 -0700
- DOI：10.1029/2025GL120253
- 原文連結：[連結](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025GL120253?af=R)

**Summary (EN)**
The authors introduce GenFrac, a pre-trained generative AI method based on denoising diffusion for autonomous inversion of fracture networks. GenFrac frames inversion as a conditional denoising process using sparse, noisy observations and geological priors, with a physics-supervised screening step to ensure physical plausibility, and it yields probabilistic ensembles to represent uncertainty. Applied to theoretical geothermal and a real unconfined aquifer case, the method improves reconstruction accuracy and enables efficient, generative parameter inversion conditioned on state observations, while formal uncertainty calibration across diverse settings is left for future work.

**重點摘要（繁中）**
作者提出 GenFrac，一種基於去噪擴散的預訓練生成式 AI，用於自主反演裂隙網路。GenFrac 將反演表述為以稀疏且有噪觀測與地質先驗為條件的去噪過程，並透過物理監督的篩選步驟確保生成場域的物理合理性，且以機率化的樣本集呈現不確定性。該方法在理論地熱與實際不受限含水層案例上都提升了重建精度，並能在狀態觀測條件下有效進行生成式參數反演，且形式化的不確定性校準與跨地質情形的驗證為後續工作方向。

## [2294] 利用完整震源矩張量在超球面上進行地震事件表徵
**Seismic Event Characterization Using Full Moment Tensors on the Hypersphere**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Fri, 12 Jun 2026 00:00:00 GMT
- DOI：10.1785/0220250339/731753
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250339/731753/Seismic-Event-Characterization-Using-Full-Moment)

**Summary (EN)**
The authors compile a catalog of 1,405 full seismic moment tensor solutions (explosions, earthquakes, collapses) and test anisotropic probability distributions on the 5D hypersphere to distinguish source types. Using a Bayesian classifier they achieve an overall success rate of 98.4% and show that adjusting prior probabilities naturally trades off missing target events (e.g., explosions) versus misclassifying common events (e.g., earthquakes). They also report preliminary evidence of subgroupings within source classes on the hypersphere, suggesting future potential to separate, for example, chemical and nuclear explosions as databases grow.

**重點摘要（繁中）**
作者組成一個包含1,405筆完整震源矩解的資料庫（爆炸、地震、坍塌），並在5維超球面上使用各向異性機率分布來區分震源類型。以貝式分類器達到整體98.4%的成功率，並示範調整先驗機率可在不漏檢目標事件（如爆炸）與降低誤判常見事件（如地震）之間取得平衡。研究亦發現初步跡象顯示在超球面上同一類震源內可能存在子群，暗示未來有可能進一步區分例如化學與核爆炸。

## [2295] SDpy：一個用於穩健應力降估計的開源 Python 套件
**SDpy: An Open‐Source Python Package for Robust Stress‐Drop Estimation**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Fri, 12 Jun 2026 00:00:00 GMT
- DOI：10.1785/0220250296/731752
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250296/731752/SDpy-An-Open-Source-Python-Package-for-Robust)

**Summary (EN)**
SDpy is an open‑source Python package for estimating earthquake stress drop using spectral fitting and spectral ratio methods. It supports P, S and coda wave analyses with single- or multi-window approaches, multiple source models (including Brune and Boatwright), and flexible processing scenarios (single/three-component, single/multi-station, and use of empirical Green’s functions), and is modular and extensible. Application to a repeating earthquake sequence at the San Andreas Fault Observatory at Depth produced stress-drop estimates consistent with previous work, demonstrating the tool’s robustness and practical reliability.

**重點摘要（繁中）**
SDpy 是一個開放原始碼的 Python 套件，用於以頻譜擬合與頻譜比方法估算地震應力降。它支援 P 波、S 波及餘波的單窗或多窗分析，包含 Brune 與 Boatwright 等理論源模型，並能處理單或三分量記錄、單或多站資料及單或多個經驗格林函數等多種處理情況，具模組化且可擴充的設計。將 SDpy 應用於 San Andreas Fault Observatory at Depth 的重複地震序列所得估計與先前研究一致，顯示其穩健性與實用可靠性。
