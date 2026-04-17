<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="DealSim Logo" width="75%"/>

Institutional Deal Pressure-Testing Engine
</br>
<em>"Given this deal, what breaks first under real capital scrutiny?"</em>

[![GitHub Stars](https://img.shields.io/github/stars/666ghj/DealSim?style=flat-square&color=DAA520)](https://github.com/666ghj/DealSim/stargazers)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)

[English](./README.md) | [中文文档](./README-ZH.md)

</div>

## ⚡ Overview

**DealSim** is an institutional-grade pressure-testing engine designed to simulate adversarial capital scrutiny before a GP walks into an IC, a founder meets a lead investor, or a deal team presents to an LP advisory board.

The gap in modern finance is not information; it is **structured adversarial scrutiny** applied early. DealSim fills this gap by allowing you to:
- **Map Investment Claims**: Extract the core logic of a deal into a verifiable graph.
- **Trigger Adversarial Audits**: Deploy specialized "Investment Archetypes" (The Skeptical Institutionalist, The Growth Optimist, The Financial Engineer) to stress-test your assumptions.
- **Identify Fragility**: Discover "what breaks first" through a 5-stage simulated Investment Committee (IC) loop.

## 🔄 The DealSim 5-Stage Audit

1. **First Look (Quick Sanity Check)**: High-level review of deal structure and surface-level red flags.
2. **Full Pack Review (Detailed Examination)**: Exhaustive analysis of the investment memo and financial model.
3. **Cross-Examination (Adversarial Interrogation)**: Intensive questioning by agents with conflicting mandates (e.g., Growth vs. Capital Preservation).
4. **Diligence Surfacing (Identifying Gaps)**: Synthesizing information that *is not* in the document but *should be*.
5. **Final Verdict (Investment Decision)**: A GO/NO-GO recommendation based on the cumulative pressure-test.

## 📸 System Screenshots

*(UI currently focused on Audit Mode and IC Prep Report synthesis)*

<div align="center">
<table>
<tr>
<td><img src="./static/image/Screenshot/运行截图1.png" alt="DealSim Step 1" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图2.png" alt="DealSim Step 2" width="100%"/></td>
</tr>
</table>
</div>

## 🚀 Quick Start

### 1. Prerequisites
- **Node.js** 18+
- **Python** 3.11+
- **uv** (Fast Python package manager)

### 2. Configure Environment
```bash
cp .env.example .env
# Fill in your LLM_API_KEY (OpenAI compatible) and ZEP_API_KEY
```

### 3. Deployment
```bash
# Install all dependencies
npm run setup:all

# Start local dev server
npm run dev
```

## 📄 Architecture & Archetypes

DealSim shifts from personality-driven AI to **Mandate-driven AI**. Each "Persona" in the IC Room is bound by a specific investment mandate:
- **The Skeptical Institutionalist**: Focuses on downside protection and capital preservation.
- **The Financial Engineer**: Obsessed with EBITDA margins and exit multiples.
- **The Distressed Specialist**: Looks for where the deal breaks to find entry value.

## 📄 Acknowledgments

DealSim's simulation engine is powered by **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)**. We sincerely thank the CAMEL-AI team for their foundational work.

---
© 2026 DealSim. Institutional Deal Pressure-Testing Engine.
# DealSim
