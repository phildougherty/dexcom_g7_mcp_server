#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from pydexcom import Dexcom

# Configuration
DEXCOM_USERNAME = os.getenv("DEXCOM_USERNAME", "")
DEXCOM_PASSWORD = os.getenv("DEXCOM_PASSWORD", "") 
DEXCOM_REGION = os.getenv("DEXCOM_REGION", "us")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8007"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dexcom MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Dexcom client
dexcom_client = None
if DEXCOM_USERNAME and DEXCOM_PASSWORD:
    try:
        dexcom_client = Dexcom(
            username=DEXCOM_USERNAME,
            password=DEXCOM_PASSWORD,
            region=DEXCOM_REGION
        )
        logger.info("Dexcom client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Dexcom client: {e}")

def mg_to_mmol(mg_value: float) -> float:
    """Convert mg/dL to mmol/L"""
    return round(mg_value * 0.0555, 2)

@app.post("/")
async def mcp_endpoint(request: dict):
    """Main MCP endpoint"""
    
    method = request.get("method")
    req_id = request.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "dexcom-monitor",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0", 
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "get_current_glucose",
                        "description": "Get current glucose reading from Dexcom G7",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "get_glucose_history",
                        "description": "Get glucose history for specified hours", 
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hours": {
                                    "type": "integer",
                                    "description": "Hours of history (default: 6)",
                                    "default": 6
                                }
                            },
                            "required": []
                        }
                    }
                ]
            }
        }
        
    elif method == "tools/call":
        if not dexcom_client:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": "Dexcom client not initialized"
                }
            }
            
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "get_current_glucose":
                reading = dexcom_client.get_latest_glucose_reading()
                mmol_value = mg_to_mmol(reading.value)
                
                result_text = (
                    f"🩸 Current Glucose: {reading.value} mg/dL ({mmol_value} mmol/L)\n"
                    f"📈 Trend: {reading.trend_description}\n" 
                    f"⏰ Time: {reading.datetime.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": result_text}]
                    }
                }
                
            elif tool_name == "get_glucose_history":
                hours = arguments.get("hours", 6)
                readings = dexcom_client.get_glucose_readings(minutes=hours*60, max_count=20)
                
                if not readings:
                    result_text = f"No glucose readings found for the last {hours} hours."
                else:
                    lines = [f"📊 Last {hours}h glucose readings:"]
                    for i, reading in enumerate(readings[:10]):
                        mmol_value = mg_to_mmol(reading.value)
                        lines.append(
                            f"{i+1}. {reading.datetime.strftime('%Y-%m-%d %H:%M:%S')} - "
                            f"{reading.value} mg/dL ({mmol_value} mmol/L) [{reading.trend_description}]"
                        )
                    result_text = "\n".join(lines)
                
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": result_text}]
                    }
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": f"Error executing tool: {str(e)}"
                }
            }
    
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }

if __name__ == "__main__":
    logger.info(f"Starting Dexcom MCP HTTP server on port {HTTP_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)