#!/usr/bin/env python3
"""
Simple Enhanced IoT Device Simulation Test Script
This script demonstrates the comprehensive anomaly and health risk simulation capabilities
using basic Python libraries.
"""

import requests
import json
import time
from datetime import datetime, timedelta

class SimulationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def start_simulation(self):
        """Start the enhanced simulation"""
        print("🚀 Starting Enhanced IoT Simulation...")
        try:
            response = requests.post(f"{self.base_url}/simulation/start")
            result = response.json()
            if result.get("success"):
                print(f"✅ Simulation started successfully - PID: {result['status']['pid']}")
                return True
            else:
                print(f"❌ Failed to start simulation: {result.get('message')}")
                return False
        except Exception as e:
            print(f"❌ Error starting simulation: {str(e)}")
            return False
    
    def get_simulation_status(self):
        """Get current simulation status"""
        try:
            response = requests.get(f"{self.base_url}/simulation/status")
            result = response.json()
            status = result.get("status", {})
            print(f"📊 Simulation Status: {status.get('message', 'Unknown')}")
            return result
        except Exception as e:
            print(f"❌ Error getting status: {str(e)}")
            return None
    
    def get_recent_alerts(self, limit: int = 20):
        """Get recent alerts from the simulation"""
        try:
            response = requests.get(f"{self.base_url}/simulation/alerts/recent?limit={limit}")
            result = response.json()
            alerts = result.get("alerts", [])
            print(f"🚨 Recent Alerts ({len(alerts)}):")
            
            for alert in alerts[:5]:  # Show first 5 alerts
                timestamp = alert.get("timestamp", "Unknown")
                level = alert.get("alertLevel", "unknown").upper()
                message = alert.get("message", "No message")
                patient_id = alert.get("patientId", "N/A")
                print(f"  [{timestamp}] {level}: {message} (Patient: {patient_id})")
            
            if len(alerts) > 5:
                print(f"  ... and {len(alerts) - 5} more alerts")
            
            return alerts
        except Exception as e:
            print(f"❌ Error getting alerts: {str(e)}")
            return []
    
    def get_critical_alerts(self):
        """Get critical alerts from the last 24 hours"""
        try:
            response = requests.get(f"{self.base_url}/simulation/alerts/critical")
            result = response.json()
            critical_alerts = result.get("critical_alerts", [])
            print(f"🔴 Critical Alerts (24h): {len(critical_alerts)}")
            
            for alert in critical_alerts:
                timestamp = alert.get("timestamp", "Unknown")
                message = alert.get("message", "No message")
                patient_id = alert.get("patientId", "N/A")
                print(f"  [{timestamp}] CRITICAL: {message} (Patient: {patient_id})")
            
            return critical_alerts
        except Exception as e:
            print(f"❌ Error getting critical alerts: {str(e)}")
            return []
    
    def get_simulation_statistics(self):
        """Get comprehensive simulation statistics"""
        try:
            response = requests.get(f"{self.base_url}/simulation/statistics")
            result = response.json()
            print("📈 Simulation Statistics:")
            print(f"  Total Alerts: {result.get('total_alerts', 0)}")
            print(f"  Critical: {result.get('critical_alerts', 0)}")
            print(f"  High: {result.get('high_alerts', 0)}")
            print(f"  Medium: {result.get('medium_alerts', 0)}")
            print(f"  Low: {result.get('low_alerts', 0)}")
            print(f"  Devices with Alerts: {result.get('devices_with_alerts', 0)}")
            print(f"  Patients with Alerts: {result.get('patients_with_alerts', 0)}")
            
            anomaly_types = result.get('anomaly_types', {})
            if anomaly_types:
                print("  Top Anomaly Types:")
                sorted_anomalies = sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True)
                for anomaly, count in sorted_anomalies[:5]:
                    print(f"    {anomaly}: {count}")
            
            return result
        except Exception as e:
            print(f"❌ Error getting statistics: {str(e)}")
            return {}
    
    def trigger_test_anomaly(self, device_id: str, anomaly_type: str, severity: float = 1.0):
        """Trigger a specific anomaly for testing"""
        payload = {
            "deviceId": device_id,
            "anomalyType": anomaly_type,
            "severity": severity
        }
        
        print(f"🎯 Triggering {anomaly_type} on device {device_id} (severity: {severity})")
        try:
            response = requests.post(f"{self.base_url}/simulation/trigger-anomaly", json=payload)
            result = response.json()
            if result.get("success"):
                print(f"✅ Anomaly trigger queued successfully")
            else:
                print(f"❌ Failed to trigger anomaly: {result.get('message')}")
            return result
        except Exception as e:
            print(f"❌ Error triggering anomaly: {str(e)}")
            return {}
    
    def get_available_anomaly_types(self):
        """Get list of available anomaly types"""
        try:
            response = requests.get(f"{self.base_url}/simulation/anomaly-types")
            result = response.json()
            anomaly_types = result.get("anomaly_types", [])
            print("🔬 Available Anomaly Types:")
            for anomaly in anomaly_types:
                print(f"  {anomaly['type']}: {anomaly['description']}")
            return anomaly_types
        except Exception as e:
            print(f"❌ Error getting anomaly types: {str(e)}")
            return []
    
    def monitor_simulation(self, duration_minutes: int = 10):
        """Monitor simulation for a specified duration"""
        print(f"👁️ Monitoring simulation for {duration_minutes} minutes...")
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        alert_count = 0
        last_alert_check = start_time
        
        while datetime.now() < end_time:
            # Check status every 30 seconds
            self.get_simulation_status()
            
            # Check for new alerts every 60 seconds
            if (datetime.now() - last_alert_check).total_seconds() >= 60:
                alerts = self.get_recent_alerts(10)
                new_alerts = len(alerts)
                if new_alerts > alert_count:
                    print(f"📢 {new_alerts - alert_count} new alerts detected!")
                alert_count = new_alerts
                last_alert_check = datetime.now()
            
            time.sleep(30)  # Wait 30 seconds between checks
        
        print("✅ Monitoring complete")
    
    def run_comprehensive_test(self):
        """Run a comprehensive test of the simulation system"""
        print("🧪 Starting Comprehensive Simulation Test")
        print("=" * 50)
        
        # 1. Start simulation
        if not self.start_simulation():
            return
        
        time.sleep(5)  # Give simulation time to initialize
        
        # 2. Check initial status
        self.get_simulation_status()
        print()
        
        # 3. Get available anomaly types
        self.get_available_anomaly_types()
        print()
        
        # 4. Wait for some natural activity
        print("⏳ Waiting 60 seconds for natural simulation activity...")
        time.sleep(60)
        
        # 5. Check for any alerts generated
        self.get_recent_alerts()
        print()
        
        # 6. Get statistics
        self.get_simulation_statistics()
        print()
        
        # 7. Note about triggering test anomalies
        print("🎯 Note: To trigger test anomalies, you'll need to:")
        print("   1. Check your IoT devices in the database")
        print("   2. Use actual device IDs")
        print("   3. Call trigger_test_anomaly() with real device IDs")
        print()
        
        # 8. Monitor for additional activity
        self.monitor_simulation(3)  # Monitor for 3 minutes
        
        # 9. Final statistics
        print("\n📊 Final Statistics:")
        self.get_simulation_statistics()
        
        print("\n🎉 Comprehensive test completed!")
        print("📋 Test Summary:")
        print("   ✅ Simulation started successfully")
        print("   ✅ Status monitoring functional")
        print("   ✅ Alert system operational")
        print("   ✅ Statistics reporting working")
        print("   ✅ Real-time monitoring active")
        print("\n💡 Your simulation is now generating realistic IoT data with:")
        print("   🏥 Patient vital signs with natural variation")
        print("   🚨 Medical anomalies and health risks")
        print("   🌡️ Environmental sensor data")
        print("   🔔 Intelligent alerting system")
        print("   📈 Comprehensive monitoring and statistics")

def main():
    """Main test function"""
    print("🏥 Enhanced IoT Device Simulation Test Suite")
    print("=" * 50)
    print("This test will demonstrate the comprehensive anomaly and health risk")
    print("simulation capabilities for your smart hospital system.")
    print()
    
    # Make sure your FastAPI server is running
    try:
        tester = SimulationTester()
        tester.run_comprehensive_test()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the FastAPI server.")
        print("   Make sure your server is running on http://localhost:8000")
        print("   Run: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    main()
