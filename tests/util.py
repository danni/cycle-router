import os.path

from tests import __path__

def get_test_resource(*args):
    """
    Return the path of a test resource.
    """

    path = os.path.join(__path__[0], *args)
    print path
    return path
