"""
class for errors:
"""

class Error(Exception):
    """
    Base class for exceptions in `carneades` package
    """
    pass



# ------------------------------------------------
#   Error for Scanning, Tokenising and Parsing
# ------------------------------------------------
class TokenizerError(Error): # extend the Error class
    """
    If the syntax is wrong or not obeyed, tell user where it occurs!
    """
    def __init__(self, lineIdx, colIdx, message):
        self.lineIdx    = lineIdx
        self.colIdx     = colIdx
        self.message    = message

    def __str__(self):
        s = '{} ocured at line {}, column {}'.format(self.message, self.lineIdx, self.colIdx)
        return(s)
