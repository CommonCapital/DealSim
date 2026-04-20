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
        
        # 从 Zep 图谱或 state.json 加载 Claims
        state_path = os.path.join(self.simulation_dir, "state.json")
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
        
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
        market_context = getattr(self, 'market_sentiment', "暂无公开市场情绪数据。")
        
        for member in active_members:
            # LLM 决定该成员本轮针对哪个 Claim 发言
            # 构建 Prompt
            prompt = f"""你正在参与投审会（IC Room）的讨论。
当前阶段: {stage_name}

【质询依据：双维度情报】
1. 内部逻辑节点 (Internal Logic Nodes): 包含项目 PPT 提案及财务模型中的多项投资声明。
2. 专家思维节点 (Expert Thought Nodes): 以下是先前阶段行业专家及公开市场讨论中反馈出的核心“思维节点”，请你在质询时重点结合这些反馈：
{market_context}

你的授权（Mandate）: {member.get('mandate_description')}
你的决策逻辑: {json.dumps(member.get('decision_logic'))}

请根据你的授权和上述市场反馈，针对本次交易的核心逻辑进行质询或评论。
你需要表现出专业、挑剔且具有洞察力的风格。

输出要求：
1. 选择一个主要关注点
2. 提出一个尖锐的问题或发表独立见解
3. 给出你的质询文本（150字以内）
"""
            
            try:
                # 简单模拟，实际应用中应更复杂地绑定 Claim
                response = self.llm_client.chat([
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
                
                # 模拟思考延迟
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Agent {member.get('name')} interaction failed: {e}")

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
    args = parser.parse_args()
    
    # 提取目录
    sim_dir = os.path.dirname(args.config)
    
    sim = ICRoomSimulation(sim_dir)
    sim.market_sentiment = args.market_sentiment
    
    async def main():
        await sim.initialize()
        await sim.run()
        
    asyncio.run(main())
