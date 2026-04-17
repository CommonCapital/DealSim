# DealSim

<div align="center">
<img src="./frontend/public/logo/dealsim_logo.png" alt="DealSim Logo" width="600"/>
</div>

Institutional Deal Pressure-Testing Engine
<em>"Given this deal, what breaks first under real capital scrutiny?"</em>


[English](./README.md) | [中文文档](./README-ZH.md)

</div>

## ⚡ Overview

**DealSim** is an institutional-grade pressure-testing engine designed to simulate adversarial capital scrutiny before a GP walks into an IC, a founder meets a lead investor, or a deal team presents to an LP advisory board.

The gap in modern finance is not information; it is **structured adversarial scrutiny** applied early. DealSim fills this gap by allowing you to:
- **Map Investment Claims**: Extract the core logic of a deal into a verifiable graph.
- **Trigger Adversarial Audits**: Deploy specialized "Investment Archetypes" (The Skeptical Institutionalist, The Growth Optimist, The Financial Engineer) to stress-test your assumptions.
- **Identify Fragility**: Discover "what breaks first" through a 5-stage simulated Investment Committee (IC) loop.

---

### 💡 Statement in Plain English

*DealSim* is a software tool that stress-tests investment deals before they face real investors.

**The problem:** When a fund manager or founder walks into an investment committee (IC) or investor meeting, that's usually the first time their deal gets seriously challenged. By then, weeks of work and real credibility are already on the line. Catching flaws that late is expensive and embarrassing.

**What it does:** You upload your pitch deck, financial model, and assumptions memo. The system breaks the deal down into every specific claim you're making — things like "our retention is 120%" or "we'll exit at 12x." It then runs those claims through 50–100 simulated capital allocators (a skeptical VC, a conservative PE partner, a family office, a regulatory reviewer, etc.), each applying their real-world decision criteria. They attack your claims across five structured stages, essentially mimicking what a real IC process looks like.

**The output** is a single clean report telling you: which claims break first, what the most common objections are, what information gaps will get flagged, which investor types would pass vs. proceed, and — crucially — exactly what evidence or changes would flip a "no" into a "maybe."

**The value in one sentence:** It's a rehearsal room for your deal that tells you where you'll get destroyed before you walk into the room where it actually matters.

---

## 🔄 The DealSim 5-Stage Audit

1. **First Look (Quick Sanity Check)**: High-level review of deal structure and surface-level red flags.
2. **Full Pack Review (Detailed Examination)**: Exhaustive analysis of the investment memo and financial model.
3. **Cross-Examination (Adversarial Interrogation)**: Intensive questioning by agents with conflicting mandates (e.g., Growth vs. Capital Preservation).
4. **Diligence Surfacing (Identifying Gaps)**: Synthesizing information that *is not* in the document but *should be*.
5. **Final Verdict (Investment Decision)**: A GO/NO-GO recommendation based on the cumulative pressure-test.


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
