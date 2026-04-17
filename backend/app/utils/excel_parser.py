"""
DealSim Excel/CSV Parser Utility
Extracts text and structured data from traditional financial models.
"""

import pandas as pd
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger('dealsim.excel_parser')

class ExcelParser:
    """Excel/CSV解析器"""
    
    @staticmethod
    def parse(file_path: str) -> str:
        """
        解析文件内容并返回文本描述
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path)
                return ExcelParser._df_to_text(df, "CSV Data")
            elif ext in ['.xlsx', '.xls']:
                # 解析所有Sheet
                all_text = []
                xl = pd.ExcelFile(file_path)
                for sheet_name in xl.sheet_names:
                    df = xl.parse(sheet_name)
                    all_text.append(ExcelParser._df_to_text(df, f"Sheet: {sheet_name}"))
                return "\n\n---\n\n".join(all_text)
            else:
                return ""
        except Exception as e:
            logger.error(f"解析 {file_path} 失败: {str(e)}")
            return f"Error parsing file {os.path.basename(file_path)}: {str(e)}"

    @staticmethod
    def _df_to_text(df: pd.DataFrame, title: str) -> str:
        """将DataFrame转换为易于LLM阅读的文本"""
        if df.empty:
            return f"{title}: (Empty)"
            
        # 限制行列，避免文本爆炸
        max_rows = 100
        max_cols = 20
        
        display_df = df.iloc[:max_rows, :max_cols]
        
        # 转换为 Markdown 表格格式（LLM最喜欢的结构）
        md_table = display_df.to_markdown(index=False)
        
        result = f"### {title}\n\n{md_table}"
        
        if len(df) > max_rows or len(df.columns) > max_cols:
            result += f"\n\n(Truncated: Original size {len(df)}x{len(df.columns)})"
            
        return result
