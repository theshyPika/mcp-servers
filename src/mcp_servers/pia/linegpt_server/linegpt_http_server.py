import argparse
import json
import sys
import time
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from fastmcp import FastMCP
import pytz

mcp = FastMCP("linegpt")

# @mcp.resource("api://login/{Name}/{Password}")
# def login(Name: str, Password: str) -> Union[str, Dict]:
#     """Handle PIA IAS APP login request and return JWT token."""

#     api_url = "https://pia-ias-demo.piagroup.com/app/authService/LocalAuthentificationServer/Login"
#     try:
#         response = requests.post(
#             api_url,
#             json={"Name": Name, "Password": Password},
#             timeout=10,
#             verify=False,
#         )
#         response.raise_for_status()
#         return response.text
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(
#             status_code=400, detail=f"Authentication failed: {str(e)}"
#         )

# @mcp.resource(
#     "api://producedPartHistory/{lineId}/{startTime}/{endTime}/{frameSpan}/{authorization}"
# )
# def get_produced_part_history(
#     lineId: str,
#     startTime: str,
#     endTime: str,
#     frameSpan: int,
#     authorization: str,
# ) -> Dict:
#     """Get produced part history by line ID with time range and frame span.
#     Args:
#         startTime/endTime:
#         lineId：产线ID，如果用户未提供，默认lineId=34498e03-ffca-4b01-9799-c8e533c0604e
#         frameSpan: 该字段表示API响应中各个时间段的时间跨度，可取值为[1,2,3,4],分别对应[10分钟，一小时，一天，一个月]
#         authorization: 通过PIA IAS APP login得到的Token
#     """

#     api_url = "https://pia-ias-demo.piagroup.com/app/optimumService/ProducedPartServer/GetProducedPartHistoryByLine"

#     # Validate frameSpan
#     if frameSpan not in [1, 2, 3, 4]:
#         raise HTTPException(
#             status_code=400,
#             detail="frameSpan must be 1(10min), 2(1h), 3(1d) or 4(1month)",
#         )

#     # Parse and format time strings
#     try:
#         from datetime import datetime

#         # For daily data (frameSpan=3), use fixed 16:00:00 time
#         if frameSpan == 3:
#             start_dt = datetime.strptime(startTime.split("T")[0], "%Y-%m-%d")
#             end_dt = datetime.strptime(endTime.split("T")[0], "%Y-%m-%d")
#             params = {
#                 "lineId": lineId,
#                 "startTime": f"{start_dt.strftime('%Y-%m-%d')}T16:00:00.000Z",
#                 "endTime": f"{end_dt.strftime('%Y-%m-%d')}T16:00:00.000Z",
#                 "frameSpan": frameSpan,
#             }
#         else:
#             # For other frameSpan values, use input time directly
#             params = {
#                 "lineId": lineId,
#                 "startTime": f"{startTime}.000Z",
#                 "endTime": f"{endTime}.000Z",
#                 "frameSpan": frameSpan,
#             }

#         headers = {
#             "accept": "application/json",
#             "authorization": f"Bearer {authorization}",
#         }
#         response = requests.get(
#             api_url, params=params, headers=headers, timeout=60, verify=False
#         )
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Failed to get produced part history: {str(e)}",
#         )


# 登录工具（原login资源）
@mcp.tool(
    name="login",
    description="Handle PIA IAS APP login request and return JWT token",
)
def login_tool() -> Union[str, Dict]:
    name: str = "nesinext"
    password: str = "Ne$!next"
    api_url = "https://pia-ias-demo.piagroup.com/app/authService/LocalAuthentificationServer/Login"
    try:
        response = requests.post(
            api_url,
            json={"Name": name, "Password": password},
            timeout=10,
            verify=False,
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return {
            "error_type": "authentication_error",
            "message": f"Authentication failed: {str(e)}",
            "details": {"status_code": 400},
        }


# 生产历史工具（原get_produced_part_history资源）
@mcp.tool(
    name="daily_production_report",
    description="""获取指定日期和班别的生产数据报告（固定按天统计）
    \n Args:
        date: 日期格式YYYY-MM-DD
        shift_type: 班别（day-白班 04:00-12:00, night-夜班 12:00-20:00, all-全天 04:00-20:00）
        line_id：产线ID，默认34498e03-ffca-4b01-9799-c8e533c0604e
        authorization: 通过PIA IAS APP login得到的Token""",
)
def daily_production_report(
    date: str,
    shift_type: str,
    authorization: str,
    line_id: str = "34498e03-ffca-4b01-9799-c8e533c0604e",
) -> Dict:
    """获取指定日期和班别的生产数据报告
    Args:
        date: 日期字符串，格式为YYYY-MM-DD
        shift_type: 班别类型，可选值：
            - 'day': 白班 (04:00-12:00)
            - 'night': 夜班 (12:00-20:00) 
            - 'all': 全天 (04:00-20:00)
        authorization: 认证令牌，通过login接口获取
        line_id: 产线ID，默认为34498e03-ffca-4b01-9799-c8e533c0604e

    Returns:
        包含生产数据的字典，格式为{"data": [...]}
        如果出错则返回错误信息字典，包含error_type、message和details字段

    Raises:
        无显式抛出异常，所有错误都通过返回值处理
    """
    # 参数验证
    if shift_type not in ["day", "night", "all"]:
        return {
            "error_type": "invalid_shift_type",
            "message": "班别必须是day(白班), night(夜班)或all(全天)",
            "details": {"allowed_values": ["day", "night", "all"]},
        }

    # 根据班别计算时间段
    try:
        from datetime import datetime

        # 固定使用frameSpan=3（按天统计）
        frame_span = 3

        # 计算开始和结束时间
        if shift_type == "day":
            start_time = f"{date}T04:00:00.000Z"
            end_time = f"{date}T12:00:00.000Z"
        elif shift_type == "night":
            start_time = f"{date}T12:00:00.000Z"
            end_time = f"{date}T20:00:00.000Z"
        else:  # all
            start_time = f"{date}T04:00:00.000Z"
            end_time = f"{date}T20:00:00.000Z"

        # 使用固定16:00:00的时间格式（按天统计的特殊要求）
        start_dt = datetime.strptime(date, "%Y-%m-%d")
        end_dt = datetime.strptime(date, "%Y-%m-%d")
        params = {
            "lineId": line_id,
            "startTime": f"{start_dt.strftime('%Y-%m-%d')}T16:00:00.000Z",
            "endTime": f"{end_dt.strftime('%Y-%m-%d')}T16:00:00.000Z",
            "frameSpan": frame_span,
        }

        # 发送请求
        api_url = "https://pia-ias-demo.piagroup.com/app/optimumService/ProducedPartServer/GetProducedPartHistoryByLine"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {authorization}",
        }
        response = requests.get(
            api_url, params=params, headers=headers, timeout=60, verify=False
        )
        response.raise_for_status()
        return {"data": response.json()}  # Wrap list in dict
    except Exception as e:
        return {
            "error_type": "api_error",
            "message": "Failed to get produced part history",
            "details": {"exception": str(e)},
        }


# 班次对比（白班04:00-12:00,夜班12:20:00）例：白班OEE为85%，夜班OEE为82%，白班做得多。
#             curl -k -X GET \
# 'https://pia-ias-demo.piagroup.com/app/oeeService/OeeServer/GetOeeValue?lineId=34498e03-ffca-4b01-9799-c8e533c0604e&startDate=2025-04-10T04:00:00.000Z&endDate=2025-04-10T12:00:00.000Z' \
# -H 'accept: application/json' \
# -H 'accept-encoding: gzip, deflate, br, zstd' \
# -H 'accept-language: zh' \
# -H 'authorization: Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IklBUyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJMb2NhbEF1dGhTZXJ2aWNlIiwiZXhwIjoxNzQ0MjY3OTY5LCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1lIjoibmVzaW5leHQiLCJuYW1lIjoibmVzaW5leHQiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJuZXNpbmV4dCIsInVzZXJfaWQiOiJlODc3NTlkOC02ZGFkLTQwMzMtODVjZC1mZTlhMmM2YTViNGUiLCJpYXQiOjE3NDQyNjQzNjksIm5iZiI6MTc0NDI2NDM2OX0.2-48H3HVH1XTk9FP_OoeMHmMIyCgH0nikU6pqOLy5oI'
# 班次对比工具


@mcp.tool(
    name="shift_performance_analysis",
    description="""提供指定日期白班或夜班的OEE性能数据，自动处理时间段转换。
    \n Args:
    date: 日期格式YYYY-MM-DD
    shift_type: 班别（day-白班 04:00-12:00, night-夜班 12:00-20:00）
    line_id：产线ID，默认34498e03-ffca-4b01-9799-c8e533c0604e
    authorization: 通过PIA IAS APP login得到的Token
    """,
)
def shift_performance_analysis(
    date: str, shift_type: str, authorization: str, 
    line_id: str = "34498e03-ffca-4b01-9799-c8e533c0604e"
) -> Union[Dict, str]:
    """获取指定日期和班别的OEE性能数据"""
    api_url = "https://pia-ias-demo.piagroup.com/app/oeeService/OeeServer/GetOeeValue"

    # 根据班别自动计算时间段
    if shift_type == "day":
        start_time = f"{date}T04:00:00.000Z"
        end_time = f"{date}T12:00:00.000Z"
    elif shift_type == "night":
        start_time = f"{date}T12:00:00.000Z"
        end_time = f"{date}T20:00:00.000Z"
    else:
        return {
            "error_type": "invalid_shift_type",
            "message": "班别必须是day(白班)或night(夜班)",
            "details": {"allowed_values": ["day", "night"]}
        }

    # 配置请求参数和头部
    params = {"lineId": line_id, "startDate": start_time, "endDate": end_time}

    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh",
        "authorization": f"Bearer {authorization}",
    }

    try:
        response = requests.get(
            api_url, params=params, headers=headers, timeout=15, verify=False
        )
        response.raise_for_status()
        return {"data": response.json()}  # 包装在字典中返回

    except requests.exceptions.RequestException as e:
        return {
            "error_type": "oee_fetch_error",
            "message": f"OEE数据获取失败: {str(e)}",
            "details": {
                "status_code": e.response.status_code if e.response else 500,
                "request_params": params,
            },
        }


# 现在有哪些设备处于故障状态？
# http GET '  https://pia-ias-demo.piagroup.com/app/machinedataService/MessageDataServer/GetCurrentByLineId?lineId=34498e03-ffca-4b01-9799-c8e533c0604e'   \
# accept:application/json \
# accept-encoding:'gzip, deflate, br, zstd' \
# accept-language:zh \
# authorization:'Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IklBUyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJMb2NhbEF1dGhTZXJ2aWNlIiwiZXhwIjoxNzQ0MzM4NzI5LCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1lIjoibmVzaW5leHQiLCJuYW1lIjoibmVzaW5leHQiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJuZXNpbmV4dCIsInVzZXJfaWQiOiJlODc3NTlkOC02ZGFkLTQwMzMtODVjZC1mZTlhMmM2YTViNGUiLCJpYXQiOjE3NDQzMzUxMjksIm5iZiI6MTc0NDMzNTEyOX0.AA1UL3s6O_cnm3AuPeSITdjHMP_RzuDu9wRDMYJiPOw'
@mcp.tool(
    name="get_faulty_equipment_v2",
    description="根据实时消息数据识别处于故障状态（Error类别）的生产设备",
)
def get_faulty_equipment_v2(
    line_id: str, authorization: str, include_warnings: bool = False
) -> Union[Dict, List]:
    """增强版故障设备检测（支持多状态筛选）"""
    api_url = "https://pia-ias-demo.piagroup.com/app/machinedataService/MessageDataServer/GetCurrentByLineId"

    params = {"lineId": line_id}
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh",
        "authorization": f"Bearer {authorization}",
    }

    try:
        response = requests.get(
            api_url, params=params, headers=headers, timeout=15, verify=False
        )
        response.raise_for_status()

        raw_data = response.json()
        # 状态过滤逻辑优化
        target_categories = ["Error"]
        if include_warnings:
            target_categories.append("Warning")

        # 设备状态智能聚合
        device_status = {}
        for entry in raw_data:
            if entry.get("category") in target_categories:
                station_id = entry.get("stationId")
                if not station_id:
                    continue
                    
                # 保留最新状态信息
                if (
                    station_id not in device_status
                    or entry.get("timestamp", 0)
                    > device_status[station_id].get("latest_timestamp", 0)
                ):
                    device_status[station_id] = {
                        "line_name": entry.get("lineName"),
                        "group_name": entry.get("groupName"),
                        "station_name": entry.get("stationName"),
                        "latest_message": entry.get("text"),
                        "latest_timestamp": entry.get("timestamp", 0),
                        "error_count": device_status.get(station_id, {}).get(
                            "error_count", 0
                        )
                        + 1,
                        "message_codes": list(
                            set(
                                device_status.get(station_id, {}).get(
                                    "message_codes", []
                                )
                                + [entry.get("messageId")]
                            )
                        ),
                    }

        # 结构化输出
        return {
            "line_id": line_id,
            "total_messages": len(raw_data),
            "faulty_devices": [
                {
                    "station_id": k,
                    **v,
                    "status_level": (
                        "CRITICAL" if "Error" in target_categories else "WARNING"
                    ),
                }
                for k, v in device_status.items()
            ],
            "data_snapshot_time": datetime.utcnow().isoformat() + "Z",
        }

    except requests.exceptions.RequestException as e:
        return {
            "error_type": "equipment_status_error",
            "message": f"设备状态查询失败: {str(e)}",
            "details": {
                "status_code": e.response.status_code if e.response else 500,
                "request_params": params,
            },
        }
    except KeyError as e:
        return {
            "error_type": "data_parse_error",
            "message": f"响应数据缺少必要字段: {str(e)}"
        }


@mcp.tool(
    name="analyze_production_line_performance",
    description="""
    产线性能分析及优化建议方法

    参数：
    line_id - 产线ID
    token - 认证令牌

    返回：
    analysis_guide - 分析步骤和标准指南
    data_summary - 组织好的产线性能数据
    """,
)
def analyze_production_line_performance(
    token,
    line_id="34498e03-ffca-4b01-9799-c8e533c0604e",
):
    """
    产线性能分析及优化建议方法

    参数：
    line_id - 产线ID
    token - 认证令牌

    返回：
    analysis_guide - 分析步骤和标准指南
    data_summary - 组织好的产线性能数据
    """

    # 生成时间范围（前一天凌晨到当天凌晨 UTC时间）
    now = datetime.now(pytz.utc)
    start_time = (now - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 调用API获取数据（带重试机制）
    def call_api(url_suffix, max_retries=3):
        url = f"https://pia-ias-demo.piagroup.com/app/optimumService/ManagementReportServer/{url_suffix}"
        params = {
            "lineId": line_id,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "count": 5,
        }
        headers = {"authorization": f"Bearer {token}"}
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    verify=False,
                    timeout=15  # 添加超时控制
                )
                if response.status_code == 200:
                    return {"data": response.json()}
                elif response.status_code >= 500:
                    print(f"API服务器错误({response.status_code})，重试 {attempt + 1}/{max_retries}")
                    continue
                else:
                    return {
                        "error": f"API请求失败: {response.status_code}",
                        "details": response.text[:200]  # 截取部分错误信息
                    }
            except requests.exceptions.RequestException as e:
                print(f"API调用异常(尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "error": "API请求失败",
                        "details": str(e),
                        "retries_exhausted": True
                    }
            time.sleep(1 * (attempt + 1))  # 指数退避
        
        return {"error": "API请求失败，重试次数用尽"}

    # 获取并组织数据（带错误检查）
    messages_result = call_api("GetManagementReportMessagesByStations")
    process_result = call_api("GetManagementReportProcessTimesByStations")
    
    # 检查API返回数据有效性
    if "error" in messages_result:
        return {"error": f"获取消息数据失败: {messages_result['error']}"}
    if "error" in process_result:
        return {"error": f"获取节拍数据失败: {process_result['error']}"}
    
    messages_data = messages_result.get("data", [])
    process_data = process_result.get("data", [])

    # 构建分析指南
    analysis_guide = {
        "analysis_steps": [
            {
                "step": 1,
                "name": "技术性停机分析",
                "description": "检查报警信息是否指向设备硬件/软件故障",
                "criteria": [
                    "报警代码直接关联设备部件（如'电机过载 E01'）",
                    "报警描述包含明确的设备故障关键词"
                ],
                "data_fields": ["故障", "总时长(秒)"]
            },
            {
                "step": 2,
                "name": "节拍时间分析",
                "description": "对比实际中位时间与标称时间差异",
                "criteria": [
                    "差异超过±5%表示需要关注",
                    "差异超过±10%表示严重问题"
                ],
                "data_fields": ["实际中位时间", "标称时间", "差异(%)"]
            },
            {
                "step": 3,
                "name": "瓶颈工站识别",
                "description": "识别影响整体产线效率的关键工站",
                "criteria": [
                    "停机时间最长的工站",
                    "节拍时间差异最大的工站",
                    "故障次数最多的工站"
                ],
                "data_fields": ["工站", "总时长(秒)", "差异(%)", "次数"]
            }
        ],
        "notes": [
            "1. 优先处理技术性停机问题，通常对OEE影响最大",
            "2. 节拍时间差异可能是设备老化或工艺参数不当导致",
            "3. 多次重复故障可能表明存在系统性质量问题"
        ]
    }

    # 安全处理数据
    def safe_process_messages(data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return []
        return [
            {
                "station": (m.get("stations") or [None])[0] if isinstance(m, dict) else None,
                "故障次数": m.get("count", 0) if isinstance(m, dict) else 0,
                "总停机时间(秒)": m.get("duration", 0) if isinstance(m, dict) else 0,
                "最近故障": m.get("messageText", "无描述") if isinstance(m, dict) else "无描述",
            }
            for m in (data if isinstance(data, list) else [])
        ]

    def safe_process_processes(data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return []
        return [
            {
                "工站": item.get("item1", {}).get("name", "未知工站") if isinstance(item, dict) else "未知工站",
                "实际中位时间": item.get("item1", {}).get("median", 0) if isinstance(item, dict) else 0,
                "标称时间": item.get("item1", {}).get("nominalCycleTime", 1) if isinstance(item, dict) else 1,
                "差异百分比": f"{round((item.get('item1', {}).get('median', 0)/max(1, item.get('item1', {}).get('nominalCycleTime', 1))-1)*100,1)}%" 
                    if isinstance(item, dict) else "0%",
            }
            for item in (data if isinstance(data, list) else [])
        ]

    return json.dumps(
        {
            "analysis_guide": analysis_guide,
            "data_summary": {
                "messages_data": safe_process_messages(messages_data),
                "process_data": safe_process_processes(process_data),
            },
        },
        ensure_ascii=False,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="OpenManus MCP Server")
    parser.add_argument(
        "-t", "--transport",
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
            mcp.run(transport="http", host="0.0.0.0", port=9000, path="/mcp")
        else:
            print(f"Error: Unsupported transport protocol '{args.transport}'", file=sys.__stderr__)
            sys.exit(1)

    except KeyboardInterrupt:
        # 使用sys.__stderr__确保总能输出关闭消息
        print("\nServer shutdown requested...", file=sys.__stderr__)
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.__stderr__)
        sys.exit(1)
