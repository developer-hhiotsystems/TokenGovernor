from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tokengovernor",
    version="0.1.0",
    author="TokenGovernor Team",
    author_email="tokengovernor@example.com",
    description="Standalone governance system for agentic coding workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/TokenGovernor",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10", 
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "flake8>=6.1.0",
            "black>=23.9.1",
            "bandit>=1.7.5",
            "safety>=2.3.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "token-gov=tokengovernor.cli.main:main",
        ],
    },
)