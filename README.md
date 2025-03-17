# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather information using the Open-Meteo API.

## Features

* Get current weather information for a specified city.

## Installation

This server is designed to be installed manually by adding its configuration to the `cline_mcp_settings.json` file.

1.  Add the following entry to the `mcpServers` object in your `cline_mcp_settings.json` file:

```json
"weather": {
  "command": "python",
  "args": [
    "mcp_weather_server.py"
  ],
  "disabled": false,
  "autoApprove": []
}
```
2.  Make sure to use double backslashes (`\\`) in the file path.
3. Save the `cline_mcp_settings.json` file.

## Configuration

This server does not require an API key. It uses the Open-Meteo API, which is free and open-source.

## Usage

This server provides a single tool: `get_weather`.

### `get_weather`

Retrieves the current weather information for a given city.

**Parameters:**

*   `city` (string, required): The name of the city.

**Example:**

To get the weather in Taipei, you would use the tool like this:

```
<use_mcp_tool>
<server_name>weather</server_name>
<tool_name>get_weather</tool_name>
<arguments>
{
  "city": "Taipei"
}
</arguments>
</use_mcp_tool>
```
## License

MIT License
