from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as readme_file:
	long_description = readme_file.read()

setup(
	name="farm_management",
	version="0.0.1",
	description="Enterprise Agricultural ERP extending ERPNext",
	long_description=long_description,
	long_description_content_type="text/markdown",
	author="VerityCore Consultancy",
	author_email="dev@veritycore.co.zw",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[],
)
