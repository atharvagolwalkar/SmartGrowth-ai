#!/usr/bin/env python3
"""
SmartGrowth AI Deployment Script

Quick deployment and system startup script for production environments.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

class SmartGrowthDeployment:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.api_process = None
        self.dashboard_process = None
    
    def check_system(self):
        """Check system prerequisites"""
        print("🔍 System Check")
        print("=" * 50)
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
        
        print(f"✅ Python {sys.version.split()[0]}")
        
        # Check key files
        required_files = [
            'requirements.txt',
            'config.py', 
            'app/main.py',
            'app/dashboard_enhanced.py',
            'ml_models/churn/predictor.py'
        ]
        
        for file_path in required_files:
            if (self.project_root / file_path).exists():
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path} - Missing")
                return False
        
        return True
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print("\n📦 Installing Dependencies")
        print("=" * 50)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Dependency installation failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def setup_database(self):
        """Initialize database"""
        print("\n🗄️  Database Setup")
        print("=" * 50)
        
        try:
            result = subprocess.run(
                [sys.executable, "setup_database.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Database setup complete")
                print(result.stdout)
                return True
            else:
                print(f"❌ Database setup failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            return False
    
    def start_api(self):
        """Start FastAPI backend"""
        print("\n🌐 Starting API Backend")
        print("=" * 50)
        
        try:
            # Change to app directory for proper imports
            app_dir = self.project_root / "app"
            
            self.api_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for startup
            time.sleep(3)
            
            # Check if process is still running
            if self.api_process.poll() is None:
                print("✅ API backend started successfully")
                print("📍 API URL: http://localhost:8000")
                print("📖 Documentation: http://localhost:8000/docs")
                return True
            else:
                stdout, stderr = self.api_process.communicate()
                print(f"❌ API failed to start")
                print(f"Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting API: {e}")
            return False
    
    def start_dashboard(self):
        """Start Streamlit dashboard"""
        print("\n📱 Starting Dashboard")
        print("=" * 50)
        
        try:
            app_dir = self.project_root / "app"
            
            # Use streamlit run command
            self.dashboard_process = subprocess.Popen(
                [
                    sys.executable, "-m", "streamlit", "run", 
                    "dashboard_enhanced.py", "--server.headless", "true"
                ],
                cwd=app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for startup
            time.sleep(5)
            
            if self.dashboard_process.poll() is None:
                print("✅ Dashboard started successfully")
                print("📍 Dashboard URL: http://localhost:8501")
                return True
            else:
                stdout, stderr = self.dashboard_process.communicate()
                print(f"❌ Dashboard failed to start")
                print(f"Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting dashboard: {e}")
            return False
    
    def run_tests(self):
        """Run system tests"""
        print("\n🧪 Running Tests")
        print("=" * 50)
        
        try:
            result = subprocess.run(
                [sys.executable, "run_tests.py"],
                cwd=self.project_root,
                text=True
            )
            
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def stop_services(self):
        """Stop running services"""
        print("\n🛑 Stopping Services")
        print("=" * 50)
        
        if self.api_process and self.api_process.poll() is None:
            self.api_process.terminate()
            self.api_process.wait()
            print("✅ API backend stopped")
        
        if self.dashboard_process and self.dashboard_process.poll() is None:
            self.dashboard_process.terminate()
            self.dashboard_process.wait()
            print("✅ Dashboard stopped")
    
    def deploy(self, mode="full"):
        """Main deployment function"""
        print("🚀 SmartGrowth AI Deployment")
        print("=" * 50)
        print(f"Mode: {mode.upper()}")
        
        # System check
        if not self.check_system():
            print("❌ System check failed")
            return False
        
        # Install dependencies
        if mode in ["full", "setup"]:
            if not self.install_dependencies():
                print("❌ Dependency installation failed")
                return False
        
        # Setup database
        if mode in ["full", "setup"]:
            if not self.setup_database():
                print("❌ Database setup failed")
                return False
        
        # Run tests
        if mode in ["full", "test"]:
            if not self.run_tests():
                print("❌ Tests failed")
                return False
        
        # Start services
        if mode in ["full", "start"]:
            if not self.start_api():
                print("❌ API startup failed")
                return False
            
            if not self.start_dashboard():
                print("❌ Dashboard startup failed")
                return False
            
            # Setup signal handler for graceful shutdown
            def signal_handler(sig, frame):
                print("\n\n🛑 Shutting down...")
                self.stop_services()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            
            print("\n🎉 SmartGrowth AI is now running!")
            print("=" * 50)
            print("📍 Services:")
            print("  • API Backend:     http://localhost:8000")
            print("  • API Docs:        http://localhost:8000/docs")  
            print("  • Dashboard:       http://localhost:8501")
            print("\n⌨️  Press Ctrl+C to stop")
            
            # Keep alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_services()
        
        print("\n✅ Deployment completed successfully")
        return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartGrowth AI Deployment Script")
    parser.add_argument(
        "mode", 
        choices=["full", "setup", "test", "start", "stop"],
        default="full",
        nargs="?",
        help="Deployment mode (default: full)"
    )
    
    args = parser.parse_args()
    
    deployment = SmartGrowthDeployment()
    
    if args.mode == "stop":
        deployment.stop_services()
    else:
        success = deployment.deploy(args.mode)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()