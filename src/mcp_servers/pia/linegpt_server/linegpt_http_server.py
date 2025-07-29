import argparse
import json
import sys
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from fastmcp import FastMCP
from openai import OpenAI
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
def login_tool(name: str = "nesinext", password: str = "Ne$!next") -> Union[str, Dict]:
    """Modified tool version with framework-compatible parameters"""
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
    name="producedPartHistory",
    description="""Get produced part history by line ID with time range and frame span. \n Args:
        startTime/endTime:
        lineId：产线ID，如果用户未提供，默认lineId=34498e03-ffca-4b01-9799-c8e533c0604e
        frameSpan: 该字段表示API响应中各个时间段的时间跨度，可取值为[1,2,3,4],分别对应[10分钟，一小时，一天，一个月]
        authorization: 通过PIA IAS APP login得到的Token""",
)
def get_produced_part_history_tool(
    authorization: str,
    startTime: str,
    endTime: str,
    frameSpan: int,
    lineId: str = "34498e03-ffca-4b01-9799-c8e533c0604e",  # 带默认值的可选参数
) -> Dict:
    # 从上下文中获取授权信息
    authorization = authorization

    # 参数验证
    if frameSpan not in [1, 2, 3, 4]:
        return {
            "error_type": "invalid_parameter",
            "message": "frameSpan must be 1(10min), 2(1h), 3(1d) or 4(1month)",
            "details": {"allowed_values": [1, 2, 3, 4]},
        }

    # 时间处理逻辑（保持原有实现）
    try:
        from datetime import datetime

        if frameSpan == 3:
            start_dt = datetime.strptime(startTime.split("T")[0], "%Y-%m-%d")
            end_dt = datetime.strptime(endTime.split("T")[0], "%Y-%m-%d")
            params = {
                "lineId": lineId,
                "startTime": f"{start_dt.strftime('%Y-%m-%d')}T16:00:00.000Z",
                "endTime": f"{end_dt.strftime('%Y-%m-%d')}T16:00:00.000Z",
                "frameSpan": frameSpan,
            }
        else:
            params = {
                "lineId": lineId,
                "startTime": f"{startTime}.000Z",
                "endTime": f"{endTime}.000Z",
                "frameSpan": frameSpan,
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
    name="shift_comparison",
    description="""Compare OEE values of day shift or night shift with time. Attention: If you want campare day shify and night shify, you need request twice.
    \n Args:
    startTime/endTime: 格式YYYY-MM-DDTHH:MM:SS.000Z（白班：当天04:00:00-12:00:00;夜班：当天12:00:00-20:00:00）
    lineId：产线ID，如果用户未提供，默认lineId=34498e03-ffca-4b01-9799-c8e533c0604e
    authorization: 通过PIA IAS APP login得到的Token
    """,
)
def shift_comparison(
    line_id: str, start_Time: str, end_Time: str, authorization: str
) -> Union[Dict, str]:
    """获取指定产线和时间段的OEE数据"""
    api_url = "https://pia-ias-demo.piagroup.com/app/oeeService/OeeServer/GetOeeValue"

    # 配置请求参数和头部
    params = {"lineId": line_id, "startDate": start_Time, "endDate": end_Time}

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
                station_id = entry["stationId"]
                # 保留最新状态信息
                if (
                    station_id not in device_status
                    or entry["timestamp"]
                    > device_status[station_id]["latest_timestamp"]
                ):
                    device_status[station_id] = {
                        "line_name": entry["lineName"],
                        "group_name": entry["groupName"],
                        "station_name": entry["stationName"],
                        "latest_message": entry["text"],
                        "latest_timestamp": entry["timestamp"],
                        "error_count": device_status.get(station_id, {}).get(
                            "error_count", 0
                        )
                        + 1,
                        "message_codes": list(
                            set(
                                device_status.get(station_id, {}).get(
                                    "message_codes", []
                                )
                                + [entry["messageId"]]
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
            "message": f"响应数据缺少必要字段: {str(e)}",
            "details": {"sample_structure": raw_data[0] if raw_data else "无数据"},
        }


@mcp.tool(
    name="analyze_production_line_performance",
    description="""
    产线性能分析及优化建议方法

    参数：
    line_id - 产线ID
    token - 认证令牌

    返回：
    llm_response - LLM的优化建议
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
    分析及优化建议
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
    
    # 安全构建数据摘要
    def safe_get_message_summary(m):
        try:
            return {
                'station': m['stations'][0] if m.get('stations') else '未知工站',
                '故障': m.get('messageText', '无描述'),
                '次数': m.get('count', 0),
                '总时长(秒)': m.get('duration', 0)
            }
        except Exception:
            return None
            
    def safe_get_process_summary(item):
        try:
            item1 = item.get('item1', {})
            median = item1.get('median', 0)
            nominal = item1.get('nominalCycleTime', 1)  # 避免除以0
            return {
                '工站': item1.get('name', '未知工站'),
                '实际中位时间': median,
                '标称时间': nominal,
                '差异(%)': round((median/nominal-1)*100, 1) if nominal else 0
            }
        except Exception:
            return None
    
    # 过滤无效数据并排序
    valid_messages = [m for m in map(safe_get_message_summary, messages_data) if m]
    valid_processes = [p for p in map(safe_get_process_summary, process_data) if p]
    
    # 按影响时长排序异常事件
    valid_messages.sort(key=lambda x: x['总时长(秒)'], reverse=True)
    
    # 构建分析提示词
    prompt = f"""请从技术可用率和节拍时间两个维度分析产线产能瓶颈，回答需简洁：
注意：{{
1. **检查报警信息是否指向设备硬件/软件故障，即分析停机原因是否直接与设备自身故障相关。**
- 技术性停机：报警代码直接关联设备部件（如`电机过载 E01`）。
- 非技术性停机：报警描述为工艺参数超限（如`力/扭矩超限`）。
2. **节拍时间需对比实际值与标称值（nominalCycleTime）。**
}}
相关数据摘要：
1. 异常事件（按影响时长排序）：
{json.dumps(valid_messages[:10], ensure_ascii=False)}

2. 工站节拍数据（对比实际中位数与标称值）：
{json.dumps(valid_processes, ensure_ascii=False)}
"""

    # 调用DeepSeek官方接口
    def call_llm(prompt):
        client = OpenAI(
            api_key="sk-79c0ef347bf641feb2c8c210964332bd",
            base_url="https://api.deepseek.com",
        )

        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # 控制生成稳定性
            )
            return {"data": response.choices[0].message.content}
        except Exception as e:
            print(f"LLM调用失败: {str(e)}")
            return {"data": "无法获取优化建议"}

    return json.dumps(
        {
            "llm_response": call_llm(prompt),
            "data_summary": {
                "messages_data": (
                    [
                        {
                            "station": m["stations"][0],
                            "故障次数": m["count"],
                            "总停机时间(秒)": m["duration"],
                            "最近故障": m["messageText"],
                        }
                        for m in messages_data
                    ]
                    if messages_data
                    else []
                ),
                "process_data": (
                    [
                        {
                            "工站": item["item1"]["name"],
                            "实际中位时间": item["item1"]["median"],
                            "标称时间": item["item1"]["nominalCycleTime"],
                            "差异百分比": f"{round((item['item1']['median']/item['item1']['nominalCycleTime']-1)*100,1)}%",
                        }
                        for item in process_data
                    ]
                    if process_data
                    else []
                ),
            },
        },
        ensure_ascii=False,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="OpenManus MCP Server")
    parser.add_argument(
        "--transport",
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
            print(f"Error: Unsupported transport protocol '{args.transport}'")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nServer shutdown requested...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        sys.exit(1)
