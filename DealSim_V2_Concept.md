# DealSim — Institutional Deal Pressure-Testing Engine
### Product Concept V2

---

## The Single Question This Product Answers

> **"Given this deal, what breaks first under real capital scrutiny?"**

Everything in this product exists to answer that question. Nothing else.

---

## 1. The Problem

Every deal gets pressure-tested eventually. The question is when. By the time a GP walks into an IC, a founder meets a lead investor, or a deal team presents to an LP advisory board, the cost of discovering structural weaknesses is already high: weeks of diligence, legal fees, management bandwidth, and credibility.

The gap is not information. It is structured adversarial scrutiny applied early, before real time and real credibility are spent.

Existing tools don't fill it:
- Generic AI feedback has no mandate specificity
- Expert networks are expensive, slow, and inconsistent
- Internal deal teams share the same biases as the deal itself
- The actual IC is too late to be useful as a test

DealSim fills the gap by simulating the scrutiny before the room.

---

## 2. What DealSim Is

DealSim is a **decision framework simulation engine** for private capital deals.

It is not:
- "Agents with personalities debating"
- A simulated society of investors
- A personality realism engine
- A broad scenario explorer

It is:
- Mandate-specific decision frameworks applied to a specific deal
- Capital allocator objection modeling against structured claim nodes
- Institutional pressure-testing that produces one clean, actionable report

The output is not a curiosity. It reads like real IC prep. It sharpens judgment before the room.

---

## 3. The Input

Three documents. Nothing else required for V1.

| Input | Purpose |
|---|---|
| Pitch deck or CIM | Narrative claims, market framing, competitive positioning, team |
| Financial model | Quantitative assumptions, growth trajectory, unit economics, exit math |
| Assumptions memo | Explicit and implicit conditions the deal depends on |

The system parses all three and extracts every falsifiable assertion in the deal. These become the nodes under attack.

---

## 4. The Claim Extraction Layer

Before any simulation runs, the deal is decomposed into a structured knowledge graph.

**Node types:**

- `Claim` — a falsifiable assertion ("Net revenue retention exceeds 120%")
- `Evidence` — data supporting a claim ("Audited financials, FY2024")
- `Assumption` — implicit condition required for a claim to hold ("Enterprise segment expands by Year 3")
- `Risk` — identified threat to a claim ("Top 3 customers = 71% of ARR")
- `Dependency` — logical chain between claims ("Exit multiple assumption requires market re-rating")

**Edge types:**

- `SUPPORTS` — evidence supports a claim
- `REQUIRES` — claim A cannot hold without claim B
- `CONTRADICTS` — internal tension between two claims
- `UNSUBSTANTIATED` — claim has no evidence node attached

This graph is the deal's logical skeleton. It is what gets attacked. Every simulation output maps back to specific nodes in this graph, producing the claim fragility map.

---

## 5. The Decision Framework Personas

Personas in DealSim are not personalities. They are **mandate-specific decision frameworks** — structured representations of how a specific type of capital allocator evaluates, objects to, and ultimately decides on a deal.

### 5.1 Persona Dimensions (Required for Every Persona)

A persona is not useful unless it carries all of the following:

| Dimension | What it captures |
|---|---|
| Check size range | Minimum / target / maximum deployment per deal |
| Return threshold | Gross MOIC and IRR required to underwrite |
| Stage preference | Seed / early / growth / buyout / secondary |
| Loss aversion profile | Asymmetric upside tolerance vs. capital preservation mandate |
| Sector bias | Pattern-matched sectors vs. avoided sectors |
| Time horizon | Fund life, deployment window, liquidity requirements |
| Portfolio construction logic | Concentration limits, follow-on reserves, diversification rules |
| Governance sensitivity | Control requirements, board seat expectations, consent rights |
| Exit expectations | IPO / strategic / sponsor-to-sponsor / secondary |

### 5.2 The Archetype Set (V1 — Fixed)

**Core investment decision frameworks:**

| Archetype | Decision lens |
|---|---|
| Conservative PE partner | Downside protection, leverage capacity, predictable cash flows, covenant compliance |
| Growth equity partner | Rule of 40, expansion multiples, path to profitability, founder alignment |
| Aggressive crossover / tiger-cub PM | Velocity, public market comparables, re-rating potential, liquidity event timing |
| Skeptical venture investor | Wedge defensibility, TAM credibility, founder-market fit, 10x path |
| Family office CIO | Capital preservation, illiquidity premium, tax efficiency, generational horizon |
| Sovereign allocator | Country risk, governance standards, ESG compliance, long-duration alignment |
| Endowment LP | Vintage year diversification, manager track record, fee structure, DPI expectations |
| Secondaries buyer | NAV discount, portfolio construction, J-curve mitigation, legal transfer complexity |

**Real-world pressure frameworks:**

| Archetype | Attack vector |
|---|---|
| Ex-operator board member | Operational feasibility, org design, customer reality vs. pitch narrative |
| CFO / finance diligence lead | Model integrity, accounting treatment, cash flow assumptions, audit trail |
| Procurement buyer | Vendor switching costs, contract structure, budget cycle reality, champion risk |
| Competitor strategist | Defensibility of moat, build vs. buy calculus, competitive response timeline |
| Regulatory / compliance reviewer | Licensing exposure, data handling, sector-specific regulatory risk |

### 5.3 Population Generation

V1 runs **12 to 20 base archetypes**, each expanded into **3 to 8 differentiated instances** by varying mandate-specific dimensions within realistic bounds.

Total simulation population: **might vary from 50-100 to 1000 decision-maker personas per run.**

This is not personality sampling. It is **mandate space coverage** — ensuring the deal is tested against the realistic distribution of capital allocator decision frameworks it will actually encounter.

There are no hand-written personas. One LLM prompt template takes an archetype definition and a set of varied dimension values and outputs a fully structured decision framework. The archetype library is the only human-maintained artifact.

---

## 6. The Simulation

The simulation environment is the **IC Room** — a single structured environment that mirrors a real deal process, not a social platform.

### Stages

| Stage | What happens |
|---|---|
| 1. First Look | Each persona reads executive summary only. Initial signals logged. |
| 2. Full Pack Review | Each persona reviews full deck, model, and assumptions. Primary objections formed. |
| 3. Structured Cross-Examination | Personas debate claim nodes. Bears challenge bulls. Consensus and divergence mapped. |
| 4. Diligence Surfacing | Each persona lists information they require but do not have. |
| 5. Final Verdict | Each persona submits: proceed / conditional interest / pass — with stated reasoning. |

Each stage produces structured output. The ReportAgent synthesizes across all five stages.

### What the simulation is not

The simulation is not agents posting on Twitter. It is not social dynamics modeling. It is not emergent behavior for its own sake. It is a **structured adversarial interrogation** of every claim node in the deal, executed by mandate-specific decision frameworks, producing evidence for a single report.

---

## 7. The Report

One report. Six sections. No sprawl.

### Section 1 — What Breaks First
The claim fragility map. Ranked list of claim nodes by failure rate across all personas. The top items are the deal's structural vulnerabilities. These are the things that will be attacked first in every real room.

### Section 2 — Top Objections
Clustered objection table. Grouped by theme: unit economics / market size / competitive moat / team / exit path / governance. Frequency-weighted. Each objection mapped to the archetype types that raised it most consistently.

### Section 3 — Missing Diligence
Ranked registry of information gaps surfaced during the diligence surfacing stage. Items that appeared across multiple archetype types are flagged as critical. Items unique to one type are flagged as archetype-specific concerns.

### Section 4 — Split by Persona Type
Breakdown of verdict distribution across the 12-20 archetypes. Which types are most likely to proceed, which are most likely to pass, and why. Shows where the deal has natural constituency and where it faces structural resistance.

### Section 5 — What Evidence Would Change Minds
For each top objection and each broken claim node: what specific evidence, data, or narrative reframing would move the most decision frameworks from no to conditional interest. This is the actionable section — it tells the deal team exactly what to go build or find.

### Section 6 — Investment Committee Recommendation
A synthesized, directional judgment: Is this deal fundable as presented? What are the one to three changes that would materially improve its IC survivability? What is the single most dangerous unresolved question? Written to read like a senior associate's IC prep note — not a chatbot summary.

---

## 8. Technical Architecture

### Pipeline

```
Upload (deck + model + assumptions memo)
        ↓
claim_extractor.py
LLM decomposes documents into claim graph nodes
        ↓
graph_builder.py
Builds deal knowledge graph (Claim / Evidence / Risk / Assumption / Dependency)
        ↓
persona_generator.py
Generates usually 50-100 mandate-specific decision framework instances from archetype library, but in some rare cases it can go up to 1000, depending on the deal size and complexity
        ↓
OASIS simulation engine (CAMEL-AI)
IC Room environment: 5 structured stages, agents attack claim nodes
        ↓
diligence_report_agent.py
ReACT-style synthesis across simulation output
        ↓
Report (6 sections) + Objection Table + Diligence List + Claim Fragility Map
```

### What is forked from Dealsim

| DealSim component | DealSim replacement |
|---|---|
| `entity_extractor.py` | `claim_extractor.py` |
| Social world ontology | Deal logic ontology |
| MBTI social persona template | Mandate-specific decision framework template |
| Twitter / Reddit environment | IC Room 5-stage environment |
| Social dynamics report | 6-section IC prep report |

**Kept unchanged:** OASIS simulation engine, graph storage layer, persona generation loop, Flask/Vue scaffold, ReportAgent pattern.

### LLM Layer (Free Tier — V1)

- **Gemini 1.5 Flash** (Google AI Studio) — primary. Free. 1M tokens/day. Sufficient for 100-persona runs.
- **Groq + Llama 3.3 70B** — fallback. Free tier. Fast inference.

A V1 run (100 personas × 5 stages × ~1,500 tokens each) sits at approximately 750,000 tokens per full simulation — within Gemini's free daily limit.

### Infrastructure (Zero cost to start)

- Backend: Railway or Render free tier
- Frontend: Vercel
- Everything else similar to Dealsim.


---

## 9. Build Sequence — V1 Prototype (6 steps )

### 1. Claim Extraction
Write `claim_extractor.py`. Validate on three real decks. Target: 20-40 clean claim nodes per document set, correctly typed and linked. This is the foundation. If extraction is weak, the simulation is weak.

### 2. Archetype Library + Persona Generator
Write the 12-20 archetype definitions with all required mandate dimensions. Write the persona generation prompt. Generate 50 instances. Review manually for decision-framework fidelity — not personality realism.

### 3. Simulation
Configure IC Room environment in OASIS. Run first full simulation: 50 personas × 1 real deal. Review logs. Are personas attacking claim nodes or drifting into general commentary? Tune until the interrogation is disciplined.

### 4. Report
Build `diligence_report_agent.py`. Lock the six-section output schema. Run five different deals. Evaluate: does the report read like real IC prep? Would a deal team act on it?

### 5. Interface
Minimal upload interface. Simulation progress indicator. Report renderer. Claim fragility map visualization (D3 force graph, nodes colored by failure rate). "Interrogate a persona" feature — ask any decision framework why it passed.

---

## 10. What This Is Not

To stay disciplined, the following are explicitly out of scope for V1:

- Broad scenario simulation or open-ended agent worlds
- Social dynamics or opinion propagation modeling
- Hundreds of "personality" dimensions unrelated to capital allocation mandates
- Real-time data feeds or market integration
- Any feature that makes this a research project rather than a decision tool

---

## 11. Strategic Relevance to MuseData ( Instance of first production case )

MuseData's value is backward-looking: what has happened, who has done what, track records, comparables.

DealSim's value is forward-looking: given this deal, what happens next when it meets real scrutiny.

The integration thesis is clean:

1. MuseData's historical GP behavioral data calibrates DealSim's archetype dimensions with empirical grounding instead of synthetic assumptions
2. DealSim's simulation output feeds back into MuseData as a deal quality signal layer — a forward-looking dimension on top of the existing data infrastructure
3. The combined offering becomes: *historical GP behavior (MuseData) + pre-deal institutional pressure test (DealSim)* — a private markets intelligence layer that covers both what has happened and what is about to be tested

That is a differentiated product. Neither half is complete without the other.

---

## 12. The One-Line Pitch

> *DealSim runs your deal through the IC before you walk into the room.*

---

*Version 2.0 — April 2026. Scope locked. Build against this.*
