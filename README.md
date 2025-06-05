# Dexcom G7 MCP Server

A Model Context Protocol (MCP) server that provides access to Dexcom G7 continuous glucose monitor data. This server allows AI assistants and other MCP clients to retrieve current glucose readings and historical data from your Dexcom G7 device.

## Features

- **Current Glucose Reading**: Get the latest glucose value with trend information
- **Historical Data**: Retrieve glucose readings for a specified time period
- **Dual Units**: Values provided in both mg/dL and mmol/L
- **HTTP Transport**: Native HTTP/JSON-RPC interface for easy integration
- **MCP Compatible**: Full Model Context Protocol compliance

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t dexcom-mcp .

# Run with your credentials
docker run -p 8007:8007 \
  -e DEXCOM_USERNAME="your-dexcom-username" \
  -e DEXCOM_PASSWORD="your-dexcom-password" \
  -e DEXCOM_REGION="us" \
  dexcom-mcp
```

### Using MCP-Compose

For orchestrated deployment with other MCP servers, use [mcp-compose](https://github.com/phildougherty/mcp-compose):

```yaml
# mcp-compose.yaml
version: '1'
servers:
  dexcom:
    image: dexcom-mcp:local
    runtime: docker
    build:
      context: .
      dockerfile: Dockerfile
    protocol: http
    http_port: 8007
    env:
      HTTP_PORT: "8007"
      DEXCOM_REGION: "us"
      DEXCOM_USERNAME: "your-dexcom-username"
      DEXCOM_PASSWORD: "your-dexcom-password"
    capabilities: [tools]
    networks: [mcp-net]
```

Then start with:
```bash
mcp-compose up dexcom
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEXCOM_USERNAME` | Your Dexcom account username | - | Yes |
| `DEXCOM_PASSWORD` | Your Dexcom account password | - | Yes |
| `DEXCOM_REGION` | Dexcom region (`us` or `ous`) | `us` | No |
| `HTTP_PORT` | HTTP server port | `8007` | No |

**Note**: For users outside the US, set `DEXCOM_REGION=ous` (Outside US).

## Available Tools

### `get_current_glucose`

Retrieves the most recent glucose reading from your Dexcom G7.

**Parameters**: None

**Example Response**:
```
🩸 Current Glucose: 120 mg/dL (6.66 mmol/L)
📈 Trend: Steady
⏰ Time: 2024-01-15 14:30:00
```

### `get_glucose_history`

Retrieves historical glucose readings for a specified time period.

**Parameters**:
- `hours` (integer, optional): Number of hours of history to retrieve (default: 6)

**Example Response**:
```
📊 Last 6h glucose readings:
1. 2024-01-15 14:30:00 - 120 mg/dL (6.66 mmol/L) [Steady]
2. 2024-01-15 14:25:00 - 118 mg/dL (6.55 mmol/L) [Steady]
3. 2024-01-15 14:20:00 - 115 mg/dL (6.39 mmol/L) [Slowly Rising]
...
```

## API Usage

### Initialize Connection

```bash
curl -X POST http://localhost:8007/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'
```

### Get Current Glucose

```bash
curl -X POST http://localhost:8007/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_current_glucose",
      "arguments": {}
    }
  }'
```

### Get Glucose History

```bash
curl -X POST http://localhost:8007/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_glucose_history",
      "arguments": {"hours": 12}
    }
  }'
```

## Client Integration

### Claude Desktop

Add to your Claude Desktop MCP settings:

```json
{
  "servers": [
    {
      "name": "dexcom",
      "httpEndpoint": "http://localhost:8007",
      "capabilities": ["tools"],
      "description": "Dexcom G7 glucose monitor"
    }
  ]
}
```

### OpenWebUI

Use the auto-generated OpenAPI specification at `http://localhost:8007/openapi.json` (when using mcp-compose proxy).

## Architecture

### Transport Protocol

This server uses **HTTP transport** instead of the traditional STDIO transport used by many MCP servers. This provides several advantages:

- Direct HTTP/JSON-RPC communication
- No need for stdio redirection or process management
- Better error handling and connection management
- Native support for web clients and proxies

### Socat Integration (Optional)

The included `entrypoint.sh` provides socat integration for environments that expect STDIO transport. When used with MCP-Compose's socat hosting feature, it bridges between TCP sockets and the server process:

```bash
# The entrypoint wraps the server for STDIO compatibility
socat TCP-LISTEN:12345,reuseaddr,bind=0.0.0.0 EXEC:"python server.py"
```

This allows the HTTP-based server to work with STDIO-expecting orchestrators while maintaining the benefits of HTTP transport.

For more information about socat hosting and orchestration, see the [mcp-compose documentation](https://github.com/phildougherty/mcp-compose).

## Dependencies

- **pydexcom**: For Dexcom API access
- **FastAPI**: HTTP server framework
- **uvicorn**: ASGI server
- **mcp**: Model Context Protocol support

## Requirements

- Python 3.11+
- Valid Dexcom account credentials
- Active Dexcom G7 device with data sharing enabled

## Security Considerations

- Store credentials securely using environment variables
- Consider using Docker secrets for production deployments
- Restrict network access to trusted clients
- Monitor access logs for unauthorized usage

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify your Dexcom username and password are correct
- Ensure you can log into the Dexcom mobile app
- Check that data sharing is enabled in your Dexcom account

**No Recent Data**
- Confirm your G7 sensor is active and transmitting
- Check that your phone/receiver has recent connectivity to Dexcom servers
- Verify the sensor hasn't expired

**Connection Timeouts**
- Dexcom servers occasionally experience delays
- Retry requests after a brief wait
- Check your internet connectivity

### Debug Mode

Enable debug logging by setting the log level:

```bash
docker run -p 8007:8007 \
  -e DEXCOM_USERNAME="your-username" \
  -e DEXCOM_PASSWORD="your-password" \
  -e PYTHONUNBUFFERED=1 \
  dexcom-mcp
```

## Disclaimer

This software is not affiliated with or endorsed by Dexcom, Inc. Use of this software requires valid Dexcom account credentials and is subject to Dexcom's terms of service. This tool is for personal use and should not be used as a substitute for proper medical monitoring and care.
