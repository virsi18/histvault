"""
Copyright 2026 HistVault Open Source Project Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from setuptools import setup, find_packages

setup(
    name="histvault",
    version="1.0.0",
    description="Automated Browser History Preservation Vault & Anti-Deletion Archive",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="HistVault Open Source Project Contributors",
    author_email="maintainers@histvault.org",
    url="https://github.com/virsi18/histvault",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "histvault": ["server/static/*"],
    },
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "cli-pretty": ["rich>=13.0.0"],
    },
    entry_points={
        "console_scripts": [
            "histvault=histvault.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: System :: Archiving :: Backup",
    ],
)

