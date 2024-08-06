from setuptools import setup, find_packages
from setuptools.command.install import install
import os

try:
    # pip >=20
    from pip._internal.network.session import PipSession
    from pip._internal.req import parse_requirements
except ImportError:
    try:
        # 10.0.0 <= pip <= 19.3.1
        from pip._internal.download import PipSession
        from pip._internal.req import parse_requirements
    except ImportError:
        # pip <= 9.0.3
        from pip.download import PipSession
        from pip.req import parse_requirements

def load_requirements(fname):
    reqs = parse_requirements(fname, session="test")
    return [str(ir.requirement) for ir in reqs]


is_cloud = os.getenv("IS_CLOUD", False)
requirements = load_requirements("requirements-cloud.txt") if is_cloud else load_requirements("requirements.txt")

class CustomInstallCommand(install):
    """
    Custom command to print a variable during installation. 
    Will be visible if "-v" passed to pip install.
    """
    def run(self):
        print(f"Custom message: is_cloud: {is_cloud}")
        print(f"Custom message: requirements: {requirements}")
        install.run(self)


setup(
    name="karman",
    version="2.0",
    description="",
    url="https://github.com/FrontierDevelopmentLab/2024-HL-ThermCL",
    author="HL-2024-HL",
    author_email="",
    license="Apache-2.0",
    packages=find_packages(),
    install_requires=requirements,
    cmdclass={"install": CustomInstallCommand},
)
