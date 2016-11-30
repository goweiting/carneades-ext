"""
Implementation of the Dialogue for the arguments

1) The implementation includes the follow:
class:Stage
"""

class Stage(object):
    """
    store the arguments and status in the current stage
    """

    def __init__(self, arguments, status):
        # check for the same number
        if len(arguments) != len(status):
            raise Exception('There are {} arguments but {} status given'.format(len(arguments), len(status)))

        self.current = dict()
        for arg in arguments:


# The proponent always starts first:
