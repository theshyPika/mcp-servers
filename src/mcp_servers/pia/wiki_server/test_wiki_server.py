import logging
import sys

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr)])

import argparse
import asyncio
import atexit
import json
import time
from datetime import datetime
from inspect import Parameter, Signature
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

from app.logger import logger
from app.tool.base import BaseTool
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.plc import PLCGenerator
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate


class MCPServer:
    """MCP Server implementation with tool registration and management."""

    def __init__(self, name: str = "PIA WIKI"):
        self.server = FastMCP(name)
        self.tools: Dict[str, BaseTool] = {}

        # Initialize standard tools
        self.tools["bash"] = Bash()
        self.tools["editor"] = StrReplaceEditor()
        self.tools["terminate"] = Terminate()

        @self.server.tool(
            name="rag_regulatory",
            description="检索公司内部规章制度信息",
        )
        async def rag_regulatory(
            query: str,
        ) -> Union[str, Dict]:
            """检索PIA 公司内部规章制度。
            Args:
                query (str):
            """
            time.sleep(20)
            return """
# 住宿费报销标准 / Accommodation Reimbursement Criteria
## 报销限额标准 / Reimbursement Limits

| 职级 / Position Level          | 中国大陆地区 / Mainland China                                                                 | 中国大陆以外（含港澳台地区） / Outside Mainland China (Including HK, Macau & Taiwan) |
|-------------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------|
|                              | 一线/准一线城市及省会 / First Tier/Quasi First Tier & Provincial Capitals                  | 其他城市 / Other Cities                           |
|-------------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------|
| 公司中层及以上 / Manager Level | 限额 450 元/人/晚 / 450 RMB per person per night                                           | 限额 500-1,000 元/人/晚 / 500-1,000 RMB          |
| (经理、主管)                  |                                                                                            |                                                   |
| 其他员工 / Other Employees    | 限额 300 元/人/晚 / 300 RMB per person per night                                           | 限额 350-800 元/人/晚 / 350-800 RMB              |
|                               | 其他城市限额 250 元/人/晚 / 250 RMB for Other Cities                                       |                                                   |
---

## 注释 / Notes

1. **城市分类说明 / City Classification**
- **一线/准一线城市**
    北京、上海、广州、深圳、天津、南京、武汉、西安、成都、重庆、杭州、青岛、大连、宁波、苏州、长沙
    *Beijing, Shanghai, Guangzhou, Shenzhen, Tianjin, Nanjing, Wuhan, Xi'an, Chengdu, Chongqing, Hangzhou, Qingdao, Dalian, Ningbo, Suzhou, Changsha*

- **省会级城市**
    石家庄、沈阳、哈尔滨、杭州、福州、济南、广州、武汉、成都、昆明、兰州、太原、长春、南京、合肥、南昌、郑州、长沙、海口、贵阳、西安、西宁、呼和浩特、乌鲁木齐、银川、南宁、拉萨
    *Shijiazhuang, Shenyang, Harbin, Hangzhou, Fuzhou, Jinan, Guangzhou, Wuhan, Chengdu, Kunming, Lanzhou, Taiyuan, Changchun, Nanjing, Hefei, Nanchang, Zhengzhou, Changsha, Haikou, Guiyang, Xi'an, Xining, Hohhot, Urumqi, Yinchuan, Nanning, Lhasa*

2. **特殊岗位说明 / Special Positions**
大客户经理、项目经理、方案组组长、事业部设计组组长享受经理级别报销标准
*Key Account Manager, Project Manager, Concept Team Leader, and BU Design Team Leader enjoy the reimbursement standard at manager level.*"""

    def register_tool(self, tool: BaseTool, method_name: Optional[str] = None) -> None:
        """Register a tool with parameter validation and documentation."""
        tool_name = method_name or tool.name
        tool_param = tool.to_param()
        tool_function = tool_param["function"]

        # Define the async function to be registered
        async def tool_method(**kwargs):
            logger.info(f"Executing {tool_name}: {kwargs}")
            result = await tool.execute(**kwargs)

            logger.info(f"Result of {tool_name}: {result}")

            # Handle different types of results (match original logic)
            if hasattr(result, "model_dump"):
                return json.dumps(result.model_dump())
            elif isinstance(result, dict):
                return json.dumps(result)
            return result

        # Set method metadata
        tool_method.__name__ = tool_name
        tool_method.__doc__ = self._build_docstring(tool_function)
        tool_method.__signature__ = self._build_signature(tool_function)

        # Store parameter schema (important for tools that access it programmatically)
        param_props = tool_function.get("parameters", {}).get("properties", {})
        required_params = tool_function.get("parameters", {}).get("required", [])
        tool_method._parameter_schema = {
            param_name: {
                "description": param_details.get("description", ""),
                "type": param_details.get("type", "any"),
                "required": param_name in required_params,
            }
            for param_name, param_details in param_props.items()
        }

        # Register with server
        self.server.tool()(tool_method)
        logger.info(f"Registered tool: {tool_name}")

    def _build_docstring(self, tool_function: dict) -> str:
        """Build a formatted docstring from tool function metadata."""
        description = tool_function.get("description", "")
        param_props = tool_function.get("parameters", {}).get("properties", {})
        required_params = tool_function.get("parameters", {}).get("required", [])

        # Build docstring (match original format)
        docstring = description
        if param_props:
            docstring += "\n\nParameters:\n"
            for param_name, param_details in param_props.items():
                required_str = (
                    "(required)" if param_name in required_params else "(optional)"
                )
                param_type = param_details.get("type", "any")
                param_desc = param_details.get("description", "")
                docstring += (
                    f"    {param_name} ({param_type}) {required_str}: {param_desc}\n"
                )

        return docstring

    def _build_signature(self, tool_function: dict) -> Signature:
        """Build a function signature from tool function metadata."""
        param_props = tool_function.get("parameters", {}).get("properties", {})
        required_params = tool_function.get("parameters", {}).get("required", [])

        parameters = []

        # Follow original type mapping
        for param_name, param_details in param_props.items():
            param_type = param_details.get("type", "")
            default = Parameter.empty if param_name in required_params else None

            # Map JSON Schema types to Python types (same as original)
            annotation = Any
            if param_type == "string":
                annotation = str
            elif param_type == "integer":
                annotation = int
            elif param_type == "number":
                annotation = float
            elif param_type == "boolean":
                annotation = bool
            elif param_type == "object":
                annotation = dict
            elif param_type == "array":
                annotation = list

            # Create parameter with same structure as original
            param = Parameter(
                name=param_name,
                kind=Parameter.KEYWORD_ONLY,
                default=default,
                annotation=annotation,
            )
            parameters.append(param)

        return Signature(parameters=parameters)

    async def cleanup(self) -> None:
        """Clean up server resources."""
        logger.info("Cleaning up resources")
        # Follow original cleanup logic - only clean browser tool
        if "browser" in self.tools and hasattr(self.tools["browser"], "cleanup"):
            await self.tools["browser"].cleanup()

    def register_all_tools(self) -> None:
        """Register all tools with the server."""
        for tool in self.tools.values():
            self.register_tool(tool)

    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server."""
        # Register all tools
        self.register_all_tools()

        # Register cleanup function (match original behavior)
        atexit.register(lambda: asyncio.run(self.cleanup()))

        # Start server (with same logging as original)
        logger.info(f"Starting OpenManus server ({transport} mode)")
        self.server.run(transport=transport)


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
