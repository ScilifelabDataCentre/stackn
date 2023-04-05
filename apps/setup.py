from setuptools import setup

setup(
    name="studio-apps",
    version="0.0.1",
    description="""Django app for handling portal in Studio""",
    url="https://www.scaleoutsystems.com",
    include_package_data=True,
    package=["apps"],
    package_dir={"apps": "."},
    python_requires=">=3.6,<4",
    install_requires=[
        "django==4.1.7",
        "requests==2.28.1",
        "django-guardian==2.4.0",
        "celery==5.2.7",
        "Pillow==9.4.0",
        "django-tagulous==1.3.3",
        "minio==7.0.2",
        "s3fs==2022.1.0",
        "flatten-json==0.1.13",
        "PyYAML==6.0",
    ],
    license="Copyright Scaleout Systems AB. See license for details",
    zip_safe=False,
    keywords="",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)