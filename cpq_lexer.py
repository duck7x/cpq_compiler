from sly import Lexer

class CPQLexer(Lexer):
    
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
    # TODO: add lookahead of space where it's required
    RELOP   = r'(==|!=|>=|<=|<|>)'
    ADDOP   = r'[\+|-]'
    MULOP   = r'[\*|/]'
    OR      = r'\|\|'
    AND     = r'&&'
    NOT     = r'!'
    CAST    = r'static_cast<(int|float)>'
    ID      = r'[a-zA-Z][a-zA-Z0-9]*'
    NUM     = r'\d+|\d+\.\d*'
    
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
        self.lineno += t.value.count('\n')
    
    # error handling
    def error(self, t):
        print(f"ERROR: Bad character {t.value[0]} at line {self.lineno}")
        self.index += 1
        self.found_errors = True
        return t
    
# Usage example:
if __name__ == '__main__':
    data = '''
/* Finding minimum between two numbers */
a, b: float;

{
input(a);
input(b);
if (a < b)
output(a);
else
output(b);
}
    '''
    
#     data = '''
# {
#     a b c : float;
#     static_cast<int> b;
#     d = static_cast<float> c + a;
#     e = static_cast<float> b static_cast<int> static_cast<float> c;
# }
#     '''
    lexer = CPQLexer()
    for tok in lexer.tokenize(data):
        print(tok)
    
"""
important notes from the docs:
• Longer tokens always need to be specified before short tokens
• @_() with multiple regex
• If the error() method also returns the passed token, it will show up as an ERROR token in the resulting token stream.
"""