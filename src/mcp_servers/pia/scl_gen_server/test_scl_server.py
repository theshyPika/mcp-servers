import sys
import argparse
import asyncio
import atexit
import json
import os
from datetime import datetime
from inspect import Parameter, Signature
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from fastmcp import FastMCP

mcp = FastMCP("scl_coder")
@mcp.tool(
    name="gen_scl_code",
    description="""生成符合IEC 61131-3标准的SCL（Structured Control Language）代码。功能包括：
    1. 根据自然语言描述生成可执行的SCL代码片段
    2. 支持纯代码模式（默认）和完整输出模式
    3. 可选代码文件保存功能
    注意：尽量使用纯代码模式，并取消保存文件。
    """,
)
async def gen_scl_code(
    query: str,
    pure_mode: bool = True,
    save_to_file: bool = False,
    file_path: Optional[str] = None,
) -> Union[str, Dict]:
    """SCL代码生成器

    Args:
        query (str): 代码生成需求描述（需包含明确的控制逻辑和I/O参数）
        pure_mode (bool): True-返回纯净SCL代码，False-返回完整生成过程数据
        save_to_file (bool): 是否保存为.scl文件，开启时需要提供file_path
        file_path (Optional[str]): 文件保存路径（需包含.scl扩展名）

    Returns:
        Union[str, Dict]: 根据pure_mode返回代码字符串或完整响应

    Raises:
        ValueError: 文件保存参数不匹配时抛出
    """
    if save_to_file and not file_path:
        raise ValueError("启用文件保存时必须提供file_path参数")

    scl_generator = PLCGenerator()
    full_result = ""

    try:
        for chunk in scl_generator.generate_scl(user_input=query):
            if isinstance(chunk, str):
                try:
                    chunk_data = json.loads(chunk)
                    full_result += chunk_data.get("content", "")
                except json.JSONDecodeError:
                    full_result += chunk

        # 文件保存,延迟写入
        if save_to_file and file_path:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            code = PLCGenerator.extract_code(full_result) or full_result
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: Path(file_path).write_text(code, encoding="utf-8")
            )

        # 处理返回模式
        final_code = PLCGenerator.extract_code(full_result)
        if not final_code:
            return f"SCL代码：{full_result}"

        return (
            final_code
            if pure_mode
            else {
                "status": "success",
                "code": final_code,
                "raw_response": full_result,
                "saved_path": file_path if save_to_file else None,
            }
        )

    except Exception as e:
        return f"{str(e)}"
    
def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="OpenManus MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Communication method: stdio or http (default: stdio)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Create and run server (maintaining original flow)
    server = MCPServer()
    server.run(transport=args.transport)
