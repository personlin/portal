---
title: "GeoSci 精選 2026-08-28"
date: 2026-08-28T12:00:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 1 篇）。

## [3487] 使用圖神經網路建模非遍歷地震動
**Modeling Nonergodic Ground Motions Using Graph Neural Networks**

- 期刊：Bulletin of the Seismological Society of America — Advance Access
- Published：Wed, 26 Aug 2026 00:00:00 GMT
- DOI：10.1785/0120260030/747563
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/bssa/article/doi/10.1785/0120260030/747563/Modeling-Nonergodic-Ground-Motions-Using-Graph)

**Summary (EN)**
The authors develop a nonergodic ground‑motion model for southern California by training a graph neural network on about 400,000 CyberShake simulated earthquakes, focusing on long‑period responses for rupture distances up to 200 km. Each rupture is represented as a graph of sites and neighbor connections, and the GNN predicts residuals relative to an ergodic GMM while incorporating site, source, path, absolute locations, and intersite relationships to learn spatially correlated residual patterns. The model captures site‑specific effects such as basin amplification and azimuthal variations, preserves magnitude scaling and period‑dependent trends seen empirically, and in a Ridgecrest Mw 7.1 case study shows lower mean residuals at T=5.0 s and comparable performance at other periods, suggesting promise for hazard analysis.

**重點摘要（繁中）**
作者使用約40萬個CyberShake模擬地震訓練圖神經網路，建立南加州的非遍歷性地震動模型，重點為距震源200公里以內的長週期響應。每次斷層破裂以站點及其鄰近連結構成圖狀結構，GNN對相對於遍歷性GMM的殘差進行預測，並同時納入場址、震源、傳播、絕對座標與站間距離以學習空間相關的殘差模式。該模型能捕捉盆地放大與相對斷層的方位變化等場址特徵，保留與實證關係一致的震級及週期依賴性，在2019年Ridgecrest Mw 7.1個案中於T=5.0 s呈現較低的平均殘差，其他週期表現亦相當，顯示對地震危害分析具潛力。
