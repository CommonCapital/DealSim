"""
Report Agent服务
使用LangChain + Zep实现ReACT模式的模拟报告生成

功能：
1. 根据模拟需求和Zep图谱信息生成报告
2. 先规划目录结构，然后分段生成
3. 每段采用ReACT多轮思考与反思模式
4. 支持与用户对话，在对话中自主调用检索工具
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..utils.locale import get_language_instruction, t
from .zep_tools import (
    ZepToolsService, 
    SearchResult, 
    InsightForgeResult, 
    PanoramaResult,
    InterviewResult
)

logger = get_logger('dealsim.report_agent')


class ReportLogger:
    """
    Report Agent 详细日志记录器
    
    在报告文件夹中生成 agent_log.jsonl 文件，记录每一步详细动作。
    每行是一个完整的 JSON 对象，包含时间戳、动作类型、详细内容等。
    """
    
    def __init__(self, report_id: str):
        """
        初始化日志记录器
        
        Args:
            report_id: 报告ID，用于确定日志文件路径
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'agent_log.jsonl'
        )
        self.start_time = datetime.now()
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """确保日志文件所在目录存在"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _get_elapsed_time(self) -> float:
        """获取从开始到现在的耗时（秒）"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def log(
        self, 
        action: str, 
        stage: str,
        details: Dict[str, Any],
        section_title: str = None,
        section_index: int = None
    ):
        """
        记录一条日志
        
        Args:
            action: 动作类型，如 'start', 'tool_call', 'llm_response', 'section_complete' 等
            stage: 当前阶段，如 'planning', 'generating', 'completed'
            details: 详细内容字典，不截断
            section_title: 当前章节标题（可选）
            section_index: 当前章节索引（可选）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(self._get_elapsed_time(), 2),
            "report_id": self.report_id,
            "action": action,
            "stage": stage,
            "section_title": section_title,
            "section_index": section_index,
            "details": details
        }
        
        # 追加写入 JSONL 文件
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def log_start(self, simulation_id: str, graph_id: str, simulation_requirement: str):
        """记录报告生成开始"""
        self.log(
            action="report_start",
            stage="pending",
            details={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "simulation_requirement": simulation_requirement,
                "message": t('report.taskStarted')
            }
        )
    
    def log_planning_start(self):
        """记录大纲规划开始"""
        self.log(
            action="planning_start",
            stage="planning",
            details={"message": t('report.planningStart')}
        )
    
    def log_planning_context(self, context: Dict[str, Any]):
        """记录规划时获取的上下文信息"""
        self.log(
            action="planning_context",
            stage="planning",
            details={
                "message": t('report.fetchSimContext'),
                "context": context
            }
        )
    
    def log_planning_complete(self, outline_dict: Dict[str, Any]):
        """记录大纲规划完成"""
        self.log(
            action="planning_complete",
            stage="planning",
            details={
                "message": t('report.planningComplete'),
                "outline": outline_dict
            }
        )
    
    def log_section_start(self, section_title: str, section_index: int):
        """记录章节生成开始"""
        self.log(
            action="section_start",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={"message": t('report.sectionStart', title=section_title)}
        )
    
    def log_react_thought(self, section_title: str, section_index: int, iteration: int, thought: str):
        """记录 ReACT 思考过程"""
        self.log(
            action="react_thought",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "thought": thought,
                "message": t('report.reactThought', iteration=iteration)
            }
        )
    
    def log_tool_call(
        self, 
        section_title: str, 
        section_index: int,
        tool_name: str, 
        parameters: Dict[str, Any],
        iteration: int
    ):
        """记录工具调用"""
        self.log(
            action="tool_call",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "parameters": parameters,
                "message": t('report.toolCall', toolName=tool_name)
            }
        )
    
    def log_tool_result(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        result: str,
        iteration: int
    ):
        """记录工具调用结果（完整内容，不截断）"""
        self.log(
            action="tool_result",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "result": result,  # 完整结果，不截断
                "result_length": len(result),
                "message": t('report.toolResult', toolName=tool_name)
            }
        )
    
    def log_llm_response(
        self,
        section_title: str,
        section_index: int,
        response: str,
        iteration: int,
        has_tool_calls: bool,
        has_final_answer: bool
    ):
        """记录 LLM 响应（完整内容，不截断）"""
        self.log(
            action="llm_response",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "response": response,  # 完整响应，不截断
                "response_length": len(response),
                "has_tool_calls": has_tool_calls,
                "has_final_answer": has_final_answer,
                "message": t('report.llmResponse', hasToolCalls=has_tool_calls, hasFinalAnswer=has_final_answer)
            }
        )
    
    def log_section_content(
        self,
        section_title: str,
        section_index: int,
        content: str,
        tool_calls_count: int
    ):
        """记录章节内容生成完成（仅记录内容，不代表整个章节完成）"""
        self.log(
            action="section_content",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": content,  # 完整内容，不截断
                "content_length": len(content),
                "tool_calls_count": tool_calls_count,
                "message": t('report.sectionContentDone', title=section_title)
            }
        )
    
    def log_section_full_complete(
        self,
        section_title: str,
        section_index: int,
        full_content: str
    ):
        """
        记录章节生成完成

        前端应监听此日志来判断一个章节是否真正完成，并获取完整内容
        """
        self.log(
            action="section_complete",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": full_content,
                "content_length": len(full_content),
                "message": t('report.sectionComplete', title=section_title)
            }
        )
    
    def log_report_complete(self, total_sections: int, total_time_seconds: float):
        """记录报告生成完成"""
        self.log(
            action="report_complete",
            stage="completed",
            details={
                "total_sections": total_sections,
                "total_time_seconds": round(total_time_seconds, 2),
                "message": t('report.reportComplete')
            }
        )
    
    def log_error(self, error_message: str, stage: str, section_title: str = None):
        """记录错误"""
        self.log(
            action="error",
            stage=stage,
            section_title=section_title,
            section_index=None,
            details={
                "error": error_message,
                "message": t('report.errorOccurred', error=error_message)
            }
        )


class ReportConsoleLogger:
    """
    Report Agent 控制台日志记录器
    
    将控制台风格的日志（INFO、WARNING等）写入报告文件夹中的 console_log.txt 文件。
    这些日志与 agent_log.jsonl 不同，是纯文本格式的控制台输出。
    """
    
    def __init__(self, report_id: str):
        """
        初始化控制台日志记录器
        
        Args:
            report_id: 报告ID，用于确定日志文件路径
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'console_log.txt'
        )
        self._ensure_log_file()
        self._file_handler = None
        self._setup_file_handler()
    
    def _ensure_log_file(self):
        """确保日志文件所在目录存在"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
    
    def _setup_file_handler(self):
        """设置文件处理器，将日志同时写入文件"""
        import logging
        
        # 创建文件处理器
        self._file_handler = logging.FileHandler(
            self.log_file_path,
            mode='a',
            encoding='utf-8'
        )
        self._file_handler.setLevel(logging.INFO)
        
        # 使用与控制台相同的简洁格式
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self._file_handler.setFormatter(formatter)
        
        # 添加到 report_agent 相关的 logger
        loggers_to_attach = [
            'dealsim.report_agent',
            'dealsim.zep_tools',
        ]
        
        for logger_name in loggers_to_attach:
            target_logger = logging.getLogger(logger_name)
            # 避免重复添加
            if self._file_handler not in target_logger.handlers:
                target_logger.addHandler(self._file_handler)
    
    def close(self):
        """关闭文件处理器并从 logger 中移除"""
        import logging
        
        if self._file_handler:
            loggers_to_detach = [
                'mirofish.report_agent',
                'mirofish.zep_tools',
            ]
            
            for logger_name in loggers_to_detach:
                target_logger = logging.getLogger(logger_name)
                if self._file_handler in target_logger.handlers:
                    target_logger.removeHandler(self._file_handler)
            
            self._file_handler.close()
            self._file_handler = None
    
    def __del__(self):
        """析构时确保关闭文件处理器"""
        self.close()


class ReportStatus(str, Enum):
    """报告状态"""
    PENDING = "pending"
    PLANNING = "planning"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content
        }

    def to_markdown(self, level: int = 2) -> str:
        """转换为Markdown格式"""
        md = f"{'#' * level} {self.title}\n\n"
        if self.content:
            md += f"{self.content}\n\n"
        return md


@dataclass
class ReportOutline:
    """报告大纲"""
    title: str
    summary: str
    sections: List[ReportSection]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections]
        }
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = f"# {self.title}\n\n"
        md += f"> {self.summary}\n\n"
        for section in self.sections:
            md += section.to_markdown()
        return md


@dataclass
class Report:
    """完整报告"""
    report_id: str
    simulation_id: str
    graph_id: str
    simulation_requirement: str
    status: ReportStatus
    outline: Optional[ReportOutline] = None
    markdown_content: str = ""
    created_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "simulation_id": self.simulation_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "status": self.status.value,
            "outline": self.outline.to_dict() if self.outline else None,
            "markdown_content": self.markdown_content,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error
        }

TOOL_DESC_INSIGHT_FORGE = """\
【深度漏洞检索 - 强大的审计工具】
这是专门为 DealSim 设计的检索函数，用于挖掘 deal 中的潜在裂缝。它会：
1. 自动将你的审计问题分解为多个子问题
2. 从多个维度检索 IC Room 模拟日志中的信息
3. 追踪 Claim（主张）与其对应的 Evidence/Risk/Assumption 的逻辑链
4. 返回最全面、最深度的审计内容

【使用场景】
- 需要分析某个特定主张（Claim）的脆弱性
- 需要寻找不同投资人之间的意见分歧点
- 需要获取支撑报告章节的客观审计素材

【返回内容】
- 原始对话记录（直接证据）
- 脆弱性评分与逻辑漏洞
- 风险传导链条分析"""

TOOL_DESC_PANORAMA_SEARCH = """\
【广度审计 - 获取全貌视图】
用于获取整个 IC Room Interrogation 的全貌，特别适合了解审计过程。它会：
1. 获取所有五个阶段（Introduction to Summary）的完整逻辑流
2. 追踪每个 Claim 在不同阶段受到的压力变化
3. 帮助你了解 "脆弱性" 是如何从细枝末节汇聚成致命伤的

【使用场景】
- 需要了解五个审计阶段的完整逻辑发展
- 需要对比不同时间点（阶段）的共识平衡
- 需要获取所有相关的 Claim 和证据映射

【返回内容】
- 当前审计共识
- 阶段性压力测试记录
- 所有涉及的主张与风险点"""

TOOL_DESC_QUICK_SEARCH = """\
【简单检索 - 快速核实】
轻量级的快速检索工具，适合简单的、直接的事实核实。

【使用场景】
- 核实某个具体的财务数据是否被挑战
- 查找特定的风险点是否在模拟中出现
- 简单的信息检索

【返回内容】
- 与查询最相关的日志条目"""

TOOL_DESC_INTERVIEW_AGENTS = """\
【定向回访 - 与投资 Archetype 深入核实】
调用 DealSim 的采访 API，对刚才参与 IC 审查的投资人（Archetypes）进行定向回访！
这允许你追问那些在 Interrogation 阶段未能完全展开的细节。

【使用场景】
- 需要从特定投资人视角了解决策逻辑（为什么 skepticalist 会投反对票？）
- 需要深挖某个特定的风险点在特定投资框架下的分量
- 补充报告中的 "Archetype Perspectives" 章节

【返回内容】
- 指定投资人的决策逻辑深度阐述
- 第一人称的风险定性"""

# ── 大纲规划 prompt ──

# ── 大纲规划 prompt ──

PLAN_SYSTEM_PROMPT = """你是一个「DealSim IC 审查报告」专家，负责将投审会（IC Room）的对抗性模拟结果转化为一份正式的投资审计报告。

## 审计目标
你的核心任务是回答："给定这个 Deal，什么会首先崩溃？"。你正在观察的是一群具有极高专业度和特定投资授权（Mandates）的 Archetypes 对该交易进行的压力测试。

## 报告结构要求 (必须包含且仅包含以下 6 个章节)
1. **什么会首先崩溃 (What breaks first)**: 识别最致命的单一风险点或逻辑断层。这是对交易脆弱性的直击。
2. **核心反对意见 (Top objections)**: 总结 IC 成员最集中的攻击点。必须以「反对意见表」的形式呈现，包含：反对者身份、核心论点、严重程度（Critical/Major/Minor）。
3. **缺失的尽调信息 (Missing diligence)**: 列出模拟过程中发现的、现有文档未覆盖的关键信息缺口。
4. **决策画像透视 (Split by persona type)**: 按照不同的投资授权（如：Conservative PE vs Growth Equity）拆解他们的分歧。体现不同利益方的对立。
5. **改变局面的证据 (What evidence would change minds)**: 识别出哪些具体的数据或证明材料能有效抵消上述反对意见。
6. **投委会最终建议 (Investment Committee Recommendation)**: 一个明确的 GO/NO-GO 结论，包含 0-100 的信心得分（Confidence Score），以及最终的风险提示。

## 任务要求
请输出 JSON 格式的报告大纲。确保标题专业且符合 V1 规范。

```json
{
    "title": "DealSim Diagnostic Audit: [Deal Name]",
    "summary": "针对该交易的 5 阶段对抗性审计总结",
    "sections": [
        {
            "title": "章节标题",
            "description": "章节分析重点"
        }
    ]
}
```
"""

PLAN_USER_PROMPT_TEMPLATE = """【审议项目背景】
项目/主张描述：{simulation_requirement}

【审计规模】
- 参与审计的投资人总数: {profiles_count}
- 审计产生的交互记录: {total_edges}
- 识别出的关键主张 (Claims): {total_nodes}

【审计发现摘要】
{related_facts_json}

请基于以上 IC Room 的模拟结果，规划一份专业的「DealSim Diagnostic Audit」。
确保章节完全符合 6 章节标准，逻辑链严密。"""

# ── 章节生成 prompt ──

SECTION_SYSTEM_PROMPT_TEMPLATE = """你是一个「DealSim IC 审查报告」专家，正在撰写一份正式投资审计报告中的特定章节。

报告标题: {report_title}
核心摘要: {report_summary}
项目/主张描述: {simulation_requirement}

当前要撰写的章节: {section_title}

## 核心理念
这份报告不是总结，而是「审计」。你必须识别出最显著的问题、最大的逻辑断层和最不可信的数据。
你正在分析的是具有 Check size, Return threshold, Stage preference, Loss aversion, Sector bias, Time horizon 等 9 个维度的专业投资人的对抗性反馈。

## 撰写准则
1. **基于审计日志**: 所有结论必须来自 IC Room 的真实交互日志。禁止编造。
2. **利益相关方对比**: 展示 Conservative PE 为何在杠杆率上纠结，而 Growth Equity 为何在 CAC/LTV 上防御。
3. **结构化输出**: 
   - 如果是「Top objections」，必须使用 Markdown 表格。
   - 如果是「Missing diligence」，必须使用分项列表。
4. **专业语气**: 使用金融术语（MoM, IRR, Exit Multiple, Burn Rate, TAM, GTM, etc.）。
5. **格式规范**: ❌ 禁止使用 # 或 ## 等 Markdown 标题。✅ 使用 **粗体** 代替。

## 可用工具
{tools_description}

## 工作流
你必须通过多轮 Thought -> Tool Call -> Result 的 ReACT 模式来确证你的结论，最后输出 "Final Answer:"。

现在开始分析。"""

SECTION_USER_PROMPT_TEMPLATE = """\
已完成的章节内容（请仔细阅读，避免重复）：
{previous_content}

═══════════════════════════════════════════════════════════════
【当前任务】撰写章节: {section_title}
═══════════════════════════════════════════════════════════════

【重要提醒】
1. 仔细阅读上方已完成的章节，避免重复相同的内容！
2. 开始前必须先调用工具获取模拟数据
3. 请混合使用不同工具，不要只用一种
4. 报告内容必须来自检索结果，不要使用自己的知识

【⚠️ 格式警告 - 必须遵守】
- ❌ 不要写任何标题（#、##、###、####都不行）
- ❌ 不要写"{section_title}"作为开头
- ✅ 章节标题由系统自动添加
- ✅ 直接写正文，用**粗体**代替小节标题

请开始：
1. 首先思考（Thought）这个章节需要什么信息
2. 然后调用工具（Action）获取模拟数据
3. 收集足够信息后输出 Final Answer（纯正文，无任何标题）"""

# ── ReACT 循环内消息模板 ──

REACT_OBSERVATION_TEMPLATE = """\
Observation（审计发现）:

═══ 工具 {tool_name} 返回 ═══
{result}

═══════════════════════════════════════════════════════════════
已调用工具 {tool_calls_count}/{max_tool_calls} 次（已用: {used_tools_str}）{unused_hint}
- 如果证据充分：以 "Final Answer:" 开头输出审计结论（必须引用上述日志原文）
- 如果需要更多细节：调用一个工具继续检索
═══════════════════════════════════════════════════════════════"""

REACT_INSUFFICIENT_TOOLS_MSG = (
    "【注意】你只调用了{tool_calls_count}次工具，至少需要{min_tool_calls}次。"
    "请再调用审计工具获取更多证据，然后再输出 Final Answer。{unused_hint}"
)

REACT_INSUFFICIENT_TOOLS_MSG_ALT = (
    "当前只调用了 {tool_calls_count} 次工具，至少需要 {min_tool_calls} 次。"
    "请调用审计工具获取更多证据。{unused_hint}"
)

REACT_TOOL_LIMIT_MSG = (
    "审计工具调用次数已达上限（{tool_calls_count}/{max_tool_calls}），不能再调用工具。"
    '请立即基于已获取的证据，以 "Final Answer:" 开头输出章节内容。'
)

REACT_UNUSED_TOOLS_HINT = "\n💡 你还没有使用过: {unused_list}，建议尝试不同工具获取多角度信息"

REACT_FORCE_FINAL_MSG = "已达到审计工具调用限制，请直接输出 Final Answer: 并生成章节内容。"

# ── Chat/QA prompt ──

CHAT_SYSTEM_PROMPT_TEMPLATE = """\
你是一个 DealSim 投资决策助手。

【背景】
正在审议的项目: {simulation_requirement}

【已生成的 IC Prep Report】
{report_content}

【规则】
1. 优先基于报告内容回答关于 deal 脆弱性的问题
2. 保持专业、审慎的投资审计语气
3. 仅在需要深挖报告未提及的细节时，才调用审计工具
4. 回答要直接，聚焦于风险与决策建议

【可用工具】
{tools_description}

【回答风格】
- 使用专业投资术语
- 优先给出定性或定量结论
- 使用 > 引用原始对话日志作为佐证"""

CHAT_OBSERVATION_SUFFIX = "\n\n请简洁回答审计问题。"


# ═══════════════════════════════════════════════════════════════
# ReportAgent 主类
# ═══════════════════════════════════════════════════════════════


class ReportAgent:
    """
    Report Agent - 模拟报告生成Agent

    采用ReACT（Reasoning + Acting）模式：
    1. 规划阶段：分析模拟需求，规划报告目录结构
    2. 生成阶段：逐章节生成内容，每章节可多次调用工具获取信息
    3. 反思阶段：检查内容完整性和准确性
    """
    
    # 最大工具调用次数（每个章节）
    MAX_TOOL_CALLS_PER_SECTION = 5
    
    # 最大反思轮数
    MAX_REFLECTION_ROUNDS = 3
    
    # 对话中的最大工具调用次数
    MAX_TOOL_CALLS_PER_CHAT = 2
    
    def __init__(
        self, 
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None
    ):
        """
        初始化Report Agent
        
        Args:
            graph_id: 图谱ID
            simulation_id: 模拟ID
            simulation_requirement: 模拟需求描述
            llm_client: LLM客户端（可选）
            zep_tools: Zep工具服务（可选）
        """
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.simulation_requirement = simulation_requirement
        
        self.llm = llm_client or LLMClient()
        self.zep_tools = zep_tools or ZepToolsService()
        
        # 工具定义
        self.tools = self._define_tools()
        
        # 日志记录器（在 generate_report 中初始化）
        self.report_logger: Optional[ReportLogger] = None
        # 控制台日志记录器（在 generate_report 中初始化）
        self.console_logger: Optional[ReportConsoleLogger] = None
        
        logger.info(t('report.agentInitDone', graphId=graph_id, simulationId=simulation_id))
    
    def _define_tools(self) -> Dict[str, Dict[str, Any]]:
        """定义可用工具"""
        return {
            "insight_forge": {
                "name": "insight_forge",
                "description": TOOL_DESC_INSIGHT_FORGE,
                "parameters": {
                    "query": "你想深入分析的问题或话题",
                    "report_context": "当前报告章节的上下文（可选，有助于生成更精准的子问题）"
                }
            },
            "panorama_search": {
                "name": "panorama_search",
                "description": TOOL_DESC_PANORAMA_SEARCH,
                "parameters": {
                    "query": "搜索查询，用于相关性排序",
                    "include_expired": "是否包含过期/历史内容（默认True）"
                }
            },
            "quick_search": {
                "name": "quick_search",
                "description": TOOL_DESC_QUICK_SEARCH,
                "parameters": {
                    "query": "搜索查询字符串",
                    "limit": "返回结果数量（可选，默认10）"
                }
            },
            "interview_agents": {
                "name": "interview_agents",
                "description": TOOL_DESC_INTERVIEW_AGENTS,
                "parameters": {
                    "interview_topic": "采访主题或需求描述",
                    "max_agents": "最多采访的Agent数量（可选，默认5，最大10）"
                }
            }
        }
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], report_context: str = "") -> str:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            report_context: 报告上下文（用于InsightForge）
            
        Returns:
            工具执行结果（文本格式）
        """
        logger.info(t('report.executingTool', toolName=tool_name, params=parameters))
        
        try:
            if tool_name == "insight_forge":
                query = parameters.get("query", "")
                ctx = parameters.get("report_context", "") or report_context
                result = self.zep_tools.insight_forge(
                    graph_id=self.graph_id,
                    query=query,
                    simulation_requirement=self.simulation_requirement,
                    report_context=ctx
                )
                return result.to_text()
            
            elif tool_name == "panorama_search":
                # 广度搜索 - 获取全貌
                query = parameters.get("query", "")
                include_expired = parameters.get("include_expired", True)
                if isinstance(include_expired, str):
                    include_expired = include_expired.lower() in ['true', '1', 'yes']
                result = self.zep_tools.panorama_search(
                    graph_id=self.graph_id,
                    query=query,
                    include_expired=include_expired
                )
                return result.to_text()
            
            elif tool_name == "quick_search":
                # 简单搜索 - 快速检索
                query = parameters.get("query", "")
                limit = parameters.get("limit", 10)
                if isinstance(limit, str):
                    limit = int(limit)
                result = self.zep_tools.quick_search(
                    graph_id=self.graph_id,
                    query=query,
                    limit=limit
                )
                return result.to_text()
            
            elif tool_name == "interview_agents":
                # 深度采访
                interview_topic = parameters.get("interview_topic", parameters.get("query", ""))
                max_agents = parameters.get("max_agents", 5)
                if isinstance(max_agents, str):
                    max_agents = int(max_agents)
                max_agents = min(max_agents, 10)
                result = self.zep_tools.interview_agents(
                    simulation_id=self.simulation_id,
                    interview_requirement=interview_topic,
                    simulation_requirement=self.simulation_requirement,
                    max_agents=max_agents
                )
                return result.to_text()
            
            # ========== 向后兼容的旧工具 ==========
            
            elif tool_name == "search_graph":
                # 重定向到 quick_search
                logger.info(t('report.redirectToQuickSearch'))
                return self._execute_tool("quick_search", parameters, report_context)
            
            elif tool_name == "get_graph_statistics":
                result = self.zep_tools.get_graph_statistics(self.graph_id)
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_entity_summary":
                entity_name = parameters.get("entity_name", "")
                result = self.zep_tools.get_entity_summary(
                    graph_id=self.graph_id,
                    entity_name=entity_name
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_simulation_context":
                # 重定向到 insight_forge，因为它更强大
                logger.info(t('report.redirectToInsightForge'))
                query = parameters.get("query", self.simulation_requirement)
                return self._execute_tool("insight_forge", {"query": query}, report_context)
            
            elif tool_name == "get_entities_by_type":
                entity_type = parameters.get("entity_type", "")
                nodes = self.zep_tools.get_entities_by_type(
                    graph_id=self.graph_id,
                    entity_type=entity_type
                )
                result = [n.to_dict() for n in nodes]
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            else:
                return f"未知工具: {tool_name}。请使用以下工具之一: insight_forge, panorama_search, quick_search"
                
        except Exception as e:
            logger.error(t('report.toolExecFailed', toolName=tool_name, error=str(e)))
            return f"工具执行失败: {str(e)}"
    
    # 合法的工具名称集合，用于裸 JSON 兜底解析时校验
    VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        从LLM响应中解析工具调用
        """
        tool_calls = []

        # 格式1: XML风格（标准格式）
        xml_pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        for match in re.finditer(xml_pattern, response, re.DOTALL):
            try:
                call_data = json.loads(match.group(1))
                tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        if tool_calls:
            return tool_calls

        # 格式2: 兜底 - LLM 直接输出裸 JSON
        stripped = response.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                call_data = json.loads(stripped)
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
                    return tool_calls
            except json.JSONDecodeError:
                pass

        json_pattern = r'(\{"(?:name|tool)"\s*:.*?\})\s*$'
        match = re.search(json_pattern, stripped, re.DOTALL)
        if match:
            try:
                call_data = json.loads(match.group(1))
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        return tool_calls

    def _is_valid_tool_call(self, data: dict) -> bool:
        """校验解析出的 JSON 是否是合法的工具调用"""
        tool_name = data.get("name") or data.get("tool")
        if tool_name and tool_name in self.VALID_TOOL_NAMES:
            if "tool" in data:
                data["name"] = data.pop("tool")
            if "params" in data and "parameters" not in data:
                data["parameters"] = data.pop("params")
            return True
        return False
    
    def _get_tools_description(self) -> str:
        """生成工具描述文本"""
        desc_parts = ["可用工具："]
        for name, tool in self.tools.items():
            params_desc = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
            desc_parts.append(f"- {name}: {tool['description']}")
            if params_desc:
                desc_parts.append(f"  参数: {params_desc}")
        return "\n".join(desc_parts)
    
    def plan_outline(
        self, 
        progress_callback: Optional[Callable] = None
    ) -> ReportOutline:
        """
        规划报告大纲
        """
        logger.info(t('report.startPlanningOutline'))
        
        if progress_callback:
            progress_callback("planning", 0, t('progress.analyzingRequirements'))
        
        context = self.zep_tools.get_simulation_context(
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement
        )
        
        if progress_callback:
            progress_callback("planning", 30, t('progress.generatingOutline'))
        
        system_prompt = f"{PLAN_SYSTEM_PROMPT}\n\n{get_language_instruction()}"
        user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            total_nodes=context.get('graph_statistics', {}).get('total_nodes', 0),
            total_edges=context.get('graph_statistics', {}).get('total_edges', 0),
            entity_types=list(context.get('graph_statistics', {}).get('entity_types', {}).keys()),
            profiles_count=context.get('total_entities', 0),
            related_facts_json=json.dumps(context.get('related_facts', [])[:10], ensure_ascii=False, indent=2),
        )

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            if progress_callback:
                progress_callback("planning", 80, t('progress.parsingOutline'))
            
            sections = []
            for section_data in response.get("sections", []):
                sections.append(ReportSection(
                    title=section_data.get("title", ""),
                    content=""
                ))
            
            outline = ReportOutline(
                title=response.get("title", "IC Prep Report"),
                summary=response.get("summary", ""),
                sections=sections
            )
            
            if progress_callback:
                progress_callback("planning", 100, t('progress.outlinePlanComplete'))
            
            logger.info(t('report.outlinePlanDone', count=len(sections)))
            return outline
            
        except Exception as e:
            logger.error(t('report.outlinePlanFailed', error=str(e)))
            return ReportOutline(
                title="DealSim Diagnostic Audit",
                summary="针对该交易的 5 阶段对抗性审计总结",
                sections=[
                    ReportSection(title="什么会首先崩溃 (What breaks first)"),
                    ReportSection(title="核心反对意见 (Top objections)"),
                    ReportSection(title="缺失的尽调信息 (Missing diligence)"),
                    ReportSection(title="决策画像透视 (Split by persona type)"),
                    ReportSection(title="改变局面的证据 (What evidence would change minds)"),
                    ReportSection(title="投委会最终建议 (Investment Committee Recommendation)")
                ]
            )
    
    def _generate_section_react(
        self, 
        section: ReportSection,
        outline: ReportOutline,
        previous_sections: List[str],
        progress_callback: Optional[Callable] = None,
        section_index: int = 0
    ) -> str:
        """
        使用ReACT模式生成单个章节内容
        """
        logger.info(t('report.reactGenerateSection', title=section.title))
        
        if self.report_logger:
            self.report_logger.log_section_start(section.title, section_index)
        
        system_prompt = SECTION_SYSTEM_PROMPT_TEMPLATE.format(
            report_title=outline.title,
            report_summary=outline.summary,
            simulation_requirement=self.simulation_requirement,
            section_title=section.title,
            tools_description=self._get_tools_description(),
        )
        system_prompt = f"{system_prompt}\n\n{get_language_instruction()}"

        if previous_sections:
            previous_parts = []
            for sec in previous_sections:
                truncated = sec[:4000] + "..." if len(sec) > 4000 else sec
                previous_parts.append(truncated)
            previous_content = "\n\n---\n\n".join(previous_parts)
        else:
            previous_content = "（这是第一个章节）"
        
        user_prompt = SECTION_USER_PROMPT_TEMPLATE.format(
            previous_content=previous_content,
            section_title=section.title,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        tool_calls_count = 0
        max_iterations = 5 
        min_tool_calls = 3 
        conflict_retries = 0 
        used_tools = set()  
        all_tools = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

        report_context = f"章节标题: {section.title}\n项目描述: {self.simulation_requirement}"
        
        for iteration in range(max_iterations):
            if progress_callback:
                progress_callback(
                    "generating", 
                    int((iteration / max_iterations) * 100),
                    t('progress.deepSearchAndWrite', current=tool_calls_count, max=self.MAX_TOOL_CALLS_PER_SECTION)
                )
            
            response = self.llm.chat(
                messages=messages,
                temperature=0.5,
                max_tokens=4096
            )

            if response is None:
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": "（响应为空）"})
                    messages.append({"role": "user", "content": "请继续生成内容。"})
                    continue
                break

            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            has_final_answer = "Final Answer:" in response

            if has_tool_calls and has_final_answer:
                conflict_retries += 1
                if conflict_retries <= 2:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": "【格式错误】请不要在一次回复中同时包含工具调用和 Final Answer。"
                    })
                    continue
                else:
                    first_tool_end = response.find('</tool_call>')
                    if first_tool_end != -1:
                        response = response[:first_tool_end + len('</tool_call>')]
                        tool_calls = self._parse_tool_calls(response)
                        has_tool_calls = bool(tool_calls)
                    has_final_answer = False
                    conflict_retries = 0

            if self.report_logger:
                self.report_logger.log_llm_response(
                    section_title=section.title,
                    section_index=section_index,
                    response=response,
                    iteration=iteration + 1,
                    has_tool_calls=has_tool_calls,
                    has_final_answer=has_final_answer
                )

            if has_final_answer:
                if tool_calls_count < min_tool_calls:
                    messages.append({"role": "assistant", "content": response})
                    unused_tools = all_tools - used_tools
                    unused_hint = f"（推荐使用: {', '.join(unused_tools)}）" if unused_tools else ""
                    messages.append({
                        "role": "user",
                        "content": REACT_INSUFFICIENT_TOOLS_MSG.format(
                            tool_calls_count=tool_calls_count,
                            min_tool_calls=min_tool_calls,
                            unused_hint=unused_hint,
                        ),
                    })
                    continue

                final_answer = response.split("Final Answer:")[-1].strip()
                if self.report_logger:
                    self.report_logger.log_section_content(
                        section_title=section.title,
                        section_index=section_index,
                        content=final_answer,
                        tool_calls_count=tool_calls_count
                    )
                return final_answer

            if has_tool_calls:
                if tool_calls_count >= self.MAX_TOOL_CALLS_PER_SECTION:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": REACT_TOOL_LIMIT_MSG.format(
                            tool_calls_count=tool_calls_count,
                            max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        ),
                    })
                    continue

                call = tool_calls[0]
                if self.report_logger:
                    self.report_logger.log_tool_call(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        parameters=call.get("parameters", {}),
                        iteration=iteration + 1
                    )

                result = self._execute_tool(
                    call["name"],
                    call.get("parameters", {}),
                    report_context=report_context
                )

                if self.report_logger:
                    self.report_logger.log_tool_result(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        result=result,
                        iteration=iteration + 1
                    )

                tool_calls_count += 1
                used_tools.add(call['name'])

                unused_tools = all_tools - used_tools
                unused_hint = ""
                if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                    unused_hint = REACT_UNUSED_TOOLS_HINT.format(unused_list="、".join(unused_tools))

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": REACT_OBSERVATION_TEMPLATE.format(
                        tool_name=call["name"],
                        result=result,
                        tool_calls_count=tool_calls_count,
                        max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        used_tools_str=", ".join(used_tools),
                        unused_hint=unused_hint,
                    ),
                })
                continue

            messages.append({"role": "assistant", "content": response})

            if tool_calls_count < min_tool_calls:
                unused_tools = all_tools - used_tools
                unused_hint = f"（推荐使用: {', '.join(unused_tools)}）" if unused_tools else ""
                messages.append({
                    "role": "user",
                    "content": REACT_INSUFFICIENT_TOOLS_MSG_ALT.format(
                        tool_calls_count=tool_calls_count,
                        min_tool_calls=min_tool_calls,
                        unused_hint=unused_hint,
                    ),
                })
                continue

            final_answer = response.strip()
            if self.report_logger:
                self.report_logger.log_section_content(
                    section_title=section.title,
                    section_index=section_index,
                    content=final_answer,
                    tool_calls_count=tool_calls_count
                )
            return final_answer
        
        messages.append({"role": "user", "content": REACT_FORCE_FINAL_MSG})
        response = self.llm.chat(
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        if response is None:
            final_answer = "生成失败"
        elif "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
        else:
            final_answer = response
        
        if self.report_logger:
            self.report_logger.log_section_content(
                section_title=section.title,
                section_index=section_index,
                content=final_answer,
                tool_calls_count=tool_calls_count
            )
        
        return final_answer
    
    def generate_report(
        self, 
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
        report_id: Optional[str] = None
    ) -> Report:
        """
        生成完整报告
        """
        import uuid
        if not report_id:
            report_id = f"report_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        
        report = Report(
            report_id=report_id,
            simulation_id=self.simulation_id,
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement,
            status=ReportStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        completed_section_titles = []
        
        try:
            ReportManager._ensure_report_folder(report_id)
            self.report_logger = ReportLogger(report_id)
            self.report_logger.log_start(
                simulation_id=self.simulation_id,
                graph_id=self.graph_id,
                simulation_requirement=self.simulation_requirement
            )
            self.console_logger = ReportConsoleLogger(report_id)
            
            ReportManager.update_progress(
                report_id, "pending", 0, t('progress.initReport'),
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            report.status = ReportStatus.PLANNING
            ReportManager.update_progress(
                report_id, "planning", 5, t('progress.startPlanningOutline'),
                completed_sections=[]
            )
            self.report_logger.log_planning_start()
            
            if progress_callback:
                progress_callback("planning", 0, t('progress.startPlanningOutline'))
            
            outline = self.plan_outline(
                progress_callback=lambda stage, prog, msg: 
                    progress_callback(stage, prog // 5, msg) if progress_callback else None
            )
            report.outline = outline
            self.report_logger.log_planning_complete(outline.to_dict())
            
            ReportManager.save_outline(report_id, outline)
            ReportManager.update_progress(
                report_id, "planning", 15, "大纲规划完成",
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            report.status = ReportStatus.GENERATING
            total_sections = len(outline.sections)
            generated_sections = [] 
            
            for i, section in enumerate(outline.sections):
                section_num = i + 1
                base_progress = 20 + int((i / total_sections) * 70)
                
                ReportManager.update_progress(
                    report_id, "generating", base_progress,
                    f"正在生成第 {section_num}/{total_sections} 章节: {section.title}",
                    current_section=section.title,
                    completed_sections=completed_section_titles
                )

                if progress_callback:
                    progress_callback(
                        "generating",
                        base_progress,
                        f"正在生成第 {section_num}/{total_sections} 章节: {section.title}"
                    )
                
                section_content = self._generate_section_react(
                    section=section,
                    outline=outline,
                    previous_sections=generated_sections,
                    progress_callback=lambda stage, prog, msg:
                        progress_callback(
                            stage, 
                            base_progress + int(prog * 0.7 / total_sections),
                            msg
                        ) if progress_callback else None,
                    section_index=section_num
                )
                
                section.content = section_content
                generated_sections.append(f"## {section.title}\n\n{section_content}")
                ReportManager.save_section(report_id, section_num, section)
                completed_section_titles.append(section.title)

                if self.report_logger:
                    self.report_logger.log_section_full_complete(
                        section_title=section.title,
                        section_index=section_num,
                        full_content=f"## {section.title}\n\n{section_content}"
                    )
                
                ReportManager.update_progress(
                    report_id, "generating", 
                    base_progress + int(70 / total_sections),
                    f"章节 {section.title} 生成完成",
                    current_section=None,
                    completed_sections=completed_section_titles
                )
            
            ReportManager.update_progress(
                report_id, "generating", 95, "正在组装完整报告",
                completed_sections=completed_section_titles
            )
            
            report.markdown_content = ReportManager.assemble_full_report(report_id, outline)
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.now().isoformat()
            
            total_time_seconds = (datetime.now() - start_time).total_seconds()
            if self.report_logger:
                self.report_logger.log_report_complete(
                    total_sections=total_sections,
                    total_time_seconds=total_time_seconds
                )
            
            ReportManager.save_report(report)
            ReportManager.update_progress(
                report_id, "completed", 100, t('progress.reportComplete'),
                completed_sections=completed_section_titles
            )
            
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
            
        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            report.status = ReportStatus.FAILED
            report.error = str(e)
            if self.report_logger:
                self.report_logger.log_error(str(e), "failed")
            
            try:
                ReportManager.save_report(report)
                ReportManager.update_progress(
                    report_id, "failed", -1, f"报告生成失败: {str(e)}",
                    completed_sections=completed_section_titles
                )
            except Exception:
                pass
            
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
    
    def chat(
        self, 
        message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        与Report Agent对话
        """
        logger.info(f"Agent对话: {message[:50]}")
        chat_history = chat_history or []
        
        report_content = ""
        try:
            report = ReportManager.get_report_by_simulation(self.simulation_id)
            if report and report.markdown_content:
                report_content = report.markdown_content[:15000]
        except Exception as e:
            logger.warning(f"获取报告失败: {e}")
        
        system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            report_content=report_content if report_content else "（暂无报告）",
            tools_description=self._get_tools_description(),
        )
        system_prompt = f"{system_prompt}\n\n{get_language_instruction()}"

        messages = [{"role": "system", "content": system_prompt}]
        for h in chat_history[-10:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})
        
        tool_calls_made = []
        max_iterations = 2 
        
        for iteration in range(max_iterations):
            response = self.llm.chat(
                messages=messages,
                temperature=0.5
            )
            
            tool_calls = self._parse_tool_calls(response)
            if not tool_calls:
                clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL)
                clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
                return {
                    "response": clean_response.strip(),
                    "tool_calls": tool_calls_made,
                    "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
                }
            
            tool_results = []
            for call in tool_calls[:1]:
                if len(tool_calls_made) >= self.MAX_TOOL_CALLS_PER_CHAT:
                    break
                result = self._execute_tool(call["name"], call.get("parameters", {}))
                tool_results.append({
                    "tool": call["name"],
                    "result": result[:1500]
                })
                tool_calls_made.append(call)
            
            messages.append({"role": "assistant", "content": response})
            observation = "\n".join([f"[{r['tool']}结果]\n{r['result']}" for r in tool_results])
            messages.append({
                "role": "user",
                "content": observation + CHAT_OBSERVATION_SUFFIX
            })
        
        final_response = self.llm.chat(
            messages=messages,
            temperature=0.5
        )
        clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', final_response, flags=re.DOTALL)
        clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
        
        return {
            "response": clean_response.strip(),
            "tool_calls": tool_calls_made,
            "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
        }


class ReportManager:
    """
    报告管理器
    """
    REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'reports')
    
    @classmethod
    def _ensure_reports_dir(cls):
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_report_folder(cls, report_id: str) -> str:
        return os.path.join(cls.REPORTS_DIR, report_id)
    
    @classmethod
    def _ensure_report_folder(cls, report_id: str) -> str:
        folder = cls._get_report_folder(report_id)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    @classmethod
    def _get_report_path(cls, report_id: str) -> str:
        return os.path.join(cls._get_report_folder(report_id), "meta.json")
    
    @classmethod
    def _get_report_markdown_path(cls, report_id: str) -> str:
        return os.path.join(cls._get_report_folder(report_id), "full_report.md")
    
    @classmethod
    def _get_outline_path(cls, report_id: str) -> str:
        return os.path.join(cls._get_report_folder(report_id), "outline.json")
    
    @classmethod
    def _get_progress_path(cls, report_id: str) -> str:
        return os.path.join(cls._get_report_folder(report_id), "progress.json")
    
    @classmethod
    def _get_section_path(cls, report_id: str, section_index: int) -> str:
        return os.path.join(cls._get_report_folder(report_id), f"section_{section_index:02d}.md")
    
    @classmethod
    def _get_agent_log_path(cls, report_id: str) -> str:
        return os.path.join(cls._get_report_folder(report_id), "agent_log.jsonl")
    
    @classmethod
    def _get_console_log_path(cls, report_id: str) -> str:
        return os.path.join(cls._get_report_folder(report_id), "console_log.txt")
    
    @classmethod
    def get_console_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        log_path = cls._get_console_log_path(report_id)
        if not os.path.exists(log_path):
            return {"logs": [], "total_lines": 0, "from_line": 0, "has_more": False}
        
        logs = []
        total_lines = 0
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    logs.append(line.rstrip('\n\r'))
        return {"logs": logs, "total_lines": total_lines, "from_line": from_line, "has_more": False}
    
    @classmethod
    def get_agent_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        log_path = cls._get_agent_log_path(report_id)
        if not os.path.exists(log_path):
            return {"logs": [], "total_lines": 0, "from_line": 0, "has_more": False}
        
        logs = []
        total_lines = 0
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    try:
                        logs.append(json.loads(line.strip()))
                    except:
                        continue
        return {"logs": logs, "total_lines": total_lines, "from_line": from_line, "has_more": False}
    
    @classmethod
    def save_outline(cls, report_id: str, outline: ReportOutline) -> None:
        cls._ensure_report_folder(report_id)
        with open(cls._get_outline_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(outline.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def save_section(cls, report_id: str, section_index: int, section: ReportSection) -> str:
        cls._ensure_report_folder(report_id)
        cleaned_content = cls._clean_section_content(section.content, section.title)
        md_content = f"## {section.title}\n\n{cleaned_content}\n\n"
        file_path = cls._get_section_path(report_id, section_index)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return file_path
    
    @classmethod
    def _clean_section_content(cls, content: str, section_title: str) -> str:
        if not content: return content
        lines = content.strip().split('\n')
        cleaned_lines = []
        skip_next_empty = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            if heading_match:
                title_text = heading_match.group(2).strip()
                if i < 5 and (title_text == section_title or title_text.replace(' ', '') == section_title.replace(' ', '')):
                    skip_next_empty = True
                    continue
                cleaned_lines.append(f"**{title_text}**")
                cleaned_lines.append("")
                continue
            if skip_next_empty and stripped == '':
                skip_next_empty = False
                continue
            skip_next_empty = False
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines).strip()
    
    @classmethod
    def update_progress(cls, report_id: str, status: str, progress: int, message: str, current_section: str = None, completed_sections: List[str] = None) -> None:
        cls._ensure_report_folder(report_id)
        progress_data = {
            "status": status, "progress": progress, "message": message,
            "current_section": current_section, "completed_sections": completed_sections or [],
            "updated_at": datetime.now().isoformat()
        }
        with open(cls._get_progress_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_generated_sections(cls, report_id: str) -> List[Dict[str, Any]]:
        folder = cls._get_report_folder(report_id)
        if not os.path.exists(folder): return []
        sections = []
        for filename in sorted(os.listdir(folder)):
            if filename.startswith('section_') and filename.endswith('.md'):
                with open(os.path.join(folder, filename), 'r', encoding='utf-8') as f:
                    sections.append({
                        "filename": filename,
                        "section_index": int(filename.split('_')[1].split('.')[0]),
                        "content": f.read()
                    })
        return sections
    
    @classmethod
    def assemble_full_report(cls, report_id: str, outline: ReportOutline) -> str:
        md_content = f"# {outline.title}\n\n> {outline.summary}\n\n---\n\n"
        sections = cls.get_generated_sections(report_id)
        for s in sections: md_content += s["content"]
        md_content = cls._post_process_report(md_content, outline)
        with open(cls._get_report_markdown_path(report_id), 'w', encoding='utf-8') as f:
            f.write(md_content)
        return md_content
    
    @classmethod
    def _post_process_report(cls, content: str, outline: ReportOutline) -> str:
        lines = content.split('\n')
        processed_lines = []
        section_titles = {s.title for s in outline.sections}
        prev_was_heading = False
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                if level == 1:
                    if title == outline.title: processed_lines.append(line)
                    elif title in section_titles: processed_lines.append(f"## {title}")
                    else: processed_lines.append(f"**{title}**\n")
                elif level == 2:
                    processed_lines.append(line)
                else:
                    processed_lines.append(f"**{title}**\n")
                prev_was_heading = True
                i += 1; continue
            processed_lines.append(line)
            prev_was_heading = False
            i += 1
        return '\n'.join(processed_lines)
    
    @classmethod
    def save_report(cls, report: Report) -> None:
        cls._ensure_report_folder(report.report_id)
        with open(cls._get_report_path(report.report_id), 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        if report.outline: cls.save_outline(report.report_id, report.outline)
        if report.markdown_content:
            with open(cls._get_report_markdown_path(report.report_id), 'w', encoding='utf-8') as f:
                f.write(report.markdown_content)
    
    @classmethod
    def get_report(cls, report_id: str) -> Optional[Report]:
        path = cls._get_report_path(report_id)
        if not os.path.exists(path): return None
        with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
        outline = None
        if data.get('outline'):
            sections = [ReportSection(title=s['title'], content=s.get('content', '')) for s in data['outline'].get('sections', [])]
            outline = ReportOutline(title=data['outline']['title'], summary=data['outline']['summary'], sections=sections)
        return Report(report_id=data['report_id'], simulation_id=data['simulation_id'], graph_id=data['graph_id'], simulation_requirement=data['simulation_requirement'], status=ReportStatus(data['status']), outline=outline, markdown_content=data.get('markdown_content', ''), created_at=data.get('created_at', ''), completed_at=data.get('completed_at', ''), error=data.get('error'))
    
    @classmethod
    def get_report_by_simulation(cls, simulation_id: str) -> Optional[Report]:
        cls._ensure_reports_dir()
        for item in os.listdir(cls.REPORTS_DIR):
            report = cls.get_report(item)
            if report and report.simulation_id == simulation_id: return report
        return None
    
    @classmethod
    def list_reports(cls, simulation_id: Optional[str] = None, limit: int = 50) -> List[Report]:
        cls._ensure_reports_dir()
        reports = []
        for item in os.listdir(cls.REPORTS_DIR):
            report = cls.get_report(item)
            if report and (simulation_id is None or report.simulation_id == simulation_id): reports.append(report)
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return reports[:limit]
    
    @classmethod
    def delete_report(cls, report_id: str) -> bool:
        import shutil
        folder_path = cls._get_report_folder(report_id)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            return True
        return False
