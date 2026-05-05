"""
DealSim IC Room Simulation Engine
A structured 5-stage adversarial interrogation of investment claims.
Built on top of the CAMEL-OASIS architecture.
"""

import sys
import os
import json
import asyncio
import logging
import argparse
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

# Constants for Stages
STAGES = [
    "First Look (Quick Sanity Check)",
    "Full Pack Review (Detailed Examination)",
    "Cross-Examination (Adversarial Interrogation)",
    "Diligence Surfacing (Identifying Information Gaps)",
    "Final Verdict (Investment Decision)"
]

# Add backend directory to path
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
sys.path.insert(0, _backend_dir)

from app.config import Config
from app.utils.llm_client import LLMClient

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dealsim.ic_room')

class ICRoomSimulation:
    def __init__(self, simulation_dir: str):
        self.simulation_dir = simulation_dir
        self.config_path = os.path.join(simulation_dir, "simulation_config.json")
        self.profiles_path = os.path.join(simulation_dir, "ic_profiles.json")
        self.actions_log_path = os.path.join(simulation_dir, "ic_actions.jsonl")
        
        self.config = {}
        self.profiles = []
        self.claims = []
        self.current_stage_idx = 0
        
        self.llm_client = LLMClient()

    async def initialize(self):
        """加载配置和人设"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        if os.path.exists(self.profiles_path):
            with open(self.profiles_path, 'r', encoding='utf-8') as f:
                self.profiles = json.load(f)
        
        self.claims = []
        
        # 从 Zep 图谱或 state.json 加载 Claims
        state_path = os.path.join(self.simulation_dir, "state.json")
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
            
            # Fetch nodes from Zep
            graph_id = self.state.get("graph_id")
            if graph_id:
                try:
                    from app.services.zep_entity_reader import ZepEntityReader
                    reader = ZepEntityReader()
                    filtered = reader.filter_defined_entities(graph_id=graph_id)
                    self.claims = filtered.entities
                    logger.info(f"Fetched {len(self.claims)} company nodes from graph {graph_id}")
                except Exception as e:
                    logger.error(f"Failed to fetch nodes from Zep: {e}")
        
        logger.info(f"Initialized IC Room with {len(self.profiles)} members.")

    def log_action(self, agent_id: int, agent_name: str, stage: str, action_type: str, claim_id: str, content: str):
        """记录动作日志"""
        log_entry = {
            "round": self.current_stage_idx + 1,
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "action_args": {
                "stage": stage,
                "claim_id": claim_id
            },
            "result": content,
            "success": True
        }
        with open(self.actions_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    async def run_stage(self, stage_idx: int):
        """运行单个阶段的模拟"""
        stage_name = STAGES[stage_idx]
        logger.info(f"Starting Stage {stage_idx + 1}: {stage_name}")
        
        # 挑选活跃的IC成员参与本轮
        active_members = random.sample(self.profiles, k=min(len(self.profiles), 8))
        
        # 注入市场情绪（如果有的话）
        market_context = getattr(self, 'market_sentiment', "No public market sentiment data available.")
        
        # 准备 Claims 文本
        claims_text = "\n".join([f"- {c.name}: {c.summary}" for c in self.claims[:12]])
        if not claims_text:
            claims_text = "No specific internal logic node data available."

        async def process_member(member):
            # LLM 决定该成员本轮针对哪个 Claim 发言
            # 构建 Prompt
            prompt = f"""You are participating in an Investment Committee (IC Room) discussion.
Current Stage: {stage_name}

[Interrogation Basis: Dual-Dimension Intelligence]
1. Internal Logic Nodes: Contains the core investment claims and factual nodes from the project proposal:
{claims_text}

2. Expert Thought Nodes: Below are the core skepticisms and feedback from the public market (Twitter/Reddit). Please heavily incorporate these into your interrogation:
{market_context}

Your Mandate: {member.get('mandate_description')}
Your Decision Logic: {json.dumps(member.get('decision_logic'))}

Based on your mandate and the market feedback above, please interrogate or comment on the core logic of this transaction.
You must exhibit a professional, highly critical, and insightful style.

Output Requirements:
1. Select a primary focus area.
2. Ask a sharp, pointed question or provide an independent insight.
3. Provide your interrogation text (within 150 words).
Please respond entirely in English.
"""
            
            try:
                # 异步发送请求
                response = await self.llm_client.chat_async([
                    {"role": "system", "content": member.get('persona', "You are an IC member.")},
                    {"role": "user", "content": prompt}
                ])
                
                # 记录日志
                self.log_action(
                    agent_id=member.get('user_id'),
                    agent_name=member.get('name'),
                    stage=stage_name,
                    action_type="INTERROGATION",
                    claim_id="general", # 待后续精细化
                    content=response
                )
                logger.info(f"[{member.get('name')}] added to discussion in {stage_name}")
            except Exception as e:
                logger.error(f"Agent {member.get('name')} interaction failed: {e}")

        # 使用 asyncio.gather 并行处理所有成员
        await asyncio.gather(*(process_member(m) for m in active_members))

    async def run(self):
        """运行完整 5 阶段循环"""
        logger.info("Starting IC Room Simulation Loop...")
        for i in range(len(STAGES)):
            await self.run_stage(i)
            # 阶段间停顿
            await asyncio.sleep(2)
        
        logger.info("Simulation Completed. IC Prep report is ready to be generated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DealSim IC Room Simulator")
    parser.add_argument("--config", type=str, required=True, help="Path to simulation config")
    parser.add_argument("--market-sentiment", type=str, default="", help="Summarized market sentiment context")
    parser.add_argument("--max-rounds", type=int, default=5, help="Maximum number of rounds to simulate")
    args = parser.parse_args()
    
    # 提取目录
    sim_dir = os.path.dirname(args.config)
    
    sim = ICRoomSimulation(sim_dir)
    sim.market_sentiment = args.market_sentiment
    
    async def main():
        await sim.initialize()
        await sim.run()
        
    asyncio.run(main())
