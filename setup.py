#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Setup dot py."""
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from os.path import dirname, join
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.build_ext import build_ext
from setuptools.command.install import install


CNS_BINARY_URL = ""


class CustomBuildInstall(install):
    """Custom Build and Install class"""

    def run(self):
        self.run_command("build_ext")
        install.run(self)


class CustomBuild(build_ext):
    """CustomBuild handles the build of the C++ dependencies"""

    def run(self):
        # TODO: Find a smarter way of passing this `bin_dir` without defining it outside `__init__`
        self.bin_dir = Path(self.get_install_dir(), "haddock", "bin")
        self.bin_dir.mkdir(exist_ok=True, parents=True)

        # Build FCC
        self.clone_and_build_submodule(
            name="FCC",
            repo_url="https://github.com/haddocking/fcc.git",
            build_cmd="make",
            src_dir="src",
            binary_name="contact_fcc",
        )

        # Build fast-rmsdmatrix
        self.clone_and_build_submodule(
            name="fast-rmsdmatrix",
            repo_url="https://github.com/mgiulini/fast-rmsdmatrix.git",
            build_cmd="make fast-rmsdmatrix",
            src_dir="src",
            binary_name="fast-rmsdmatrix",
        )

        # Run original build_ext
        build_ext.run(self)

    def get_install_dir(self):
        """Get the directory in which HADDOCK was installed"""
        install_cmd = self.get_finalized_command("install")
        return install_cmd.install_lib  # type: ignore

    def clone_and_build_submodule(
        self, name, repo_url, build_cmd, src_dir, binary_name
    ):
        """Clone a repository and build."""
        print(f"Building {name}...")
        with tempfile.TemporaryDirectory() as temp_dir:

            # clone the repository
            subprocess.run(["git", "clone", repo_url, temp_dir], check=True)

            # Build
            build_dir = Path(temp_dir, src_dir)
            subprocess.run(
                build_cmd,
                shell=True,
                cwd=build_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # TODO: Add error handling

            # Move the binary
            src_bin = Path(build_dir, binary_name)
            dst_bin = Path(self.bin_dir, binary_name)

            shutil.copy2(src_bin, dst_bin)


class CNSInstall(CustomBuildInstall):
    """Custom class to handle the download of the CNS binary"""

    def run(self):
        """Run the installation"""

        # Run the standard installation
        CustomBuildInstall.run(self)

        # Get the installation directory
        if self.install_lib is None:
            print("Something went wrong during installation.")
            sys.exit(1)

        # Set where the cns binary needs to be
        bin_dir = Path(self.install_lib, "haddock", "bin")

        # Create the `bin/` directory
        bin_dir.mkdir(exist_ok=True)

        # Download the binary
        cns_exec = Path(bin_dir, "cns")
        if cns_exec.exists():
            cns_exec.unlink()

        urllib.request.urlretrieve(CNS_BINARY_URL, cns_exec)

        # TODO: Handle failed download

        os.chmod(cns_exec, 0o755)


with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()


def read_description(*names, **kwargs) -> str:
    """Read description files."""
    path = join(dirname(__file__), *names)
    with open(path, encoding=kwargs.get("encoding", "utf8")) as fh:
        return fh.read()


readme = read_description("README.md")
changelog = read_description("CHANGELOG.md")
long_description = f"{readme}{os.linesep}{changelog}"


setup(
    name="haddock3",
    version="3.0.0",
    description="HADDOCK3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache License 2.0",
    author="BonvinLab",
    author_email="bonvinlab.support@uu.nl",
    url="https://github.com/haddocking/haddock3",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # TODO: Update the classifiers - http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3.9",
    ],
    project_urls={
        "webpage": "https://bonvinlab.org/haddock3",
        "Documentation": "https://github.com/haddocking/haddock3#readme",
        "Changelog": "",
        "Issue Tracker": "https://github.com/haddocking/haddock3/issues",
        "Discussion Forum": "https://github.com/haddocking/haddock3/issues",
    },
    keywords=[
        "Structural Biology",
        "Biochemistry",
        "Docking",
        "Protein docking",
        "Proteins",
    ],
    python_requires=">=3.9, <3.10",
    install_requires=[requirements],
    extras_require={},
    setup_requires=[],
    entry_points={
        "console_scripts": [
            "haddock3 = haddock.clis.cli:maincli",
            "haddock3-mpitask = haddock.clis.cli_mpi:maincli",
            "haddock3-bm = haddock.clis.cli_bm:maincli",
            "haddock3-cfg = haddock.clis.cli_cfg:maincli",
            "haddock3-clean = haddock.clis.cli_clean:maincli",
            "haddock3-copy = haddock.clis.cli_cp:maincli",
            "haddock3-dmn = haddock.clis.cli_dmn:maincli",
            "haddock3-pp = haddock.clis.cli_pp:maincli",
            "haddock3-score = haddock.clis.cli_score:maincli",
            "haddock3-unpack = haddock.clis.cli_unpack:maincli",
            "haddock3-analyse = haddock.clis.cli_analyse:maincli",
            "haddock3-traceback = haddock.clis.cli_traceback:maincli",
            "haddock3-re = haddock.clis.cli_re:maincli",
            "haddock3-restraints = haddock.clis.cli_restraints:maincli",
        ]
    },
    cmdclass={"build_ext": CustomBuild, "install": CNSInstall},
)
