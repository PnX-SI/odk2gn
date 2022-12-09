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
    description="GeoNature-monitoring ODK project",
    maintainer="OFB and PNX",
    # url='https://github.com/PnX-SI/gn_module_monitoring',
    packages=setuptools.find_packages("odk2gn"),
    package_dir={"": "."},
    install_requires=requirements,
    tests_require=[],
    entry_points={
        "console_scripts": [
            "synchronize=odk2gn.main:synchronize",
            "upgrade_odk_form=odk2gn.main:upgrade_odk_form",
            "test1=odk2gn.main:get_and_post_medias",
            "odk_schema=odk2gn.main:get_schema",
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
