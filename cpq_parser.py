from sly import Parser
from cpq_lexer import CPQLexer
from common_functions import print_error

# TODO: maybe handle contsants better
_FLOAT = 'float'
_INT = 'int'

types = {
    _FLOAT: 'R',
    _INT: 'I'
}

ops = {
    '+': 'ADD',
    '-': 'SUB',
    '*': 'MLT',
    '/': 'DIV',
    '==': 'EQL',
    '!=': 'NQL',
    '<': 'LSS',
    '>': 'GRT',
    '=': 'EQL'
}

def temp_generator():
    count = 0
    while True:
        count += 1
        yield f't{count}'
    
    
def label_generator():
    count = 0
    while True:
        count += 1
        yield f'L{count}'


class CPQParser(Parser):
    
    # Get the token list from the lexer
    tokens = CPQLexer.tokens
    start = 'program'
    
    found_errors = False
    
    symbol_table = dict()
    quad_code = list()
    
    class NeedsAName():
        def __init__(self, value, type):
            self.val = value
            self.type = type
            
    _ZERO = NeedsAName(0, _INT)
    _ONE = NeedsAName(1, _INT)
    _TWO = NeedsAName(2, _INT)
    
    # generate a bit of code
    def gen(self, code):
        self.quad_code.append(code)
        
    
    def error(self, token):
        print_error(f'unrecognized token {token}', line=token.lineno)
        self.found_errors = True
    
        
    def semantic_error(self, error):
        print_error(error, line=self.lineno)
        self.found_errors = True
        
    
    def get_from_symbol_table(self, symbol):
        type = self.symbol_table.get(symbol)
        if type is None:
            self.semantic_error(f"{symbol} not in symbol table")
        return type  or _FLOAT
    
    
    def is_in_symbol_label(self, symbol):
        return self.symbol_table.get(symbol) is not None
    
    def add_to_symbol_table(self, symbol, type):
        if self.is_in_symbol_label(symbol):
            self.semantic_error(f"{symbol} already defined")
        self.symbol_table[symbol] = type
    
    
    def gen_label(self, label):
        self.gen(f'{label}: ')        

    def gen_jump_to_label(self, label):
        self.gen(f'JUMP {label}')
        
    def gen_cond_jump(self, label, cond):
        self.gen(f'JMPZ {label} {cond}')
        
    def get_type(self, first, second):
        return first if first == second else _FLOAT
    
    def convert_type(self, type, val):
        temp = self.get_temp()
        opcode = 'ITOR' if type == _FLOAT else 'RTOI'
        self.gen(' '.join([opcode, temp, val]))
        return self.NeedsAName(temp, type)
    
    def get_converted_operands(self, type, operands_list):
        converted_operands = list()
        for operand in operands_list:
            if operand.type != type:
                converted_operands.append(self.convert_type(type, operand.val))
            else:
                converted_operands.append(operand)
        return converted_operands
        
    
    def generate_three_adress_code(self, type, op, operands):
        self.gen(f'{types.get(type)}{ops.get(op)} {" ".join(operands)}')  # TODO: document this
        
    
    def three_adress_code(self, opcpde, operands):
        # TODO: document this
        temp = self.get_temp()
        type = self.get_type(*[ operand.type for operand in operands ])
        converted_operands = self.get_converted_operands(type, operands)
        all_operands_list = [temp] + [ operand.val for operand in converted_operands ]
        self.generate_three_adress_code(type, opcpde, all_operands_list)
        return self.NeedsAName(temp, type)
    
    _label_generator = label_generator()
    _temp_generator = temp_generator()
    
    
    def get_temp(self):
        temp = next(self._temp_generator)
        while self.is_in_symbol_label(temp):
            temp = next(self._temp_generator)
        return temp
    
    def get_label(self):
        return next(self._label_generator)
    
    # Grammer rules and actions
    @_('')
    def empty(self, p):
        pass
    
    @_('declarations stmt_block')
    def program(self, p):
        self.lineno = p.lineno
        self.gen('HALT')
        return self.quad_code
    
    @_('declarations declaration',
       'empty')
    def declarations(self, p):
        pass
    
    @_('idlist ":" type ";"')
    def declaration(self, p):
        self.lineno = p.lineno
        for id in p.idlist:
            self.add_to_symbol_table(id, p.type)
        return self.symbol_table
        
    @_('INT',
       'FLOAT')
    def type(self, p):
        self.lineno = p.lineno
        return p[0]
    
    @_('idlist "," ID')
    def idlist(self, p):
        self.lineno = p.lineno
        p.idlist.append(p.ID)
        return p.idlist
    
    @_('ID')
    def idlist(self, p):
        self.lineno = p.lineno
        return [p.ID]
    
    @_('assignment_stmt',
       'input_stmt',
       'output_stmt',
       'if_stmt',
       'while_stmt',
       'stmt_block')
    def stmt(self, p):
        pass
    
    @_('ID "=" expression ";"')
    def assignment_stmt(self, p):
        self.lineno = p.lineno
        '''
        get id from symbol table
        ensure the expression type fits
        create assign code
        either:
        IASN ID EXPR
        or:
        RASN ID EXPR
        '''
        id_type = self.get_from_symbol_table(p.ID)
        if id_type != p.expression.type:
            err = f"can't assign {p.expression.val} of type {p.expression.type} into {p.ID} of type {id_type}"
            self.semantic_error(err)
        self.gen(f'{types.get(id_type)}ASN {p.ID} {p.expression.val}')
    
    @_('INPUT "(" ID ")" ";"')
    def input_stmt(self, p):
        self.lineno = p.lineno
        type = self.get_from_symbol_table(p.ID)
        self.gen(f'{types.get(type)}INP {p.ID}')
    
    @_('OUTPUT "(" expression ")" ";"')
    def output_stmt(self, p):
        self.lineno = p.lineno
        self.gen(f'{types.get(p.expression.type)}PRT {p.expression.val}')
    
    @_('IF "(" boolexpr ")" jump_if_false stmt jump_to_end ELSE false_label stmt')
    def if_stmt(self, p):
        self.lineno = p.lineno
        continue_label = p.jump_to_end
        self.gen_label(continue_label)
    
    @_('WHILE label "(" boolexpr ")" jump_if_false stmt')
    def while_stmt(self, p):
        self.lineno = p.lineno
        while_label = p.label
        continue_label = p.jump_if_false
        self.gen_jump_to_label(while_label)
        self.gen_label(continue_label)
       
    @_('')
    def jump_if_false(self, p):
        jump_label = self.get_label()
        self.gen_cond_jump(jump_label, p[-2].val)
        return jump_label
    
    @_('')
    def jump_to_end(self, p):
        end_label = self.get_label()
        self.gen_jump_to_label(end_label)
        return end_label
    
    @_('')
    def false_label(self, p):
        self.gen_label(p[-4])
    
    @_('')
    def label(self, p):
        label = self.get_label()
        self.gen_label(label)
        return label
       
    @_('"{" stmtlist "}"')
    def stmt_block(self, p):
        pass
       
    @_('stmtlist stmt',
       'empty')
    def stmtlist(self, p):
        pass
       
    @_('boolexpr OR boolterm')
    def boolexpr(self, p):
        self.lineno = p.lineno
        temp = self.get_temp()
        type = self.get_type(p.boolexpr.type, p.boolterm.type)
        converted_operands = self.get_converted_operands(p.boolexpr, p.boolterm)
        self.generate_three_adress_code(type, '+', [temp] + [ operand.val for operand in converted_operands ])
        self.generate_three_adress_code(type, '>', [temp, temp, self._ZERO])
        return temp
       
    @_('boolterm')
    def boolexpr(self, p):
        self.lineno = p.lineno
        return p.boolterm
       
    @_('boolterm AND boolfactor')
    def boolterm(self, p):
        self.lineno = p.lineno
        temp = self.get_temp()
        type = self.get_type(p.boolterm.type, p.boolfactor.type)
        converted_operands = self.get_converted_operands(p.boolterm, p.boolfactor)
        self.generate_three_adress_code(type, '+', [temp] + [ operand.val for operand in converted_operands ])
        self.generate_three_adress_code(type, '==', [temp, temp, self._TWO])
        return temp
              
    @_('boolfactor')
    def boolterm(self, p):
        self.lineno = p.lineno
        return p.boolfactor
       
    @_('NOT "(" boolexpr ")"')
    def boolfactor(self, p):
        self.lineno = p.lineno
        return self.three_adress_code('!=', [p.boolexpr, self._ONE])
              
    @_('expression RELOP expression')
    def boolfactor(self, p):
        self.lineno = p.lineno
        opcode = ops.get(p.RELOP)
        temp =self.get_temp()
        type = self.get_type(p.expression0.type, p.expression1.type)
        converted_operands = self.get_converted_operands(type, [p.expression0, p.expression1])
        operands_list = [ operand.val for operand in converted_operands ]
        if not opcode:
            temp2 = self.get_temp()
            self.generate_three_adress_code(type, p.RELOP[0], [temp] + operands_list)
            self.generate_three_adress_code(type, p.RELOP[1], [temp2] + operands_list)
            self.generate_three_adress_code(type, '+', [temp, temp, temp2])
        else:
            self.generate_three_adress_code(type, p.RELOP, [temp] + operands_list)
        return self.NeedsAName(temp, _INT)
       
    @_('expression ADDOP term')
    def expression(self, p):
        self.lineno = p.lineno
        return self.three_adress_code(p.ADDOP, [p.expression, p.term])
    
    @_('term')
    def expression(self, p):
        self.lineno = p.lineno
        return p.term
       
    @_('term MULOP factor')
    def term(self, p):
        self.lineno = p.lineno
        return self.three_adress_code(p.MULOP, [p.term, p.factor])
    
    @_('factor')
    def term(self, p):
        self.lineno = p.lineno
        return p.factor
       
    @_('"(" expression ")"')
    def factor(self, p):
        self.lineno = p.lineno
        return p.expression

    @_('CAST "(" expression ")"')
    def factor(self, p):
        self.lineno = p.lineno
        return self.convert_type(p.CAST[1], p.expression.val)

    @_('ID')
    def factor(self, p):
        self.lineno = p.lineno
        return self.NeedsAName(p.ID, self.get_from_symbol_table(p.ID))
    
    @_('NUM')
    def factor(self, p):
        self.lineno = p.lineno
        return self.NeedsAName(p.NUM, _FLOAT if '.' in p.NUM else _INT)

# Usage example:
if __name__ == '__main__':
    lexer = CPQLexer()
    parser = CPQParser()
    
    data = '''
k, j: int;
{
    while (k <= 10)
        if (j > 5)
            k = k + 2;
        else
            k = 20;
}
    '''
    
    result = parser.parse(lexer.tokenize(data))
    print("------result------")
    print(result)
    print("---symbol table---")
    print(parser.symbol_table)
    print("-----quad code-----")
    print(parser.quad_code)
    print("-----quad code-----")
    print("\n".join(parser.quad_code))
