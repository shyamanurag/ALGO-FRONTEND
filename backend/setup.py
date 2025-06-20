from setuptools import setup, find_packages

setup(
    name="trading-system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0,<0.100.0",
        "uvicorn>=0.15.0,<0.25.0",
        "pandas>=1.3.0,<2.0.0",
        "numpy>=1.20.0,<2.0.0",
        "pydantic>=1.8.0,<2.0.0",
        "aiohttp>=3.8.0,<4.0.0",
        "plotly>=5.3.0,<6.0.0",
        "psutil>=5.8.0,<6.0.0",
        "python-dotenv>=0.19.0,<1.0.0",
        "websockets>=10.0,<11.0",
        "redis>=4.0.0,<5.0.0",
        "sqlalchemy>=1.4.0,<2.0.0",
        "alembic>=1.7.0,<2.0.0",
        "pytest>=6.2.0,<7.0.0",
        "pytest-asyncio>=0.16.0,<0.20.0",
        "pytest-cov>=2.12.0,<3.0.0",
        "black>=21.12b0,<22.0.0",
        "isort>=5.10.0,<6.0.0",
        "mypy>=0.910,<1.0.0",
        "flake8>=4.0.0,<5.0.0"
    ],
    python_requires=">=3.10,<3.12",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated Trading System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-system",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 