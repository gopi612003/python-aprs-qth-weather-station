# coding: utf-8
import multiprocessing
import time
import signal
import sys
import os

def run_flask_app():
    """Start the Flask app to receive weather data"""
    try:
        from app import app
        print("Starting Flask weather data receiver...")
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask app error: {e}")

def run_aprs_daemon():
    """Start the APRS daemon"""
    # Wait a few seconds to give Flask time to start
    time.sleep(5)
    try:
        from aprs_send_daemon import APRSDaemon
        print("Starting APRS transmission daemon...")
        daemon = APRSDaemon()
        daemon.run()
    except Exception as e:
        print(f"APRS daemon error: {e}")

class ServiceManager:
    def __init__(self):
        self.processes = []
        
    def signal_handler(self, signum, frame):
        """Handle termination signals and stop all services cleanly"""
        print(f"Received shutdown signal {signum}")
        for process in self.processes:
            if process.is_alive():
                process.terminate()
        
        # Wait for processes to finish
        for process in self.processes:
            process.join(timeout=10)
            if process.is_alive():
                process.kill()
        
        print("All services stopped")
        sys.exit(0)
    
    def start(self):
        """Start and monitor Flask app and APRS daemon services"""
        # Register clean shutdown handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("Starting APRS Weather Station Services...")
        
        # Start Flask in a separate process
        flask_process = multiprocessing.Process(target=run_flask_app, name="FlaskApp")
        flask_process.start()
        self.processes.append(flask_process)
        print(f"Flask process started (PID: {flask_process.pid})")
        
        # Start APRS daemon in a separate process
        aprs_process = multiprocessing.Process(target=run_aprs_daemon, name="APRSDaemon")
        aprs_process.start()
        self.processes.append(aprs_process)
        print(f"APRS daemon process started (PID: {aprs_process.pid})")
        
        try:
            # Keep the main process alive and monitor child processes
            while True:
                for process in list(self.processes):
                    if not process.is_alive():
                        print(f"Process {process.name} (PID: {process.pid}) died with exit code {process.exitcode}, restarting...")
                        if process.name == "FlaskApp":
                            new_process = multiprocessing.Process(target=run_flask_app, name="FlaskApp")
                        else:
                            new_process = multiprocessing.Process(target=run_aprs_daemon, name="APRSDaemon")
                        
                        new_process.start()
                        self.processes.remove(process)
                        self.processes.append(new_process)
                        print(f"Restarted {new_process.name} (new PID: {new_process.pid})")
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    manager = ServiceManager()
    manager.start()
