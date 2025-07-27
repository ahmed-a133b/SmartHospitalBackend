from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
import subprocess
import os
import signal
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

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
        
        # Start the simulation process with environment variables
        env = os.environ.copy()  # Copy current environment variables
        simulation_process = subprocess.Popen(
            ["python", script_path],
            cwd=current_dir,
            env=env,  # Pass environment variables
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
            # Process has ended, get final output
            try:
                stdout, stderr = simulation_process.communicate(timeout=1)
                return {
                    "logs": f"Process ended.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}",
                    "running": False,
                    "return_code": simulation_process.returncode
                }
            except subprocess.TimeoutExpired:
                return {"logs": "Process ended but unable to get output", "running": False}
        
        # Process is still running, try to get current output
        try:
            # This won't work for real-time output, but we can check if the process is responsive
            return {
                "logs": f"Simulation is running with PID {simulation_process.pid}. Check server logs for detailed output.",
                "running": True,
                "pid": simulation_process.pid
            }
        except Exception as e:
            return {
                "logs": f"Error checking process: {str(e)}",
                "running": False
            }
        
    except Exception as e:
        logger.error(f"Error getting simulation logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.get("/alerts/recent")
async def get_recent_alerts(limit: int = Query(default=50, ge=1, le=200)):
    """Get recent alerts generated by the simulation"""
    try:
        from firebase_admin import db
        
        alerts_ref = db.reference('alerts')
        alerts_data = alerts_ref.order_by_child('timestamp').limit_to_last(limit).get()
        
        if not alerts_data:
            return {"alerts": [], "count": 0}
        
        # Convert to list and sort by timestamp (newest first)
        alerts_list = []
        for alert_id, alert_data in alerts_data.items():
            alert_data['id'] = alert_id
            alerts_list.append(alert_data)
        
        alerts_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            "alerts": alerts_list,
            "count": len(alerts_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.get("/alerts/critical")
async def get_critical_alerts():
    """Get all critical alerts from the last 24 hours"""
    try:
        from firebase_admin import db
        
        # Calculate 24 hours ago timestamp
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        cutoff_timestamp = twenty_four_hours_ago.strftime("%Y-%m-%d_%H-%M-%S")
        
        alerts_ref = db.reference('alerts')
        alerts_data = alerts_ref.order_by_child('timestamp').start_at(cutoff_timestamp).get()
        
        if not alerts_data:
            return {"critical_alerts": [], "count": 0}
        
        # Filter for critical alerts
        critical_alerts = []
        for alert_id, alert_data in alerts_data.items():
            if alert_data.get('alertLevel') == 'critical':
                alert_data['id'] = alert_id
                critical_alerts.append(alert_data)
        
        # Sort by timestamp (newest first)
        critical_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            "critical_alerts": critical_alerts,
            "count": len(critical_alerts)
        }
        
    except Exception as e:
        logger.error(f"Error getting critical alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get critical alerts: {str(e)}")

@router.get("/statistics")
async def get_simulation_statistics():
    """Get simulation statistics and metrics"""
    try:
        from firebase_admin import db
        
        # Get recent alerts for statistics
        alerts_ref = db.reference('alerts')
        alerts_data = alerts_ref.order_by_child('timestamp').limit_to_last(100).get()
        
        stats = {
            "total_alerts": 0,
            "critical_alerts": 0,
            "high_alerts": 0,
            "medium_alerts": 0,
            "low_alerts": 0,
            "anomaly_types": {},
            "devices_with_alerts": set(),
            "patients_with_alerts": set()
        }
        
        if alerts_data:
            for alert_id, alert_data in alerts_data.items():
                stats["total_alerts"] += 1
                
                # Count by alert level
                alert_level = alert_data.get('alertLevel', 'unknown')
                # Handle both enum objects and string values
                if hasattr(alert_level, 'value'):
                    alert_level = alert_level.value
                    
                if alert_level == 'critical':
                    stats["critical_alerts"] += 1
                elif alert_level == 'high':
                    stats["high_alerts"] += 1
                elif alert_level == 'medium':
                    stats["medium_alerts"] += 1
                elif alert_level == 'low':
                    stats["low_alerts"] += 1
                
                # Count by anomaly type
                anomaly_type = alert_data.get('anomalyType', 'unknown')
                # Handle both enum objects and string values
                if hasattr(anomaly_type, 'value'):
                    anomaly_type = anomaly_type.value
                stats["anomaly_types"][anomaly_type] = stats["anomaly_types"].get(anomaly_type, 0) + 1
                
                # Track devices and patients
                device_id = alert_data.get('deviceId')
                patient_id = alert_data.get('patientId')
                
                if device_id:
                    stats["devices_with_alerts"].add(device_id)
                if patient_id and patient_id != "N/A":
                    stats["patients_with_alerts"].add(patient_id)
        
        # Convert sets to counts
        stats["devices_with_alerts"] = len(stats["devices_with_alerts"])
        stats["patients_with_alerts"] = len(stats["patients_with_alerts"])
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting simulation statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

class TriggerAnomalyRequest(BaseModel):
    deviceId: str
    anomalyType: str
    severity: Optional[float] = 1.0

@router.post("/trigger-anomaly")
async def trigger_specific_anomaly(request: TriggerAnomalyRequest):
    """Manually trigger a specific anomaly for testing purposes"""
    try:
        # This would be implemented by writing a trigger to a Firebase location
        # that the simulation script monitors
        from firebase_admin import db
        
        trigger_ref = db.reference('simulation_triggers')
        trigger_data = {
            'deviceId': request.deviceId,
            'anomalyType': request.anomalyType,
            'severity': request.severity,
            'timestamp': datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            'processed': False
        }
        
        trigger_ref.push(trigger_data)
        
        return {
            "success": True,
            "message": f"Anomaly trigger queued for device {request.deviceId}",
            "trigger": trigger_data
        }
        
    except Exception as e:
        logger.error(f"Error triggering anomaly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger anomaly: {str(e)}")

@router.get("/anomaly-types")
async def get_available_anomaly_types():
    """Get list of available anomaly types for testing"""
    return {
        "anomaly_types": [
            {"type": "cardiac_arrhythmia", "description": "Irregular heart rhythm"},
            {"type": "hypertensive_crisis", "description": "Dangerously high blood pressure"},
            {"type": "hypotensive_shock", "description": "Dangerously low blood pressure"},
            {"type": "respiratory_distress", "description": "Difficulty breathing"},
            {"type": "hypoxemia", "description": "Low blood oxygen levels"},
            {"type": "fever_spike", "description": "High fever"},
            {"type": "hypothermia", "description": "Low body temperature"},
            {"type": "hyperglycemia", "description": "High blood sugar"},
            {"type": "hypoglycemia", "description": "Low blood sugar"},
            {"type": "tachycardia", "description": "Fast heart rate"},
            {"type": "bradycardia", "description": "Slow heart rate"}
        ]
    }
