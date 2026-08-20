---
title: "GeoSci 精選 2026-08-20"
date: 2026-08-20T12:00:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 1 篇）。

## [3364] TL‐BiRNN‐Pick：基於遷移學習之用於地下礦山的端到端自動化微震監測框架
**TL‐BiRNN‐Pick: An End‐to‐End Automated Microseismic Monitoring Framework for Underground Mines via Transfer Learning**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Tue, 18 Aug 2026 00:00:00 GMT
- DOI：10.1785/0220260072/734959
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220260072/734959/TL-BiRNN-Pick-An-End-to-End-Automated-Microseismic)

**Summary (EN)**
This paper introduces TL-BiRNN-Pick, an end-to-end microseismic monitoring framework that uses transfer learning with a pretrained DiTing 2.0 encoder–decoder and bidirectional RNNs fine-tuned on mining seismic data. The system combines the picker with DBSCAN association, enhanced Geiger localization, and double-difference relocation to produce automated waveform-to-catalog outputs. On 996 mining waveforms it achieved precision 0.947, F1 0.933, RMSE 8.23 ms (SD 15.24 ms), and in a 16-day Dongtan Coal Mine trial detected 1271 events (3–4× more than traditional methods) while improving magnitude of completeness to −1.64 (a 0.24 unit gain).

**重點摘要（繁中）**
本文提出TL-BiRNN-Pick，一個端到端的微震監測框架，透過以DiTing 2.0為預訓練模型的編碼器–解碼器與雙向遞歸神經網路，並對礦區地震資料進行微調的遷移學習方法。系統結合DBSCAN關聯、改良的Geiger定位與雙差重定位，實現自動化的波形到目錄流程。針對996筆礦山波形測得精確率0.947、F1為0.933、RMSE為8.23 ms（標準差15.24 ms），在東灘煤礦16天的實際應用中識別1271個事件（較傳統方法多3–4倍），並將完整度震級改善至−1.64（提升0.24 震級單位）。
