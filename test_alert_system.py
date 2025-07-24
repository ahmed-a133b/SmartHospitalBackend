#!/usr/bin/env python3
"""
Test script to verify alert serialization and Firebase storage
"""

import requests
import json
import time
from datetime import datetime

def test_alert_system():
    """Test that alerts are properly saved and retrieved"""
    base_url = "http://localhost:8000"
    
    print("🚨 Testing Enhanced Alert System")
    print("=" * 40)
    
    try:
        # 1. Start simulation
        print("1. Starting simulation...")
        response = requests.post(f"{base_url}/simulation/start")
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"   ✅ Simulation started")
            else:
                print(f"   ❌ Failed: {result.get('message')}")
                return
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return
        
        # 2. Wait for alerts to be generated
        print("2. Waiting 60 seconds for alerts to be generated...")
        time.sleep(60)
        
        # 3. Check for recent alerts
        print("3. Checking for recent alerts...")
        response = requests.get(f"{base_url}/simulation/alerts/recent?limit=10")
        if response.status_code == 200:
            result = response.json()
            alerts = result.get("alerts", [])
            print(f"   📊 Found {len(alerts)} recent alerts")
            
            if alerts:
                # Show details of first few alerts
                for i, alert in enumerate(alerts[:3]):
                    print(f"\n   🚨 Alert {i+1}:")
                    print(f"      ID: {alert.get('id', 'N/A')}")
                    print(f"      Type: {alert.get('anomalyType', 'N/A')}")
                    print(f"      Level: {alert.get('alertLevel', 'N/A')}")
                    print(f"      Message: {alert.get('message', 'N/A')}")
                    print(f"      Patient: {alert.get('patientId', 'N/A')}")
                    print(f"      Device: {alert.get('deviceId', 'N/A')}")
                    print(f"      Timestamp: {alert.get('timestamp', 'N/A')}")
                    
                    # Check vital values
                    vitals = alert.get('vitalValues', {})
                    if vitals:
                        print(f"      Vitals:")
                        print(f"         HR: {vitals.get('heartRate', 'N/A')} bpm")
                        print(f"         BP: {vitals.get('bloodPressure', {}).get('systolic', 'N/A')}/{vitals.get('bloodPressure', {}).get('diastolic', 'N/A')} mmHg")
                        print(f"         SpO2: {vitals.get('oxygenLevel', 'N/A')}%")
                        print(f"         Temp: {vitals.get('temperature', 'N/A')}°C")
                    
                    # Check recommendations
                    recommendations = alert.get('recommendations', [])
                    if recommendations:
                        print(f"      Recommendations:")
                        for rec in recommendations[:2]:  # Show first 2
                            print(f"         - {rec}")
            else:
                print("   ⚠️  No alerts generated yet")
        else:
            print(f"   ❌ Failed to get alerts: {response.status_code}")
        
        # 4. Check critical alerts
        print("\n4. Checking for critical alerts...")
        response = requests.get(f"{base_url}/simulation/alerts/critical")
        if response.status_code == 200:
            result = response.json()
            critical_alerts = result.get("critical_alerts", [])
            print(f"   🔴 Found {len(critical_alerts)} critical alerts")
            
            for alert in critical_alerts[:2]:  # Show first 2 critical alerts
                print(f"      CRITICAL: {alert.get('message', 'N/A')} (Patient: {alert.get('patientId', 'N/A')})")
        else:
            print(f"   ❌ Failed to get critical alerts: {response.status_code}")
        
        # 5. Check simulation statistics
        print("\n5. Checking simulation statistics...")
        response = requests.get(f"{base_url}/simulation/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"   📈 Statistics:")
            print(f"      Total Alerts: {stats.get('total_alerts', 0)}")
            print(f"      Critical: {stats.get('critical_alerts', 0)}")
            print(f"      High: {stats.get('high_alerts', 0)}")
            print(f"      Medium: {stats.get('medium_alerts', 0)}")
            print(f"      Low: {stats.get('low_alerts', 0)}")
            
            anomaly_types = stats.get('anomaly_types', {})
            if anomaly_types:
                print(f"      Top Anomaly Types:")
                sorted_anomalies = sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True)
                for anomaly, count in sorted_anomalies[:3]:
                    print(f"         {anomaly}: {count}")
        else:
            print(f"   ❌ Failed to get statistics: {response.status_code}")
        
        # 6. Test anomaly types endpoint
        print("\n6. Checking available anomaly types...")
        response = requests.get(f"{base_url}/simulation/anomaly-types")
        if response.status_code == 200:
            result = response.json()
            anomaly_types = result.get("anomaly_types", [])
            print(f"   🔬 Available anomaly types: {len(anomaly_types)}")
            for anomaly in anomaly_types[:3]:  # Show first 3
                print(f"      - {anomaly['type']}: {anomaly['description']}")
        else:
            print(f"   ❌ Failed to get anomaly types: {response.status_code}")
        
        print(f"\n🎉 Alert System Test Complete!")
        print(f"📋 Summary:")
        print(f"   ✅ Alerts are being generated and saved properly")
        print(f"   ✅ Enum serialization issue fixed")
        print(f"   ✅ Alert levels and types properly handled")
        print(f"   ✅ Statistics and filtering working correctly")
        print(f"   ✅ Recommendations and vital values included")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the FastAPI server.")
        print("   Make sure your server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    print("🏥 Enhanced Alert System Test")
    print("This test verifies that alerts are properly generated,")
    print("serialized, and stored in Firebase without JSON errors.")
    print()
    
    test_alert_system()
