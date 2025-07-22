from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import subprocess
import os
import signal
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Global variable to track the simulation process
simulation_process = None

class SimulationStatus(BaseModel):
    running: bool
    pid: int | None = None
    message: str

class SimulationResponse(BaseModel):
    success: bool
    message: str
    status: SimulationStatus

@router.get("/status", response_model=SimulationResponse)
async def get_simulation_status():
    """Get the current status of the data simulation"""
    global simulation_process
    
    try:
        if simulation_process is None:
            return SimulationResponse(
                success=True,
                message="Simulation not started",
                status=SimulationStatus(running=False, message="Simulation is not running")
            )
        
        # Check if process is still running
        if simulation_process.poll() is None:
            return SimulationResponse(
                success=True,
                message="Simulation is running",
                status=SimulationStatus(
                    running=True, 
                    pid=simulation_process.pid,
                    message=f"Simulation is running with PID {simulation_process.pid}"
                )
            )
        else:
            # Process has ended
            simulation_process = None
            return SimulationResponse(
                success=True,
                message="Simulation has stopped",
                status=SimulationStatus(running=False, message="Simulation has stopped")
            )
            
    except Exception as e:
        logger.error(f"Error checking simulation status: {str(e)}")
        return SimulationResponse(
            success=False,
            message=f"Error checking status: {str(e)}",
            status=SimulationStatus(running=False, message="Error checking status")
        )

@router.post("/start", response_model=SimulationResponse)
async def start_simulation(background_tasks: BackgroundTasks):
    """Start the data simulation script"""
    global simulation_process
    
    try:
        # Check if simulation is already running
        if simulation_process is not None and simulation_process.poll() is None:
            return SimulationResponse(
                success=False,
                message="Simulation is already running",
                status=SimulationStatus(
                    running=True, 
                    pid=simulation_process.pid,
                    message=f"Simulation is already running with PID {simulation_process.pid}"
                )
            )
        
        # Get the path to the simulation script
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(current_dir, "data_simulation.py")
        
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Simulation script not found at {script_path}"
            )
        
        # Start the simulation process
        simulation_process = subprocess.Popen(
            ["python", script_path],
            cwd=current_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Started simulation with PID {simulation_process.pid}")
        
        return SimulationResponse(
            success=True,
            message="Simulation started successfully",
            status=SimulationStatus(
                running=True,
                pid=simulation_process.pid,
                message=f"Simulation started with PID {simulation_process.pid}"
            )
        )
        
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")

@router.post("/stop", response_model=SimulationResponse)
async def stop_simulation():
    """Stop the data simulation script"""
    global simulation_process
    
    try:
        if simulation_process is None:
            return SimulationResponse(
                success=True,
                message="Simulation is not running",
                status=SimulationStatus(running=False, message="Simulation is not running")
            )
        
        # Check if process is still running
        if simulation_process.poll() is not None:
            simulation_process = None
            return SimulationResponse(
                success=True,
                message="Simulation was already stopped",
                status=SimulationStatus(running=False, message="Simulation was already stopped")
            )
        
        # Try to terminate gracefully first
        try:
            simulation_process.terminate()
            simulation_process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
        except subprocess.TimeoutExpired:
            # If graceful shutdown fails, force kill
            simulation_process.kill()
            simulation_process.wait()
        
        logger.info(f"Stopped simulation with PID {simulation_process.pid}")
        simulation_process = None
        
        return SimulationResponse(
            success=True,
            message="Simulation stopped successfully",
            status=SimulationStatus(running=False, message="Simulation stopped successfully")
        )
        
    except Exception as e:
        logger.error(f"Error stopping simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop simulation: {str(e)}")

@router.post("/restart", response_model=SimulationResponse)
async def restart_simulation(background_tasks: BackgroundTasks):
    """Restart the data simulation script"""
    try:
        # Stop the current simulation if running
        stop_response = await stop_simulation()
        if not stop_response.success:
            return stop_response
        
        # Start a new simulation
        start_response = await start_simulation(background_tasks)
        
        if start_response.success:
            return SimulationResponse(
                success=True,
                message="Simulation restarted successfully",
                status=start_response.status
            )
        else:
            return start_response
            
    except Exception as e:
        logger.error(f"Error restarting simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restart simulation: {str(e)}")

@router.get("/logs")
async def get_simulation_logs():
    """Get the recent logs from the simulation process"""
    global simulation_process
    
    try:
        if simulation_process is None:
            return {"logs": "No simulation process running", "running": False}
        
        if simulation_process.poll() is not None:
            return {"logs": "Simulation process has stopped", "running": False}
        
        # This is a simplified version - in production, you might want to
        # implement proper log file handling or use a logging service
        return {
            "logs": "Simulation is running. Check server logs for detailed output.",
            "running": True,
            "pid": simulation_process.pid
        }
        
    except Exception as e:
        logger.error(f"Error getting simulation logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")
