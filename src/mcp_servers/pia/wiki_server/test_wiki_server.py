import sys
import argparse
import time
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP
mcp = FastMCP("pia_wiki")
@mcp.tool(
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

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="OpenManus MCP Server")
    parser.add_argument(
        "-t","--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Communication method: stdio or http (default: stdio)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport == "http":
            mcp.run(transport="http", host="0.0.0.0", port=9100, path="/mcp")
        else:
            print(f"Error: Unsupported transport protocol '{args.transport}'", file=sys.__stderr__)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nServer shutdown requested...", file=sys.__stderr__)
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.__stderr__)
        sys.exit(1)

