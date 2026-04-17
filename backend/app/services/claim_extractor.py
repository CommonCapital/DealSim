"""
DealSim Claim Extractor Service
Decomposes deal documents into a structured knowledge graph of claims, evidence, and risks.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction

logger = logging.getLogger('dealsim.claim_extractor')

CLAIM_ONTOLOGY_PROMPT = """你是一个专业的私募股权和风险投资（PE/VC）投资分析师，专门负责撰写投审会（IC）预备报告。
你的任务是将提供的交易文档（路演PPT、财务模型、假设场景）分解为一个高度逻辑化的「权利主张图谱」（Claim Graph）。

## 核心任务
识别并提取文档中所有重大的、可验证的断言（Claims），并建立它们之间的逻辑关系。

## 节点类型（Node Types）
1. **Claim (主张)**: 一个关于交易的、可被证实或证伪的陈述。
   - 示例: "2024年净收入留存率超过120%", "到第3年进入企业级市场"。
2. **Evidence (证据)**: 支持某个主张的具体数据、事实或来源。
   - 示例: "2024财年经审计财报", "已签署的意向书"。
3. **Assumption (假设)**: 某个主张成立所必须满足的外部条件或隐性前提。
   - 示例: "市场整体估值倍数维持在15x", "政策限制在明年放宽"。
4. **Risk (风险)**: 对某个主张或整个交易构成威胁的因素。
   - 示例: "前三大客户贡献了71%的收入", "核心创始人锁定期较短"。
5. **Dependency (依赖)**: 指向另一个必须先成立的逻辑节点。

## 关系类型（Edge Types）
- **SUPPORTS**: 证据支持主张回，或主张A支持主张B。
- **REQUIRES**: 主张A的成立必须依赖于节点B。
- **CONTRADICTS**: 两个节点之间存在逻辑冲突或内部张力。
- **UNSUBSTANTIATED**: 主张缺乏证据支持的情况（逻辑标记）。

## 输出要求
你必须输出有效的JSON格式数据，包含以下结构：

```json
{
    "nodes": [
        {
            "id": "节点唯一ID（英文，如 claim_01）",
            "type": "Claim | Evidence | Assumption | Risk | Dependency",
            "content": "节点具体内容描述",
            "importance": 1-10 (该项对交易成败的重要性),
            "attributes": {
                "source": "文档来源/页码",
                "category": "Market | Financial | Team | Product | Governance"
            }
        }
    ],
    "edges": [
        {
            "source": "源节点ID",
            "target": "目标节点ID",
            "type": "SUPPORTS | REQUIRES | CONTRADICTS",
            "reason": "建立此关系的逻辑说明"
        }
    ],
    "analysis_summary": "对该交易逻辑骨架的总体评价"
}
```

## 设计准则
- **原子性**: 每个Claim应该是独立的逻辑单位。
- **关联性**: 重点寻找证据与主张之间的连接，以及假设如何支撑高估值。
- **批判性**: 作为一个“审读人”，关注那些听起来很美但缺乏支撑的断言。
- **数量管理**: 提取30-50个核心节点。
"""

class ClaimExtractor:
    """
    DealSim Claim Extractor
    分析交易文档并构建逻辑图谱
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
    
    def extract(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行提取逻辑
        """
        combined_text = "\n\n---\n\n".join(document_texts)
        
        # 截断处理（针对LLM窗口限制）
        MAX_LEN = 40000 
        if len(combined_text) > MAX_LEN:
            combined_text = combined_text[:MAX_LEN] + "\n...(Text truncated for analysis)..."
            
        user_message = f"""## 交易背景/模拟需求
{simulation_requirement}

## 交易文档内容
{combined_text}

## 额外上下文
{additional_context or "无"}

请分析上述内容，构建该交易的 Claim Graph。重点关注：
1. 核心增长逻辑及其支撑证据
2. 财务模型中的关键假设
3. 潜在的结构性风险
4. 内部逻辑矛盾点
"""

        lang_instruction = get_language_instruction()
        system_prompt = f"{CLAIM_ONTOLOGY_PROMPT}\n\n{lang_instruction}\nIMPORTANT: Node IDs must be lowercase alphanumeric. Content should be in the specified language."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 调用LLM
        result = self.llm_client.chat_json(
            messages=messages,
            temperature=0.2, # 降低随机性，保证逻辑严密
            max_tokens=4096
        )
        
        return self._post_process(result)

    def _post_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """校验并清理结果"""
        if "nodes" not in result:
            result["nodes"] = []
        if "edges" not in result:
            result["edges"] = []
            
        # 确保 ID 唯一且被引用正确
        node_ids = {n["id"] for n in result["nodes"]}
        valid_edges = []
        for edge in result["edges"]:
            if edge["source"] in node_ids and edge["target"] in node_ids:
                valid_edges.append(edge)
        result["edges"] = valid_edges
        
        return result
