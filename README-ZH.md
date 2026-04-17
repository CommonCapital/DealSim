<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="DealSim Logo" width="75%"/>

DealSim：机构级交易压力测试引擎
</br>
<em>「给定这笔交易，在真实的资本严审下，什么会首先崩溃？」</em>

[![GitHub Stars](https://img.shields.io/github/stars/666ghj/DealSim?style=flat-square&color=DAA520)](https://github.com/666ghj/DealSim/stargazers)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)

[English](./README.md) | [中文文档](./README-ZH.md)

</div>

## ⚡ 项目概述

**DealSim** 是一款机构级的交易压力测试引擎，旨在 GP 进入投审会（IC）、创始人会见领投人或交易团队向 LP 咨询委员会汇报之前，模拟真实的对抗性资本审查。

现代金融的缺口不在于信息，而在于**早期应用结构化的对抗性审查**。DealSim 通过以下功能填补了这一空白：
- **交易主张映射 (Claim Mapping)**：将交易的核心逻辑提取为可验证的图谱。
- **触发对抗性审计 (Adversarial Audits)**：部署专业的「投资原型」(如保守建制派、增长乐观派、财务工程师) 来压力测试您的假设。
- **识别脆弱性 (Fragility Identification)**：通过 5 阶段模拟投审会 (IC) 循环，发现「什么会首先崩溃」。

## 🔄 DealSim 5 阶段审计流程

1. **初步审查 (First Look)**：对交易结构进行高层次评估，识别表面的红旗风险。
2. **全套资料评审 (Full Pack Review)**：对投资建议书 (Memo) 和财务模型进行详尽检查。
3. **交叉质询 (Cross-Examination)**：由持有冲突授权（如增长 vs 资本保值）的 Agent 进行深度对抗性互动。
4. **尽调重点识别 (Diligence Surfacing)**：合成文档中*未提及*但*应当具备*的关键信息缺口。
5. **最终裁决 (Final Verdict)**：基于累积的压力测试结果，给出明确的 GO/NO-GO 投资建议。

## 📸 系统截图

*(当前 UI 聚焦于审计模式和 IC 准备报告的自动合成)*

<div align="center">
<table>
<tr>
<td><img src="./static/image/Screenshot/运行截图1.png" alt="DealSim 步骤 1" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图2.png" alt="DealSim 步骤 2" width="100%"/></td>
</tr>
</table>
</div>

## 🚀 快速开始

### 1. 前置要求
- **Node.js** 18+
- **Python** 3.11+
- **uv** (快速 Python 包管理器)

### 2. 配置环境
```bash
cp .env.example .env
# 填写您的 LLM_API_KEY (兼容 OpenAI 格式) 和 ZEP_API_KEY
```

### 3. 部署
```bash
# 安装所有依赖
npm run setup:all

# 启动本地开发服务
npm run dev
```

## 📄 架构与投资原型 (Archetypes)

DealSim 从传统的「性格驱动型」AI 转向了**「授权驱动型」(Mandate-driven) AI**。投审会中的每个人设都受特定投资授权的约束：
- **保守建制派 (The Skeptical Institutionalist)**：关注下行保护和资本保值。
- **财务工程师 (The Financial Engineer)**：痴迷于 EBITDA 利润率和退出倍数。
- **困境反转专家 (The Distressed Specialist)**：寻找交易崩溃点以寻找入场价值。

## 📄 致谢

DealSim 的仿真引擎由 **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)** 驱动。我们由衷感谢 CAMEL-AI 团队的开源贡献。

---
© 2026 DealSim. 机构级交易压力测试引擎.
