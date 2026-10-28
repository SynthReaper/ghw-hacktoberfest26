from distutils.core import setup

setup(
    name='urlfetch',
    version='0.1.2',
    description='Simple Python 2 url retrieval tool',
    author='Forgotten Dev',
    author_email='ghost@example.null',
    url='http://code.google.com/p/urlfetch-py',
    py_modules=['urlfetch'],
    install_requires=[
        'httplib2',
        'simplejson',
    ],
    classifiers=[
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ]
)
