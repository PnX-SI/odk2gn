import setuptools
from pathlib import Path


root_dir = Path(__file__).absolute().parent
with (root_dir / "VERSION").open() as f:
    version = f.read()

setuptools.setup(
    name="odk_flore_prioritaire",
    version=version,
    description="Flore prioritaire ODK project",
    maintainer="PNE",
    # url='https://github.com/PnX-SI/gn_module_monitoring',
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    tests_require=[],
    entry_points={
        "gn_odk_contrib": [
            "synchronize=odk_flore_prioritaire.main:synchronize",
            "upgrade_odk_form=odk_flore_prioritaire.main:upgrade_odk_form",
        ]
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
