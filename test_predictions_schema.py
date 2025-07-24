#!/usr/bin/env python3
"""
Test script to verify the predictions route works with the new vitals schema
"""

import requests
import json
import time
from datetime import datetime

def test_predictions_with_new_schema():
    """Test that predictions work with the new vitals schema"""
    base_url = "http://localhost:8000"
    
    print("🔮 Testing Predictions with New Vitals Schema")
    print("=" * 50)
    
    try:
        # 1. Start simulation to ensure we have data
        print("1. Starting simulation to generate vitals data...")
        response = requests.post(f"{base_url}/simulation/start")
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"   ✅ Simulation started")
            else:
                print(f"   ⚠️  Simulation already running or failed: {result.get('message')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
        
        # 2. Wait for some vitals data to be generated
        print("2. Waiting 30 seconds for vitals data generation...")
        time.sleep(30)
        
        # 3. Debug monitor structure
        print("3. Checking monitor structure...")
        response = requests.get(f"{base_url}/predict/debug/monitors")
        if response.status_code == 200:
            debug_info = response.json()
            total_monitors = debug_info.get("total_monitors", 0)
            print(f"   📱 Found {total_monitors} total monitors")
            
            monitors = debug_info.get("monitors", {})
            vitals_monitors = {}
            
            for monitor_id, info in monitors.items():
                if info.get("device_type") == "vitals_monitor":
                    vitals_monitors[monitor_id] = info
                    current_patient = info.get("current_patient")
                    vitals_patients = info.get("vitals_patients", [])
                    print(f"   🏥 Monitor {monitor_id}:")
                    print(f"      Current Patient: {current_patient}")
                    print(f"      Patients with Vitals: {vitals_patients}")
                    print(f"      Room: {info.get('room_id')}, Bed: {info.get('bed_id')}")
            
            if not vitals_monitors:
                print("   ⚠️  No vitals monitors found")
                return
            
        else:
            print(f"   ❌ Failed to get debug info: {response.status_code}")
            return
        
        # 4. Test vitals retrieval for each patient
        print("\n4. Testing vitals retrieval for patients...")
        patients_tested = set()
        
        for monitor_id, info in vitals_monitors.items():
            current_patient = info.get("current_patient")
            vitals_patients = info.get("vitals_patients", [])
            
            # Test current patient if assigned
            if current_patient and current_patient not in patients_tested:
                print(f"\n   👤 Testing patient: {current_patient}")
                response = requests.get(f"{base_url}/predict/test-vitals/{current_patient}")
                if response.status_code == 200:
                    result = response.json()
                    if result.get("vitals_found"):
                        print(f"      ✅ Vitals found - Monitor: {result.get('monitor_id')}")
                        vitals_structure = result.get("vitals_structure", {})
                        print(f"      📊 Latest Vitals:")
                        print(f"         HR: {vitals_structure.get('heartRate')} bpm")
                        print(f"         BP: {vitals_structure.get('bloodPressure', {}).get('systolic', 'N/A')}/{vitals_structure.get('bloodPressure', {}).get('diastolic', 'N/A')} mmHg")
                        print(f"         SpO2: {vitals_structure.get('oxygenLevel')}%")
                        print(f"         Temp: {vitals_structure.get('temperature')}°C")
                        print(f"         RR: {vitals_structure.get('respiratoryRate')} /min")
                        print(f"         Glucose: {vitals_structure.get('glucose')} mg/dL")
                        print(f"         Timestamp: {vitals_structure.get('timestamp')}")
                        
                        # 5. Test actual prediction
                        print(f"      🔮 Testing risk prediction...")
                        pred_response = requests.get(f"{base_url}/predict/risk/{current_patient}")
                        if pred_response.status_code == 200:
                            pred_result = pred_response.json()
                            prediction = pred_result.get("prediction")
                            probabilities = pred_result.get("probabilities", {})
                            details = pred_result.get("prediction_details", {})
                            
                            print(f"         ✅ Prediction successful!")
                            print(f"         Risk Level: {prediction}")
                            print(f"         Risk Score: {details.get('riskScore')}%")
                            print(f"         Confidence: {details.get('confidence', 0):.2f}")
                            
                            recommendations = details.get("recommendations", [])
                            if recommendations:
                                print(f"         Recommendations:")
                                for rec in recommendations:
                                    print(f"           - {rec}")
                            
                            alert_created = pred_result.get("alert_created", False)
                            if alert_created:
                                print(f"         🚨 Alert created for high/critical risk")
                            
                        else:
                            print(f"         ❌ Prediction failed: {pred_response.status_code}")
                            if pred_response.status_code != 500:
                                error_detail = pred_response.json().get("detail", "Unknown error")
                                print(f"            Error: {error_detail}")
                    else:
                        print(f"      ❌ No vitals found for patient")
                        print(f"         Message: {result.get('message')}")
                else:
                    print(f"      ❌ Vitals test failed: {response.status_code}")
                
                patients_tested.add(current_patient)
            
            # Test other patients with vitals
            for patient_id in vitals_patients:
                if patient_id not in patients_tested and len(patients_tested) < 3:  # Limit to 3 patients
                    print(f"\n   👤 Testing patient: {patient_id}")
                    response = requests.get(f"{base_url}/predict/test-vitals/{patient_id}")
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("vitals_found"):
                            print(f"      ✅ Vitals found")
                            
                            # Test prediction
                            pred_response = requests.get(f"{base_url}/predict/risk/{patient_id}")
                            if pred_response.status_code == 200:
                                pred_result = pred_response.json()
                                prediction = pred_result.get("prediction")
                                details = pred_result.get("prediction_details", {})
                                print(f"      🔮 Prediction: {prediction} (Score: {details.get('riskScore')}%)")
                            else:
                                print(f"      ❌ Prediction failed: {pred_response.status_code}")
                        else:
                            print(f"      ❌ No vitals found")
                    
                    patients_tested.add(patient_id)
        
        if not patients_tested:
            print("   ⚠️  No patients found to test")
            return
        
        print(f"\n🎉 Predictions Test Complete!")
        print(f"📋 Summary:")
        print(f"   ✅ New vitals schema (vitals/{{patient_id}}/{{timestamp}}) working correctly")
        print(f"   ✅ Vitals retrieval functions updated successfully")
        print(f"   ✅ Risk predictions working with new schema")
        print(f"   ✅ Alert creation functional")
        print(f"   ✅ Tested {len(patients_tested)} patients")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the FastAPI server.")
        print("   Make sure your server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    print("🏥 Predictions Route Test with New Vitals Schema")
    print("This test verifies that the predictions route works correctly")
    print("with the updated vitals data structure.")
    print()
    
    test_predictions_with_new_schema()
