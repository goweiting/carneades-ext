# Reader class that encapsulated the scanner, lexer and parser.
# It takes in a ``.yml`` file (may support more than one in future) and
# generates the json file which can be used by the caes to create the
# argumentation graph.



import os
import sys
import logging

class Reader(object):

    def process(self, filename):

        print('hello')
        while True:
            c = f.read(1)
            # if not c:
            #     print("end of line")
            #     break
            # print(c);



if __name__ == '__main__':
    """
    the main function that processes the files passed into the command line:
    """
    filenames = sys.argv[1:];
    print(filename)
    reader = Reader();

    with open(filename) as f:
        reader.process(f);


class character(object):
    """
    define the character's position position and the value (char)

    The information will be used by the lexer should it find error in the file
    """

    def __init__(self, c, lineIdx, colIdx, sourceID):
        """
        initialised the character
        :param c : a single character
        :param lineIdx : the line number of the file
        :param colIdx : the column number of the file
        :parm sourceID : if multiple files are given in the argument, this corresponds to the nth file.
        """
        self.c = c;
        self.lineIdx = lineIdx;
        self.colIdx = colIdx;
        self.sourceID = sourceID;

    def __str__(self):
        """
        for us to print the character
        add additional specification for the character value
        """
        c = self.c;


    def __repr__(self):
        return self.__str__();
