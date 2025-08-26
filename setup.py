import setuptools
from pathlib import Path


root_dir = Path(__file__).absolute().parent
with (root_dir / "VERSION").open() as f:
    version = f.read()
with (root_dir / "requirements.in").open() as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="odk2gn",
    version=version,
    description="GeoNature-ODK project",
    maintainer="OFB and PNX",
    packages=setuptools.find_packages("./"),
    package_dir={"": "."},
    install_requires=requirements,
    entry_points={
        "console_scripts": ["odk2gn=odk2gn.main:odk2gn"],
        "gn_module": [
            "code = odk2gn:MODULE_CODE",
            "picto = odk2gn:MODULE_PICTO",
            "blueprint = odk2gn.blueprint:blueprint",
            "config_schema = odk2gn.config_schema:Odk2GnSchema",
            "alembic_branch = odk2gn:ALEMBIC_BRANCH",
            "migrations = odk2gn:migrations",
        ],
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU Affero General Public License v3"
        "Operating System :: OS Independent",
    ],
)
