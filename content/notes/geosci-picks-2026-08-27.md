---
title: "GeoSci 精選 2026-08-27"
date: 2026-08-27T12:00:00+08:00
tags: ["geosci", "papers"]
categories: ["notes"]
---

本日選文（共 1 篇）。

## [3484] 基於 XML 資料庫的開源 FDSN 站台 Web 服務實作：exist-fdsn-station
**An Open‐Source XML Database‐Based Implementation of the FDSN Station Webservice: exist‐fdsn‐station**

- 期刊：Seismological Research Letters (SRL) — Advance Access
- Published：Tue, 25 Aug 2026 00:00:00 GMT
- DOI：10.1785/0220250003/747491
- 原文連結：[連結](https://pubs.geoscienceworld.org/ssa/srl/article/doi/10.1785/0220250003/747491/An-Open-Source-XML-Database-Based-Implementation)

**Summary (EN)**
The paper presents an extension to the FDSN fdsnws-station API that adds controlled operations for interacting with StationXML metadata repositories, enabling direct handling of StationXML within distributed service-oriented infrastructures. The authors implemented the interface as exist-fdsn-station using a native XML database and embedded application platform, allowing schema-less ingestion of heterogeneous metadata while preserving XML structure, and packaging the software as a containerized reusable component. Performance tests show predictable scaling with returned data size and suitability for large aggregated metadata collections, and the software is already used operationally at the INGV data center, including its public fdsnws-station endpoint.

**重點摘要（繁中）**
本文提出對 FDSN fdsnws-station API 的擴展，新增可控操作以直接與 StationXML 格式的測站描述資料庫互動，支援在分散式服務導向架構中處理 StationXML 文件。作者以原生 XML 資料庫與嵌入式應用平台實作 exist-fdsn-station，使無模式資料庫能自異質來源攝取並保留 XML 結構，並將軟體容器化以作為可重用元件。效能測試顯示系統隨回傳資料量可預測地擴展，適用於大型彙整的記錄集，且已在 INGV 資料中心的營運環境（含公開 fdsnws-station 服務端點）投入使用。
