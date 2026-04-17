"""
DealSim Mandate Persona Generator
Generates institutional IC member profiles based on investment mandates.
Represents a shift from "Personality-based" agents to "Constraint-based" decision frameworks.
"""

import json
import random
import logging
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction

logger = logging.getLogger('dealsim.mandate_generator')

# Investment Archetypes Definition
INVESTMENT_ARCHETYPES = [
    {"name": "Conservative PE Partner", "description": "Downside protection, EBITDA-focused, sensitive to leverage ratios.", "mandate": "Capital Preservation & Steady Yield"},
    {"name": "Growth Equity Partner", "description": "Focuses on unit economics, TAM expansion, and rule of 40.", "mandate": "Aggressive Growth / Series B+ Expansion"},
    {"name": "Tiger-Cub Style PM", "description": "High-velocity, aggressive crossover investor, focuses on public market comparables.", "mandate": "High Alpha / Late Stage Growth"},
    {"name": "Skeptical Venture Investor", "description": "Deep tech bias, focuses on product-market fit and defensibility.", "mandate": "Early Stage Innovation"},
    {"name": "Family Office CIO", "description": "Long-term horizon, mission-aligned, sensitive to reputation.", "mandate": "Generational Wealth / Wealth Preservation"},
    {"name": "Sovereign Allocator", "description": "Strategic macroeconomic perspective, huge check size, governance-heavy.", "mandate": "Long-term Strategic Alpha"},
    {"name": "Endowment LP", "description": "Highly structured, 10-year horizon, focuses on manager track record.", "mandate": "Diversified Alternative Assets"},
    {"name": "Secondaries Buyer", "description": "Discount-driven, focuses on DPI and liquidity timing.", "mandate": "Opportunistic Liquidity"},
    {"name": "Ex-Operator Board Member", "description": "Pokes holes in delivery, execution risk, and management team capability.", "mandate": "Operational Efficiency & Delivery"},
    {"name": "CFO / Finance Diligence Lead", "description": "Audit-focused, verifies accounts receivable, burn rate, and tax exposure.", "mandate": "Financial Integrity"},
    {"name": "Procurement Buyer", "description": "Asks: 'Would I actually buy this product?' Focuses on sales cycle and switching costs.", "mandate": "Market Pragmatsim"},
    {"name": "Competitor Strategist", "description": "Predicts incumbent reaction and pricing wars.", "mandate": "Market Share Defense"},
    {"name": "Regulator / Compliance Reviewer", "description": "Focuses on antitrust, data privacy (GDPR), and ESG compliance.", "mandate": "Legal & Regulatory Compliance"}
]

MANDATE_SYSTEM_PROMPT = """你是一个专业的机构投资决策顾问。
你的任务是为投审会（IC Room）模拟生成具有特定投资“授权”（Mandate）的决策者人设。

## 核心原则
传统的社交模拟人设关注性格（MBTI），但 DealSim 关注决策框架。
你生成的人设必须由其「投资授权」和「约束条件」驱动，而不是情绪。

## 决策维度 (Mandate Dimensions)
1. **Check Size (支票规模)**: 该成员代表的机构单笔投资容量。
2. **Return Threshold (回报阈值)**: 核心 IRR、现金回报倍数 (MoC) 或 DPI 要求。
3. **Stage Preference (阶段偏好)**: 早期、成长期、成熟期或二级市场。
4. **Loss Aversion Profile (损失厌恶)**: 对本金亏损的恐惧程度与容忍度。
5. **Sector Bias (行业偏见)**: 基于过往经验的行业喜好或刻板印象。
6. **Time Horizon (时间地平线)**: 退出周期（如：3-5年 vs 10年以上）。
7. **Portfolio Construction Logic (组合构建逻辑)**: 该投资如何拟合其现有资产配置。
8. **Governance Sensitivity (治理敏感度)**: 对董事会席位、投后管理和合规的要求。
9. **Exit Expectations (退出预期)**: IPO、并购或 S-Round 偏好。

## 输出要求
你必须输出有效的JSON格式数据，模拟一个具体的IC成员：

```json
{
    "name": "姓名/代号",
    "title": "MD | Partner | Director | LP Observer",
    "archetype": "来自Archetype列表的名称",
    "mandate_description": "该成员的具体投资使命及其关键决策参数（如支票规模、退出预期等，300字）",
    "decision_logic": {
        "check_size": "量化描述",
        "return_threshold": "如 >20% IRR",
        "stage_preference": "Early | Growth | Buyout",
        "loss_aversion_profile": "High | Medium | Low",
        "sector_bias": "如: 软件行业偏好",
        "time_horizon": "如: 7-10 Years",
        "portfolio_logic": "如: 核心多样化资产",
        "governance_sensitivity": "High | Medium | Low",
        "exit_expectations": "IPO preference"
    },
    "persona": "用于LLM模拟的核心Prompt（极其详细，包含其审查Claim时的攻击性风格。必须明确提及他们如何使用上述9个维度进行审判）",
    "bio": "简短背景说明"
}
```

## 模拟风格
- **攻击性**: IC成员应该是批判性的，他们不是在聊天，而是在质询。
- **专业性**: 使用金融术语，关注结构、条款和宏观风险。
"""

class MandatePersonaGenerator:
    """
    Mandate Persona Generator
    将通用的 Archetype 转化为具体的 IC 成员 Account Profile
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        
    def generate_mandate_profiles(
        self,
        claim_context: str,
        simulation_requirement: str,
        count: int = 60
    ) -> List[Dict[str, Any]]:
        """
        批量生成 Mandate Profiles (V1 Multiplier Logic)
        1. 选取 12-20 个基础 Archetypes
        2. 每个 Archetype 扩展为 3-8 个差异化实例
        3. 总计 50-100 个决策者人设
        """
        logger.info(f"Generating expanded mandate personas (target ~{count})...")
        
        # 选取基础 Archetypes (全量选取或抽样)
        base_archetypes = INVESTMENT_ARCHETYPES
        archetype_count = len(base_archetypes)
        
        # 计算每个 Archetype 需要生成的实例数
        # 如果总数是 60，13 个 Archetype，则大约每个 4-5 个
        instances_per_archetype = max(1, count // archetype_count)
        
        all_profiles = []
        
        # 为了效率，我们让 LLM 一次性生成多个实例，或者循环生成
        # 这里采用循环生成以保证质量，或者在一个 Prompt 中生成 instance sets
        for arch in base_archetypes:
            arch_instances = self._generate_archetype_instances(
                arch=arch,
                claim_context=claim_context,
                simulation_requirement=simulation_requirement,
                instance_count=instances_per_archetype
            )
            all_profiles.extend(arch_instances)
            
        # 限制在 100 以内
        return all_profiles[:100]

    def _generate_archetype_instances(
        self,
        arch: Dict[str, str],
        claim_context: str,
        simulation_requirement: str,
        instance_count: int
    ) -> List[Dict[str, Any]]:
        """为特定 Archetype 生成多个差异化实例"""
        logger.info(f"Expanding archetype '{arch['name']}' into {instance_count} instances...")
        
        user_message = f"""## 基础 Archetype
名称: {arch['name']}
基本描述: {arch['description']}
核心授权: {arch['mandate']}

## 交易上下文
{claim_context[:2000]}

## 任务
请基于上述 Archetype，生成 {instance_count} 个具有差异化的具体投资决策者人设。
这些实例必须共享上述背景，但在 9 个决策维度上应有微小差异（例如：一个更稳健，一个更激进）。
"""

        lang_instruction = get_language_instruction()
        system_prompt = f"{MANDATE_SYSTEM_PROMPT}\n\n{lang_instruction}\nIMPORTANT: Return a list of JSON objects inside a 'profiles' key."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            result = self.llm_client.chat_json(messages=messages, temperature=0.7)
            profiles = result.get("profiles", [])
            
            # 补齐必要字段
            for i, p in enumerate(profiles):
                p["user_id"] = random.randint(10000, 99999)
                p["username"] = f"{arch['name'].lower().replace(' ', '_')}_{i:02d}_{random.randint(10, 99)}"
                if "persona" not in p:
                    p["persona"] = p.get("mandate_description", "")
                
            return profiles
        except Exception as e:
            logger.error(f"Failed to generate instances for {arch['name']}: {e}")
            return []


    def _get_fallback_profiles(self, count: int) -> List[Dict[str, Any]]:
        """回退逻辑：基于预定义的 Archetypes 生成"""
        profiles = []
        for i in range(count):
            arch = random.choice(INVESTMENT_ARCHETYPES)
            profiles.append({
                "user_id": 1000 + i,
                "username": f"ic_member_{i:02d}",
                "name": f"Partner {i+1}",
                "title": "Investment Partner",
                "archetype": arch["name"],
                "bio": arch["description"],
                "mandate_description": arch["mandate"],
                "persona": f"You are an investment partner acting as a {arch['name']}. {arch['description']}"
            })
        return profiles
