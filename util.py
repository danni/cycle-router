"""
Utilities
"""


def monkeypatch(*args):
    """
    Decorator to monkeypatch a function into class as a method
    """

    def inner(func):
        name = func.__name__

        for cls in args:
            old = getattr(cls, name)
            setattr(cls, '__super__{}'.format(name), old)

            setattr(cls, name, func)

    return inner
