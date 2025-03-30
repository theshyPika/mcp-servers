import httpx
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from mcp.server import Server
import uvicorn

# Create an MCP server
mcp = FastMCP("Weather")

# Add a weather tool
@mcp.tool()
async def get_weather(city: str) -> str:
    """Get weather information for a city

    Dependencies:
        httpx
    """
    async with httpx.AsyncClient() as client:
        # Get coordinates using the Geocoding API
        geo_response = await client.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
        )
        if geo_response.status_code != 200 or "results" not in geo_response.json():
            return f"Error: Could not retrieve coordinates for {city}."

        geo_data = geo_response.json()["results"][0]
        latitude = geo_data["latitude"]
        longitude = geo_data["longitude"]

        # Get weather data using the Forecast API
        weather_response = await client.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,weather_code&timezone=auto"
        )
        if weather_response.status_code != 200:
            return f"Error: Could not retrieve weather information for {city}."

        weather_data = weather_response.json()
        current_hour = weather_data["hourly"]["time"].index(max(weather_data["hourly"]["time"]))
        temperature = weather_data["hourly"]["temperature_2m"][current_hour]
        weather_code = weather_data["hourly"]["weather_code"][current_hour]

        # Weather code descriptions (from Open-Meteo documentation)
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        description = weather_descriptions.get(weather_code, "Unknown weather code")

        return f"The weather in {city} is {description} with a temperature of {temperature}°C."

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provied mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

def main():
    mcp_server = mcp._mcp_server
    import argparse

    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
