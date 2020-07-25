from setuptools import setup, find_packages

setup(
    name="grundzeug",
    packages=find_packages(exclude=["tests.*", "tests"]),
    url="https://grundzeug.nickguletskii.com/",
    license="Apache License 2.0",
    author="Nick Guletskii",
    author_email="nick@nickguletskii.com",
    description="Grundzeug Dependency Injection container and configuration management framework",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities"
    ],
    python_requires='>=3.7',
    install_requires=[
        "typing-extensions>=3.7.4.1",
    ]
)
