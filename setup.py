from setuptools import setup

setup(
    name="vrocli",
    version='1.0',
    py_modules=['vrocli'],
    install_requires=[
        'Click',
        'pyyaml',
        'coloredlogs',
        'lxml',
        'Jinja2',
    ],
    entry_points='''
        [console_scripts]
        vrocli=vrocli:vrocli
    ''',
)
