from setuptools import setup, find_packages

setup(
    name="grundzeug",
    version="0.1.0",
    packages=find_packages(exclude=["tests.*", "tests"]),
    url="",
    license="Apache License 2.0",
    author="Nick Guletskii",
    author_email="nick@nickguletskii.com",
    description="Grundzeug Dependency Injection container and configuration management framework",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
)
