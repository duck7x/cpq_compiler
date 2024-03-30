from sly import Lexer

# TODO: address comments!
class CPQLexer(Lexer):
    
    # Set of token names
    tokens = {
        BREAK, CASE, DEFAULT, ELSE, FLOAT, IF, INPUT, INT, OUTPUT, SWITCH, WHILE,
        LPAREN, RPAREN, LBRAC, RBRAC, COMMA, COLON, SEMICOL, EQUALS,
        RELOP, ADDOP, MULOP, OR, AND, NOT, CAST,
        ID, NUM
    }
    
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
    ID['break']     = BREAK
    ID['case']      = CASE
    ID['default']   = DEFAULT
    ID['else']      = ELSE
    ID['float']     = FLOAT
    ID['if']        = IF
    ID['input']     = INPUT
    ID['int']       = INT
    ID['output']    = OUTPUT
    ID['switch']    = SWITCH
    ID['while']     = WHILE
    
    # Line number tracking
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')
    
    # error handling
    def error(self, t):
        # TODO: handle error!
        # for example:
        # print(f'Line {self.lineno}: Bad character {t.value[0]}')
        self.index += 1
        pass
    
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