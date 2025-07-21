import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
from sample_data import generate_sample_data
from data_simulation import HospitalDataSimulator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabasePopulator:
    def __init__(self):
        self.init_firebase()
        # Initialize all database references
        self.root_ref = db.reference('/')
        self.rooms_ref = db.reference('/rooms')
        self.beds_ref = db.reference('/beds')
        self.patients_ref = db.reference('/patients')
        self.staff_ref = db.reference('/staff')
        self.iot_ref = db.reference('/iotData')
        self.incidents_ref = db.reference('/incidents')
        self.inventory_ref = db.reference('/inventory')
        self.ai_logs_ref = db.reference('/aiLogs')
        self.metrics_ref = db.reference('/systemMetrics')
        
    def init_firebase(self):
        """Initialize Firebase connection"""
        load_dotenv()
        json_str = os.getenv("FIREBASE_KEY_JSON")
        db_url = os.getenv("FIREBASE_DATABASE_URL")

        if not json_str or not db_url:
            raise ValueError("Missing FIREBASE_KEY_JSON or FIREBASE_DATABASE_URL")

        try:
            json_data = json.loads(json_str)  
            cred = credentials.Certificate(json_data)
            if not firebase_admin._apps:  # Only initialize if not already initialized
                firebase_admin.initialize_app(cred, {
                    'databaseURL': db_url
                })
        except json.JSONDecodeError as e:
            raise ValueError("Invalid FIREBASE_KEY_JSON") from e

    def clear_database(self):
        """Clear all data from the database"""
        try:
            self.root_ref.delete()
            logger.info("Successfully cleared database")
            return True
        except Exception as e:
            logger.error(f"Error clearing database: {str(e)}")
            return False

    def populate_database(self):
        """Populate the database with comprehensive sample data"""
        try:
            # Generate sample data
            data = generate_sample_data()
            
            # Upload all data using existing references
            self.root_ref.update({
                'rooms': data['rooms'],
                'beds': data['beds'],
                'patients': data['patients'],
                'staff': data['staff'],
                'iotData': data['iotData'],
                'incidents': data['incidents'],
                'inventory': data['inventory'],
                'aiLogs': data['aiLogs'],
                'systemMetrics': data['systemMetrics']
            })
            
            logger.info("Successfully populated database with base data")
            return True
            
        except Exception as e:
            logger.error(f"Error populating database: {str(e)}")
            return False

def main():
    """Main function to populate the database"""
    populator = DatabasePopulator()
    
    # First clear the database
    logger.info("Clearing existing database data...")
    if populator.clear_database():
        # Then populate with new data
        logger.info("Populating database with sample data...")
        if populator.populate_database():
            logger.info("Database successfully populated with all sample data")
        else:
            logger.error("Failed to populate database")
    else:
        logger.error("Failed to clear database. Aborting population.")

if __name__ == "__main__":
    main() 