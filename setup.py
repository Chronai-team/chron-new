from setuptools import setup, find_packages

setup(
    name="chronai",
    version="0.1.0",
    description="AI Project Analysis Tool",
    author="Chronai Team",
    author_email="team@chronai.ai",
    packages=find_packages(),
    install_requires=[
        "gitpython>=3.1.40",
        "pydantic>=2.4.2",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "radon>=6.0.1",
        "pylint>=3.0.2",
        "mypy>=1.7.0",
        "tensorflow-hub>=0.15.0",
        "torch>=2.2.0",
        "transformers>=4.35.2",
        "openai>=1.12.0",
        "solana>=0.30.2",
        "anchorpy>=0.18.0",
    ],
    python_requires=">=3.8",
)
