from setuptools import setup, find_packages

setup(
    name="rasa_addons",
    version="2.2.5.2",
    author="Botfront",
    description="Rasa Addons - Components for Rasa and Botfront",
    install_requires=[
        "requests",
        "requests_futures",
        "fuzzy_matcher",
        "fbmessenger",
        "sgqlc",
    ],
    packages=find_packages(),
    licence="Apache 2.0",
    url="https://botfront.io",
    author_email="hi@botfront.io",
)
