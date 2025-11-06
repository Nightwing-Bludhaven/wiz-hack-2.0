#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import asyncio
from wiz_control import WizLight

app = FastAPI(title="Wiz Light Control API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the web interface"""
    return FileResponse("static/index.html")


class ColorRequest(BaseModel):
    r: int
    g: int
    b: int
    brightness: Optional[int] = 100


class LightResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


async def get_first_light_ip():
    """Helper function to get the first available light's IP"""
    light = WizLight()
    # run the blocking discovery call in a thread and await the result
    lights = await asyncio.get_running_loop().run_in_executor(None, light.discover)
    if not lights:
        raise HTTPException(status_code=404, detail="No lights found on network")
    return lights[0]["ip"]


@app.get("/discover", response_model=LightResponse)
async def discover_lights():
    """Discover all Wiz lights on the network"""
    try:
        light = WizLight()
        lights = light.discover()
        return {
            "success": True,
            "message": "Lights discovered successfully",
            "data": {"lights": lights},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/on", response_model=LightResponse)
async def turn_on_first_light():
    """Turn on the first discovered light"""
    try:
        ip = await get_first_light_ip()
        light = WizLight(ip)
        result = light.set_state(True)
        return {
            "success": True,
            "message": f"Light {ip} turned on successfully",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/off", response_model=LightResponse)
async def turn_off_first_light():
    """Turn off the first discovered light"""
    try:
        ip = await get_first_light_ip()
        light = WizLight(ip)
        result = light.set_state(False)
        return {
            "success": True,
            "message": f"Light {ip} turned off successfully",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/color", response_model=LightResponse)
async def set_first_light_color(color: ColorRequest):
    """Set color of the first discovered light"""
    try:
        ip = await get_first_light_ip()
        light = WizLight(ip)
        result = light.set_color(color.r, color.g, color.b, color.brightness)
        return {
            "success": True,
            "message": f"Color set successfully for light {ip}",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=LightResponse)
async def get_first_light_status():
    """Get status of the first discovered light"""
    try:
        ip = await get_first_light_ip()
        light = WizLight(ip)
        status = light.get_state()
        return {
            "success": True,
            "message": "Status retrieved successfully",
            "data": status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/light/{ip}/status", response_model=LightResponse)
async def get_light_status(ip: str):
    """Get status of a specific light"""
    try:
        light = WizLight(ip)
        status = light.get_state()
        return {
            "success": True,
            "message": "Status retrieved successfully",
            "data": status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light/{ip}/on", response_model=LightResponse)
async def turn_on_light(ip: str):
    """Turn on a specific light"""
    try:
        light = WizLight(ip)
        result = light.set_state(True)
        return {
            "success": True,
            "message": "Light turned on successfully",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light/{ip}/off", response_model=LightResponse)
async def turn_off_light(ip: str):
    """Turn off a specific light"""
    try:
        light = WizLight(ip)
        result = light.set_state(False)
        return {
            "success": True,
            "message": "Light turned off successfully",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light/{ip}/color", response_model=LightResponse)
async def set_light_color(ip: str, color: ColorRequest):
    """Set color and brightness of a specific light"""
    try:
        light = WizLight(ip)
        result = light.set_color(color.r, color.g, color.b, color.brightness)
        return {"success": True, "message": "Color set successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",  # Make accessible from other devices on network
        port=8000,
        reload=True,
    )
