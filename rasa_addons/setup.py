from setuptools import setup, find_packages

setup(
    name="rasa_addons",
    version="2.3.3-bf.4",
    author="Botfront",
    description="Rasa Addons - Components for Rasa and Botfront",
    install_requires=[
        "requests",
        "requests_futures",
        "fuzzy_matcher",
        "fbmessenger",
        "sgqlc",
        'pypred @ git+https://git@github.com/dialoguemd/pypred.git@7e30c9078e8a34a4ba3ecf96c6ea826173b25063',
    ],
    packages=find_packages(),
    licence="Apache 2.0",
    url="https://botfront.io",
    author_email="hi@botfront.io",
)
