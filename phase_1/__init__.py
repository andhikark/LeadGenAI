import os
import subprocess

def setup_environment():
    # Create a virtual environment
    env_dir = "env"
    if not os.path.exists(env_dir):
        subprocess.run(["python", "-m", "venv", env_dir])
        print(f"Virtual environment created at {env_dir}")
    else:
        print(f"Virtual environment already exists at {env_dir}")

    # Activate the virtual environment and installing required modules
    activate_script = os.path.join(env_dir, "Scripts", "activate") if os.name == "nt" else os.path.join(env_dir, "bin", "activate")
    requirements_file = "requirements.txt"
    
    pip_path = os.path.join(env_dir, "Scripts", "pip") if os.name == "nt" else os.path.join(env_dir, "bin", "pip")
    if os.path.exists(requirements_file):
        subprocess.run([pip_path, "install", "-r", requirements_file])
        print(f"Installed modules from {requirements_file}")
    else:
        print(f"{requirements_file} not found. Skipping module installation.")

    # Install Playwright browsers
    print("Installing Playwright...")
    subprocess.run(['playwright', 'install'])
    print("Playwright browsers installed")

if __name__ == "__main__":
    setup_environment()