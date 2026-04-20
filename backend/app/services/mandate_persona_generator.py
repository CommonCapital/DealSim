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

MANDATE_SYSTEM_PROMPT = """You are a professional institutional investment decision consultant.
Your task is to generate detailed decision-maker personas for an IC Room (Investment Committee) simulation, each driven by specific investment "Mandates."

## Core Principles
Traditional social simulation personas focus on personality (MBTI), but DealSim focus on "Decision Frameworks."
The personas you generate must be driven by their "Investment Mandates" and "Constraints," not social emotions.

## Mandate Dimensions
1. **Check Size**: The single investment capacity of the institution this member represents.
2. **Return Threshold**: Core IRR, Cash-on-Cash (MoC), or DPI requirements.
3. **Stage Preference**: Early, Growth, Buyout, or Secondary market.
4. **Loss Aversion Profile**: Fear profile regarding principal loss tolerance.
5. **Sector Bias**: Industry preferences or biases based on historical track record.
6. **Time Horizon**: Exit cycle (e.g., 3-5 years vs. 10+ years).
7. **Portfolio Construction Logic**: How this investment fits into their existing asset allocation.
8. **Governance Sensitivity**: Requirements for board seats, post-investment management, and compliance.
9. **Exit Expectations**: IPO, M&A, or S-Round preference.

## Output Requirements
You must return valid JSON representing a specific IC member:

```json
{
    "name": "Full Name / Handle",
    "title": "MD | Partner | Director | LP Observer",
    "archetype": "Name from Archetype list",
    "mandate_description": "Specific investment mission and key parameters of this member (e.g., check size, exit expectations, 300 words)",
    "decision_logic": {
        "check_size": "Quantitative description",
        "return_threshold": "e.g., >20% IRR",
        "stage_preference": "Early | Growth | Buyout",
        "loss_aversion_profile": "High | Medium | Low",
        "sector_bias": "e.g., Strategic bias towards SaaS",
        "time_horizon": "e.g., 7-10 Years",
        "portfolio_logic": "e.g., Core diversified assets",
        "governance_sensitivity": "High | Medium | Low",
        "exit_expectations": "IPO preference"
    },
    "persona": "Core prompt for LLM simulation (Extremely detailed, including their aggressive scrutiny style. Explicitly mention how they use the 9 dimensions to judge claims)",
    "bio": "Brief background summary"
}
```

## Simulation Style
- **Aggressive**: IC members should be critical; they are not chatting, they are interrogating.
- **Professional**: Use finance terminology, focus on structure, covenants, and macro risks.
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
        
        # To be efficient, we generate multiple instances at once
        # For quality control, we loop through archetypes and generate sets
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
        
        user_message = f"""## Base Archetype
Name: {arch['name']}
Description: {arch['description']}
Core Mandate: {arch['mandate']}

## Deal Context
{claim_context[:2000]}

## Task
Based on the above Archetype, generate {instance_count} differentiated investment decision-maker profiles.
These instances must share the same background but have slight differences in the 9 mandate dimensions (e.g., one being more conservative, another more aggressive).
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
                
                # Fix for UI mapping: map title to profession
                if "title" in p and "profession" not in p:
                    p["profession"] = p["title"]
                
                # Format mandate logic for display in UI (English only)
                logic = p.get("decision_logic", {})
                mandate_display = "\n\n## Mandate Dimensions\n"
                mandate_fields = [
                    ("check_size", "Check Size"),
                    ("return_threshold", "Return Threshold (IRR/MoC)"),
                    ("stage_preference", "Stage Preference"),
                    ("loss_aversion_profile", "Loss Aversion"),
                    ("sector_bias", "Sector Bias"),
                    ("time_horizon", "Time Horizon"),
                    ("portfolio_logic", "Portfolio Construction"),
                    ("governance_sensitivity", "Governance Sensitivity"),
                    ("exit_expectations", "Exit Expectations")
                ]
                
                for key, label in mandate_fields:
                    val = logic.get(key, "N/A")
                    mandate_display += f"- **{label}**: {val}\n"
                
                # Inject into persona and bio so it shows up in UI
                if "persona" in p:
                    p["persona"] = p["persona"] + mandate_display
                else:
                    p["persona"] = p.get("mandate_description", "") + mandate_display
                
                # Structured data for frontend grid
                p["mandate_logic"] = {label: logic.get(key, "N/A") for key, label in mandate_fields}
                
                if "bio" in p:
                    p["bio"] = p["bio"] + f" | {p.get('title', '')}"
                
            return profiles
        except Exception as e:
            logger.error(f"Failed to generate instances for {arch['name']}: {e}")
            return []


    def _get_fallback_profiles(self, count: int) -> List[Dict[str, Any]]:
        """Fallback logic: Generate based on predefined Archetypes"""
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
