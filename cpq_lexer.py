from sly import Lexer
from common_functions import print_error

class CPQLexer(Lexer):

    # Instance variable for tracking whether the lexer encountered any errors during its run
    found_errors = False

    # Set of token names
    tokens = { ELSE, FLOAT, IF, INPUT, INT, OUTPUT, WHILE, RELOP, ADDOP, MULOP, OR, AND, NOT, CAST, ID, NUM }

    # Set of literal tokens
    literals = { '(', ')', '{', '}', ',', ':', ';', '=' }

    # ignore white spaces
    ignore = ' \t'

    # ignore comments
    ignore_comment = r'/\*.*\*/'

    # Regex rules for tokens
    RELOP   = r'(==|!=|>=|<=|<|>)'
    ADDOP   = r'[\+-]'
    MULOP   = r'[\*/]'
    OR      = r'\|\|'
    AND     = r'&&'
    NOT     = r'!'
    CAST    = r'static_cast<(int|float)>'
    ID      = r'[a-zA-Z][a-zA-Z0-9]*'
    NUM     = r'\d+\.\d*|\d+'

    # Converting special keywords
    ID['else']      = ELSE
    ID['float']     = FLOAT
    ID['if']        = IF
    ID['input']     = INPUT
    ID['int']       = INT
    ID['output']    = OUTPUT
    ID['while']     = WHILE

    # Line number tracking
    @_(r'\n+')
    def ignore_newline(self, t):
        """
        Ignore new lines while keeping count of line numbers
        """

        self.lineno += t.value.count('\n')

    # error handling
    def error(self, t):
        """
        Handle lexer errors by
            Notifying the error using the print_error function
            Skipping the problematic character
            Setting the found_errors variable to true, to prevent .qod file creation
        """
        
        print_error(f'lexical error - bad character {t.value[0]}', line=self.lineno)
        self.index += 1
        self.found_errors = True
        return t
