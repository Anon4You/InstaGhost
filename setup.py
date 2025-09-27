from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="instaghost",
    version="1.0.0",
    author="Anon4You",
    author_email="your-email@example.com",
    description="Advanced Instagram OSINT Tool - Gather intelligence from Instagram profiles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anon4You/InstaGhost",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "instaghost=instaghost:main",
        ],
    },
    keywords="instagram osint security hacking reconnaissance",
    project_urls={
        "Bug Reports": "https://github.com/Anon4You/InstaGhost/issues",
        "Source": "https://github.com/Anon4You/InstaGhost",
    },
)
