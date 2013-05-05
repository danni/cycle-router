from setuptools import setup

setup(name='cyclerouter',
      version='0.1',
      description='An app for doing things with cycling data',
      author='Danielle Madeley',
      author_email='danielle@madeley.id.au',
      url='https://github.com/danni/cycle-router',
      install_requires=[
        'Flask>=0.9',
        'SQLAlchemy>=0.7.9',
        'GeoAlchemy>=0.7.2',
        'httplib2>=0.7.7',
      ]
)
