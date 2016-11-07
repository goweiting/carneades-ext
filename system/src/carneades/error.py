"""
class for errors:
"""

class Error(Exception):
    """
    Base class for exceptions in `carneades` package
    """
    pass



# ------------------------------------------------
#   Error for Scanning, Tokenising
# ------------------------------------------------
class TokenizerError(Error): # extend the Error class
    """
    Tokenizer throws error if basic syntax error (such as no End of line) is found.
    May add more functionality here
    """
    def __init__(self, lineIdx, colIdx, message):
        self.lineIdx    = lineIdx
        self.colIdx     = colIdx
        self.message    = message

    def __str__(self):
        s = '{} at line {}, column {}'.format(self.message, self.lineIdx, self.colIdx)
        return(s)

# ------------------------------------------------
#   Error for Parsing
# ------------------------------------------------
class ParseError(Error):
    """
    Parser throws error is the syntax for forming sequences or maps are not obeyed
    """
    def __init__(self, message):
        self.message = message
