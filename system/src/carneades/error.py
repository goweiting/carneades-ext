"""
class for errors:
"""

class Error(Exception):
    pass

class SyntaxError(Error): # extend the Error class
    """
    If the syntax is wrong or not obeyed
    """
    def __init__(self, lineIdx, colIdx, message):
        

class LexerError(Error):
