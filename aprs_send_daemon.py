# coding: utf-8
# aprs_send_daemon.py by N1k0droid\\IT9KVB update 14.08.25
import time
import os
import signal
import sys
import json
import logging

# Import functions from aprs_send.py
sys.path.append('/app')
from aprs_send import send_aprs_packet, read_config

class APRSDaemon:
    def __init__(self):
        self.running = True
        # Signal handlers for clean shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("APRS Daemon initialized")
    
    def signal_handler(self, signum, frame):
        print(f"Received shutdown signal {signum}")
        self.running = False
    
    def initialize_system(self):
        """Initialize system on first startup"""
        print("Initializing APRS Weather Station...")
        
        try:
            # Check / create configuration
            cfg = read_config()
            print(f"Configuration ready for {cfg['callsign']}-{cfg['ssid']}")
            
            # Check for weather data file (optional)
            meteo_file = "/config/meteo.json"
            if os.path.exists(meteo_file):
                print("Weather data file found")
            else:
                print("Weather data file not found (will be created when data arrives)")
            
            print("System initialization completed successfully")
            
        except Exception as e:
            print(f"System initialization failed: {e}")
            raise
    
    def run(self):
        # Initialize system on first run
        self.initialize_system()
        
        # Read runtime settings from environment variables with defaults
        enabled = os.getenv('APRS_AUTO_ENABLED', 'off').lower()
        interval = int(os.getenv('APRS_UPDATE_INTERVAL', '3600'))
        debug = os.getenv('APRS_DEBUG', 'yes').lower() == 'yes'
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            print("DEBUG mode enabled via environment variable")
        else:
            logging.basicConfig(level=logging.INFO)
        
        print(f"APRS Daemon starting:")
        print(f"  - Enabled: {enabled}")
        print(f"  - Update interval: {interval} seconds")
        print(f"  - Debug: {debug}")
        
        transmission_count = 0
        
        while self.running:
            if enabled == 'on':
                try:
                    print(f"\n--- Transmission #{transmission_count + 1} ---")
                    
                    # Load configuration (also applies ENV overrides)
                    cfg = read_config()
                    print(f"Config loaded for {cfg['callsign']}-{cfg['ssid']}")
                    
                    # Load weather data
                    meteo_file = "/config/meteo.json"
                    if os.path.exists(meteo_file):
                        try:
                            with open(meteo_file, 'r') as f:
                                meteo = json.load(f)
                            print(f"Weather file loaded: {len(meteo)} parameters")
                            if debug:
                                print(f"Weather data: {meteo}")
                        except json.JSONDecodeError as e:
                            print(f"Error parsing weather file: {e}")
                            meteo = {}
                        except Exception as e:
                            print(f"Error reading weather file: {e}")
                            meteo = {}
                    else:
                        meteo = {}
                        print("Weather file not found - using empty data")
                    
                    # Send APRS packet
                    send_aprs_packet(cfg, meteo, is_test=False)
                    transmission_count += 1
                    
                    print(f"Transmission #{transmission_count} completed successfully")
                    print(f"Next transmission in {interval} seconds")
                    
                except Exception as e:
                    print(f"Error in transmission: {e}")
                    if debug:
                        import traceback
                        traceback.print_exc()
            
            else:
                # Only display this message once at startup
                if transmission_count == 0:
                    print("Daemon disabled via APRS_AUTO_ENABLED=off")
                    print("Set APRS_AUTO_ENABLED=on to enable automatic transmissions")
                    print(f"Sleeping for {interval} seconds...")
            
            # Sleep in small steps to allow quick shutdown
            sleep_count = 0
            while sleep_count < interval and self.running:
                time.sleep(1)
                sleep_count += 1
                
                # Check if runtime ENV variables changed every 60 seconds
                if sleep_count % 60 == 0 and self.running:
                    new_enabled = os.getenv('APRS_AUTO_ENABLED', 'off').lower()
                    new_interval = int(os.getenv('APRS_UPDATE_INTERVAL', '3600'))
                    
                    if new_enabled != enabled:
                        enabled = new_enabled
                        print(f"Configuration updated: enabled = {enabled}")
                        if enabled == 'off':
                            print("Transmissions disabled - daemon will sleep")
                        else:
                            print("Transmissions enabled - resuming operations")
                    
                    if new_interval != interval:
                        interval = new_interval
                        print(f"Configuration updated: interval = {interval} seconds")
        
        print("APRS Daemon shutdown completed")

def main():
    print("Starting APRS Weather Station Daemon...")
    try:
        daemon = APRSDaemon()
        daemon.run()
    except KeyboardInterrupt:
        print("\nDaemon interrupted by user")
    except Exception as e:
        print(f"Daemon error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
