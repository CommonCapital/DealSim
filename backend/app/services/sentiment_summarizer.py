import os
import json
import logging
from typing import List, Dict, Any
from app.utils.llm_client import LLMClient

logger = logging.getLogger('dealsim.sentiment_summarizer')

class SentimentSummarizer:
    def __init__(self):
        self.llm_client = LLMClient()

    def summarize_parallel_actions(self, sim_dir: str) -> str:
        """从 Twitter 和 Reddit 日志中总结市场情绪"""
        twitter_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        actions = []
        
        # 加载最近的 50 条 Twitter 动作
        if os.path.exists(twitter_log):
            with open(twitter_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    try:
                        actions.append(json.loads(line))
                    except:
                        continue
                        
        # 加载最近的 50 条 Reddit 动作
        if os.path.exists(reddit_log):
            with open(reddit_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    try:
                        actions.append(json.loads(line))
                    except:
                        continue
        
        if not actions:
            return "No significant market discourse recorded yet."
            
        # 提取关键对话片段
        discourse = []
        for a in actions:
            if a.get('action_type') == 'CREATE_POST':
                discourse.append(f"[{a['platform']}] {a['agent_name']}: {a['action_args'].get('content')}")
            elif a.get('action_type') == 'CREATE_COMMENT':
                discourse.append(f"[{a['platform']}] {a['agent_name']} commented: {a['action_args'].get('content')}")
            elif a.get('action_type') == 'QUOTE_POST':
                discourse.append(f"[{a['platform']}] {a['agent_name']} quoted: {a['action_args'].get('quote_content')}")

        discourse_text = "\n".join(discourse[:40])
        
        prompt = f"""以下是针对该投资项目的公开市场（Twitter/Reddit）讨论记录。
请总结出 3-5 个核心的“市场焦虑点”或“公众质疑点”，供投审会（IC Room）内部辩论使用。
输出要求：精炼、客观、直接。

讨论记录：
{discourse_text}
"""
        
        try:
            summary = self.llm_client.chat([
                {"role": "system", "content": "You are a Market Intelligence Analyst for an Investment Committee."},
                {"role": "user", "content": prompt}
            ])
            return summary
        except Exception as e:
            logger.error(f"Sentiment summarization failed: {e}")
            return "Market sentiment analysis currently unavailable."

# Singleton instance
summarizer = SentimentSummarizer()
