from setuptools import setup, find_packages

setup(
    name="agentic",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "langgraph",
        "pydantic>=2.0",
        "langchain-core",
        "langchain-openai",
        "click>=8.0",
    ],
    entry_points={
        'console_scripts': [
            'agentic=agentic.cli:cli',
        ],
    },
)