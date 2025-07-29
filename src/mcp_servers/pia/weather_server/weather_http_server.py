from typing import Any
from datetime import datetime
import httpx
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP(name="weather")
# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool
async def get_alerts(state: str) -> dict:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    Returns:
        dict: {"status": "success/error", "message": str, "alerts": list}
    """
    try:
        url = f"{NWS_API_BASE}/alerts/active/area/{state}"
        data = await make_nws_request(url)

        if not data or "features" not in data:
            return {
                "status": "error",
                "message": "Unable to fetch alerts or no alerts found.",
            }

        if not data["features"]:
            return {"status": "success", "message": "No active alerts", "alerts": []}

        alerts = [format_alert(feature) for feature in data["features"]]
        return {
            "status": "success",
            "message": f"Found {len(alerts)} alerts",
            "alerts": alerts,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> dict:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    Returns:
        dict: {"status": "success/error", "message": str, "forecast": list}
    """
    try:
        # First get the forecast grid endpoint
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)

        if not points_data:
            return {"status": "error", "message": "Unable to fetch forecast data"}

        # Get the forecast URL from the points response
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)

        if not forecast_data:
            return {"status": "error", "message": "Unable to fetch detailed forecast"}

        # Format the periods into a readable forecast
        periods = forecast_data["properties"]["periods"]
        forecasts = []
        for period in periods[:5]:  # Only show next 5 periods
            forecasts.append(
                {
                    "period": period["name"],
                    "temperature": f"{period['temperature']}°{period['temperatureUnit']}",
                    "wind": f"{period['windSpeed']} {period['windDirection']}",
                    "forecast": period["detailedForecast"],
                }
            )

        return {
            "status": "success",
            "message": f"Found {len(forecasts)} forecast periods",
            "forecast": forecasts,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# @mcp.tool(
#     name="rag_regulatory",
#     description="检索公司内部规章制度信息",
# )
# async def rag_regulatory(
#     query: str,
# ) -> Union[str, Dict]:
#     """检索PIA 公司内部规章制度。
#     Args:
#         query (str):
#     """
#     time.sleep(20)
#     return """
# # 住宿费报销标准 / Accommodation Reimbursement Criteria
# ## 报销限额标准 / Reimbursement Limits

# | 职级 / Position Level          | 中国大陆地区 / Mainland China                                                                 | 中国大陆以外（含港澳台地区） / Outside Mainland China (Including HK, Macau & Taiwan) |
# |-------------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------|
# |                              | 一线/准一线城市及省会 / First Tier/Quasi First Tier & Provincial Capitals                  | 其他城市 / Other Cities                           |
# |-------------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------|
# | 公司中层及以上 / Manager Level | 限额 450 元/人/晚 / 450 RMB per person per night                                           | 限额 500-1,000 元/人/晚 / 500-1,000 RMB          |
# | (经理、主管)                  |                                                                                            |                                                   |
# | 其他员工 / Other Employees    | 限额 300 元/人/晚 / 300 RMB per person per night                                           | 限额 350-800 元/人/晚 / 350-800 RMB              |
# |                               | 其他城市限额 250 元/人/晚 / 250 RMB for Other Cities                                       |                                                   |
# ---

# ## 注释 / Notes

# 1. **城市分类说明 / City Classification**
# - **一线/准一线城市**
# 北京、上海、广州、深圳、天津、南京、武汉、西安、成都、重庆、杭州、青岛、大连、宁波、苏州、长沙
# *Beijing, Shanghai, Guangzhou, Shenzhen, Tianjin, Nanjing, Wuhan, Xi'an, Chengdu, Chongqing, Hangzhou, Qingdao, Dalian, Ningbo, Suzhou, Changsha*

# - **省会级城市**
# 石家庄、沈阳、哈尔滨、杭州、福州、济南、广州、武汉、成都、昆明、兰州、太原、长春、南京、合肥、南昌、郑州、长沙、海口、贵阳、西安、西宁、呼和浩特、乌鲁木齐、银川、南宁、拉萨
# *Shijiazhuang, Shenyang, Harbin, Hangzhou, Fuzhou, Jinan, Guangzhou, Wuhan, Chengdu, Kunming, Lanzhou, Taiyuan, Changchun, Nanjing, Hefei, Nanchang, Zhengzhou, Changsha, Haikou, Guiyang, Xi'an, Xining, Hohhot, Urumqi, Yinchuan, Nanning, Lhasa*

# 2. **特殊岗位说明 / Special Positions**
# 大客户经理、项目经理、方案组组长、事业部设计组组长享受经理级别报销标准
# *Key Account Manager, Project Manager, Concept Team Leader, and BU Design Team Leader enjoy the reimbursement standard at manager level.*"""


if __name__ == "__main__":
    # Initialize and run the server
    settings = {"port": 7777, "host": "0.0.0.0", "path": "/mcp/"}
    mcp.run(transport="http", **settings)
    
