#!/usr/bin/env python3
"""
Startup script for Job Packaging Tool
This script checks dependencies and starts the Flask application.
"""

import os
import sys
import subprocess
import importlib.util


def check_dependency(module_name, package_name=None):
    """Check if a Python module is available."""
    if package_name is None:
        package_name = module_name

    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"✗ {package_name} is not installed")
        return False
    else:
        print(f"✓ {package_name} is available")
        return True


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")

    required_deps = [
        ('flask', 'Flask'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('scipy', 'SciPy'),
        ('PyPDF2', 'PyPDF2'),
        ('fpdf', 'FPDF'),
        ('requests', 'Requests')
    ]

    missing_deps = []
    for module_name, package_name in required_deps:
        if not check_dependency(module_name, package_name):
            missing_deps.append(package_name)

    if missing_deps:
        print(f"\nMissing dependencies: {', '.join(missing_deps)}")
        print("Please install them using:")
        print("pip install -r requirements.txt")
        return False

    print("\n✓ All dependencies are available")
    return True


def check_ollama():
    """Check if Ollama is running."""
    print("\nChecking Ollama status...")

    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running and accessible")
            return True
        else:
            print("⚠️  Ollama is not responding properly")
            return False
    except Exception as e:
        print("⚠️  Ollama is not running or not accessible")
        print("   You can still use the application, but cover letter generation will not work.")
        print("   To start Ollama, run: ollama serve")
        return False


def main():
    """Main startup function."""
    print("Job Packaging Tool - Startup")
    print("=" * 30)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start application due to missing dependencies.")
        sys.exit(1)

    # Check Ollama (optional)
    ollama_available = check_ollama()

    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('uploads/pdfs', exist_ok=True)
    os.makedirs('uploads/texts', exist_ok=True)

    print("\n🚀 Starting Job Packaging Tool...")
    print("   The application will be available at: http://127.0.0.1:8000")
    print("   Press Ctrl+C to stop the application")

    if not ollama_available:
        print("\n⚠️  Note: Ollama is not running. Cover letter generation will not work.")
        print("   To enable cover letter generation, start Ollama with: ollama serve")

    # Start the Flask application
    try:
        from app import app
        app.run(debug=True, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
