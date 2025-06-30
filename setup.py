#!/usr/bin/env python3
"""
Setup script for AI-Driven Observability for Automated Root Cause Analysis

This setup.py file allows the project to be installed as a Python package,
making it easier to manage dependencies and deploy in various environments.

Usage:
    pip install -e .                    # Development install
    pip install .                       # Regular install
    python setup.py install             # Direct install
    python setup.py develop             # Development mode
    python setup.py sdist               # Create source distribution
    python setup.py bdist_wheel         # Create wheel distribution
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure Python version compatibility
if sys.version_info < (3, 12):
    raise RuntimeError("This package requires Python 3.12 or higher")

# Read long description from README
def read_long_description():
    """Read the README file for long description"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "AI-Driven Observability for Automated Root Cause Analysis"

# Read requirements from requirements files
def read_requirements(filename):
    """Read requirements from a requirements file"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Read backend requirements
backend_requirements = read_requirements('backend/requirements.txt')

# Read frontend requirements  
frontend_requirements = read_requirements('frontend/requirements.txt')

# Combine and deduplicate requirements
all_requirements = list(set(backend_requirements + frontend_requirements))

# Additional development requirements
dev_requirements = [
    'pytest>=7.4.0',
    'pytest-asyncio>=0.21.0',
    'pytest-cov>=4.1.0',
    'black>=23.0.0',
    'flake8>=6.0.0',
    'mypy>=1.5.0',
    'pre-commit>=3.0.0',
    'locust>=2.17.0',  # For performance testing
    'jupyter>=1.0.0',  # For data analysis notebooks
]

# Testing requirements
test_requirements = [
    'pytest>=7.4.0',
    'pytest-asyncio>=0.21.0',
    'pytest-cov>=4.1.0',
    'httpx>=0.24.0',  # For testing FastAPI
    'factory-boy>=3.3.0',  # For test data generation
]

# Documentation requirements
doc_requirements = [
    'mkdocs>=1.5.0',
    'mkdocs-material>=9.0.0',
    'mkdocstrings>=0.22.0',
    'mkdocs-jupyter>=0.24.0',
]

# Production requirements (additional tools for production deployment)
prod_requirements = [
    'gunicorn>=21.0.0',
    'uvicorn[standard]>=0.24.0',
    'supervisor>=4.2.5',
    'prometheus-client>=0.17.0',
    'sentry-sdk>=1.32.0',
]

setup(
    # Basic package information
    name="ai-observability-rca",
    version="1.0.0",
    author="AI Observability Team",
    author_email="team@example.com",
    description="AI-Driven Observability for Automated Root Cause Analysis in Modern IT Systems",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/ai-observability-rca",
    project_urls={
        "Bug Reports": "https://github.com/your-org/ai-observability-rca/issues",
        "Source": "https://github.com/your-org/ai-observability-rca",
        "Documentation": "https://your-org.github.io/ai-observability-rca",
    },
    
    # Package discovery
    packages=find_packages(include=['backend', 'backend.*', 'frontend', 'frontend.*']),
    package_dir={
        'ai_rca_backend': 'backend',
        'ai_rca_frontend': 'frontend',
    },
    
    # Include additional files
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.md', '*.yml', '*.yaml', '*.json', '*.env.example'],
        'backend': ['*.txt', '*.env.example'],
        'frontend': ['*.txt'],
        'scripts': ['*.sh', '*.py'],
        'config': ['*.py', '*.yml', '*.yaml'],
    },
    
    # Entry points for command-line tools
    entry_points={
        'console_scripts': [
            'ai-rca-backend=backend.run:main',
            'ai-rca-setup-db=scripts.setup_db:main',
            'ai-rca-generate-alerts=scripts.generate_sample_alerts:main',
            'ai-rca-performance-test=scripts.performance_test:main',
        ],
    },
    
    # Requirements
    python_requires=">=3.12.3",
    install_requires=all_requirements,
    
    # Extra requirements for different use cases
    extras_require={
        'dev': dev_requirements,
        'test': test_requirements,
        'docs': doc_requirements,
        'prod': prod_requirements,
        'all': dev_requirements + test_requirements + doc_requirements + prod_requirements,
        'backend': backend_requirements,
        'frontend': frontend_requirements,
    },
    
    # Classification
    classifiers=[
        # Development Status
        "Development Status :: 4 - Beta",
        
        # Intended Audience
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        
        # Topic
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        
        # License
        "License :: OSI Approved :: MIT License",
        
        # Programming Language
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        
        # Operating System
        "Operating System :: POSIX :: Linux",
        "Operating System :: Ubuntu",
        
        # Environment
        "Environment :: Web Environment",
        "Environment :: Console",
        
        # Framework
        "Framework :: FastAPI",
        "Framework :: AsyncIO",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "observability", "monitoring", "root-cause-analysis", "rca", 
        "artificial-intelligence", "machine-learning", "fastapi", "streamlit",
        "alerting", "correlation", "llm", "llama3", "ollama", "chromadb",
        "postgresql", "devops", "sre", "incident-management"
    ],
    
    # Minimum versions and compatibility
    zip_safe=False,
    
    # Test configuration
    test_suite='tests',
    tests_require=test_requirements,
    
    # Options for different commands
    options={
        'build_scripts': {
            'executable': '/usr/bin/python3',
        },
        'egg_info': {
            'tag_build': '',
            'tag_date': False,
        },
    },
)

# Post-installation hooks
def post_install():
    """Post-installation setup tasks"""
    print("\n" + "="*60)
    print("🎉 AI Observability RCA installed successfully!")
    print("="*60)
    print("\n📋 Next steps:")
    print("1. Setup database:        python scripts/setup_db.py")
    print("2. Install Ollama:        ./scripts/install_ollama.sh")
    print("3. Configure environment: cp backend/.env.example backend/.env")
    print("4. Start services:        ./scripts/start_services.sh")
    print("\n🌐 Access points:")
    print("- Frontend Dashboard: http://localhost:8501")
    print("- Backend API:        http://localhost:8000")
    print("- API Documentation:  http://localhost:8000/docs")
    print("\n📚 Documentation:")
    print("- README.md:          Quick start guide")
    print("- DEPLOYMENT.md:      Production deployment")
    print("- PROJECT_SUMMARY.md: Complete overview")
    print("\n🧪 Testing:")
    print("- Generate samples:    python scripts/generate_sample_alerts.py")
    print("- Performance test:    locust -f scripts/performance_test.py")
    print("="*60)

# Custom command classes
from setuptools import Command
from setuptools.command.install import install
from setuptools.command.develop import develop

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        post_install()

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        post_install()

class TestCommand(Command):
    """Custom test command."""
    description = 'Run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        
        # Run pytest
        subprocess.check_call([sys.executable, '-m', 'pytest', 'tests/', '-v'])

class CleanCommand(Command):
    """Custom clean command."""
    description = 'Clean build artifacts'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import shutil
        import os
        
        # Remove build artifacts
        dirs_to_remove = ['build', 'dist', '*.egg-info', '__pycache__']
        for dir_pattern in dirs_to_remove:
            if '*' in dir_pattern:
                import glob
                for path in glob.glob(dir_pattern):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        print(f"Removed {path}")
            else:
                if os.path.exists(dir_pattern):
                    shutil.rmtree(dir_pattern)
                    print(f"Removed {dir_pattern}")

# Add custom commands to setup
setup.cmdclass = {
    'install': PostInstallCommand,
    'develop': PostDevelopCommand,
    'test': TestCommand,
    'clean': CleanCommand,
}

if __name__ == '__main__':
    # This allows the setup.py to be run directly
    setup()
