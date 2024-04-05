from sly import Parser
from cpq_lexer import CPQLexer
from common_functions import print_error

# Constants representing float and int
_FLOAT = 'float'
_INT = 'int'

# Dictionary of types for easier QUAD code creation
types = {
    _FLOAT: 'R',
    _INT: 'I'
}

# Dictionary of operations (and their relevant operand) for easier QUAD code creation
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


# Generator of tX strings where X is a number starting from 1 and raising by 1 each time the generator is called
def temp_generator():
    count = 0
    while True:
        count += 1
        yield f't{count}'


# Generator of LX strings where X is a number starting from 1 and raising by 1 each time the generator is called
def label_generator():
    count = 0
    while True:
        count += 1
        yield f'L{count}'


class CPQParser(Parser):

    # Get the token list from the lexer
    tokens = CPQLexer.tokens

    # Set the starting grammer rule to program
    start = 'program'

    # Instance variable for tracking whether the lexer encountered any errors during its run
    found_errors = False

    # Set symbol table to be an empty dictionary
    symbol_table = dict()

    # Set the generated code to be an empty list
    quad_code = list()

    class Operand():
        """
        An operand object which has a value and a type
        """

        def __init__(self, value, type_):
            self.val = value
            self.type = type_


    # Constants representing the Operand representation of the numbers 0, 1 and 2
    _ZERO = Operand(0, _INT)
    _ONE = Operand(1, _INT)
    _TWO = Operand(2, _INT)


    def gen(self, code):
        """
        Generate code bit - adds the given code to the quad_code generated so far
        """
        self.quad_code.append(code)

    # TODO: test this
    def error(self, token):
        """
        
        """

        print_error(f'unrecognized token {token}', line=token.lineno)
        self.found_errors = True


    def semantic_error(self, error):
        """
        Handle a semantic error by
            Notifying the error using the print_error function
            Setting the found_errors variable to true, to prevent .qod file creation
        """

        print_error(error, line=self.lineno)
        self.found_errors = True


    def get_from_symbol_table(self, symbol):
        """
        Get a symbol from the symbol table
        If the symbol is not in the symbol table, handle the semantic error
        Returns the type of the symbol (fallbacks to float in case the symbol was not in the table)
        """

        type_ = self.symbol_table.get(symbol)

        if type_ is None:
            self.semantic_error(f"{symbol} not in symbol table")

        return type_ or _FLOAT


    def is_in_symbol_table(self, symbol):
        """
        Check whether a symbol is in the symbol table
        Returns True if the symbol is in the symbol table and False if it isn't
        """

        return self.symbol_table.get(symbol) is not None


    def add_to_symbol_table(self, symbol, type_):
        """
        Add a symbol to the symbol table
        If the symbol is already in the symbol table, handle the semantic error 
        """

        if self.is_in_symbol_table(symbol):
            self.semantic_error(f"{symbol} already defined")
            return

        self.symbol_table[symbol] = type_


    # Initiate label generator and temp generator
    _label_generator = label_generator()
    _temp_generator = temp_generator()


    def get_temp(self):
        """
        Generates a new temp every time the function is called
        Ensures the temp is not already in the symbol table.
            If it is, generates a new temp instead (until an unused temp is found)
            
        Returns the name of the unused temp.
        """

        # Get the next item in the temp generator
        temp = next(self._temp_generator)

        # While the current temp is in the symbol table, keep generating new temps
        while self.is_in_symbol_table(temp):
            temp = next(self._temp_generator)

        # Return the first temp that is not in the symbol table
        return temp


    def get_label(self):
        """
        Generates a new label every time the function is called
        
        Returns the name of the new label
        """

        # Get the next item in the label generator and return it
        return next(self._label_generator)


    def gen_label(self, label):
        """
        Generate the code for a given label
        """

        self.gen(f'{label}: ')        


    def gen_jump_to_label(self, label):
        """
        Generate the code for a JUMP command to the given label
        """

        self.gen(f'JUMP {label}')


    def gen_cond_jump(self, label, cond):
        """
        Generate the code for a conditional jump to the given label based on a given condition
        """

        self.gen(f'JMPZ {label} {cond}')


    def get_type(self, first, second):
        """
        Returns the type required for an operation of operands of the two given types
        """

        return first if first == second else _FLOAT


    def convert_type(self, type_, val):
        """
        Gets a value and a type, converts the given value to the given type assuming it was the opposite type.
        The conversion includes generating the required QUAD code for conversion
        Returns an Operand object with the value of the created temp where the converted value is stored
        """

        temp = self.get_temp()
        opcode = 'ITOR' if type_ == _FLOAT else 'RTOI'
        self.gen(' '.join([opcode, temp, val]))
        return self.Operand(temp, type_)


    def get_converted_operands(self, type_, operands_list):
        """
        Gets a list of Operand objects and a target type
        Returns a list of Operand objects based on the given list, where all operands are of the target type
        If an Operand in the original list is not of the desired type, it will be converted to the target type.
        The returned list will be in the same order as the given list.
        """

        converted_operands = list()

        # Go through all items of operands_list
        for operand in operands_list:
            # If the operand is not of the desired type, convert it. Otherwise, add it to the new list as is
            if operand.type_ != type_:
                converted_operands.append(self.convert_type(type_, operand.val))
            else:
                converted_operands.append(operand)

        return converted_operands


    def generate_three_adress_code(self, type_, op, operands):
        """
        Gets a type, and operation and a list of operands
        Generates the relevant QUAD code based on the types dict and the ops dict
        """

        self.gen(f'{types.get(type_)}{ops.get(op)} {" ".join(operands)}')


    def three_address_code(self, opcode, operands):
        """
        Gets an opcode and a list of Operands
        Generates the three address code to execture this opcode on the given operands
        Also takes into account (and converts, if needed) the operand types
        Returns the temp where the operation result is stored
        
        This is used specifically for operations on exactly two opearands, where the third (first) operand is a new temp
        """

        # Create a temp to store the result in
        temp = self.get_temp()

        # Get the type that's required for the operation
        type_ = self.get_type(*[ operand.type_ for operand in operands ])

        # Convert the operands, if needed
        converted_operands = self.get_converted_operands(type_, operands)

        # Generate a list of all three operand values, where temp is the first of the list
        all_operands_list = [temp] + [ operand.val for operand in converted_operands ]

        # Generate the three address code
        self.generate_three_adress_code(type_, opcode, all_operands_list)

        # Return an Operand object of the newly created temp
        return self.Operand(temp, type_)


    # Grammer rules and actions

    @_('')
    def empty(self, p):
        """
        represents epsilon
        """

        pass
    

    @_('declarations stmt_block')
    def program(self, p):
        """
        The starting symbol, represents the whole program
        """

        # Sets the current line number
        self.lineno = p.lineno

        # adds a HALT command at the end of the code
        self.gen('HALT')

        # returns the generated code
        return self.quad_code
    

    @_('declarations declaration',
       'empty')
    def declarations(self, p):
        """
        Declerations grammer rule
        Nothing should be done here
        """

        pass
    

    @_('idlist ":" type_ ";"')
    def declaration(self, p):
        """
        Declaration grammer rule
        Consists of a list of ID names and their type
        Here we add the IDs to the symbol table
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Go through the list of IDs and add them to the symbol table
        # If an ID is already in the symbol table, the add_to_symbol_table function will raise an error for it
        for id in p.idlist:
            self.add_to_symbol_table(id, p.type_)

        return self.symbol_table
        

    @_('INT',
       'FLOAT')
    def type_(self, p):
        """
        Type grammer rule
        The name includes a trailing underscore to avoid shadowing python's built in type method
        Returns the type value
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Returns the first item in the rule, which in this case is the terminal for the type used
        return p[0]
    

    @_('idlist "," ID')
    def idlist(self, p):
        """
        Idlist grammer rule for adding ID to an IDlist without closing the list
        Gets a list of IDs and a new ID, adds the new ID to the given list
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Add the new ID to the list of IDs
        p.idlist.append(p.ID)

        # Returns the list of IDs (which includes the newly added ID)
        return p.idlist
    

    @_('ID')
    def idlist(self, p):
        """
        Idlist grammer rule for adding the "final" ID in the list
        This actually acts the first ID, as it creates a list consisting of this ID only
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Return the ID consisting of a single item - the given ID
        return [p.ID]
    

    @_('assignment_stmt',
       'input_stmt',
       'output_stmt',
       'if_stmt',
       'while_stmt',
       'stmt_block')
    def stmt(self, p):
        """
        Stmt grammer rule
        Nothing should be done here
        """

        pass
    

    @_('ID "=" expression ";"')
    def assignment_stmt(self, p):
        """
        Assignment_stmt gramemr rule
        Generates the code the assignment, in case the assignment is valid.
        If the assignment is invalid, will raise a semantic error.
            Ensures the ID is in the symbol table using the get_from_symbol_table function
            Ensures the ID and the expression are of compatible types
        If the assignment requires casting, this will be taken care of.
        
        This function does not return a value since it does not provide any information for further parsing.
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Get the ID type from the symbol table
        # If the ID is not in the symbol table, the get_from_symbol_table function will raise an error
        # The get_from_symbol_table defaults to float type in case of an error, which is compatible with all types
        # So that if indeed an error was encountered, we can continue with the parsing without any issues
        id_type = self.get_from_symbol_table(p.ID)
        
        # Ensure the given ID and given expression are of compatible type
        if id_type != p.expression.type and id_type != _FLOAT:
            err = f"can't assign {p.expression.val} of type {p.expression.type} into {p.ID} of type {id_type}"
            self.semantic_error(err)

        # Get an Operand object of the expression with the required type
        # If the expression need conversion
        #   get_converted_operands will handle it and return a temp containing the converted data
        # If no converstion is required,
        #   get_converted_operands will return the original Operand object
        # Either way, get_converted_operands returns a list, from which we only need the first (and only) item
        converted_expression = self.get_converted_operands(id_type, [p.expression])[0]

        # Generate the code for assigning the (converted) expression to the given ID.
        self.gen(f'{types.get(id_type)}ASN {p.ID} {converted_expression.val}')
    

# CONTINUE DOCUMENTING FROM HERE
    @_('INPUT "(" ID ")" ";"')
    def input_stmt(self, p):
        """
        Input_stmt grammer rule
        
        
        This function does not return a value since it does not provide any information for further parsing.
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Get the ID type from the symbol table
        # If the ID is not in the symbol table, the get_from_symbol_table function will raise an error
        # The get_from_symbol_table defaults to float type in case of an error,
        # So that if indeed an error was encountered, we can continue with the parsing without any issues
        type_ = self.get_from_symbol_table(p.ID)

        
        self.gen(f'{types.get(type_)}INP {p.ID}')
    

    @_('OUTPUT "(" expression ")" ";"')
    def output_stmt(self, p):
        """
        Output_stmt grammer rule
        
        
        This function does not return a value since it does not provide any information for further parsing.
        """

        # Sets the current line number
        self.lineno = p.lineno

        # 
        self.gen(f'{types.get(p.expression.type)}PRT {p.expression.val}')
    

    @_('IF "(" boolexpr ")" jump_if_false stmt jump_to_end ELSE false_label stmt')
    def if_stmt(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno

        # 
        continue_label = p.jump_to_end

        # 
        self.gen_label(continue_label)
    

    @_('WHILE label "(" boolexpr ")" jump_if_false stmt')
    def while_stmt(self, p):
        """
        
        """

        # Sets the current line number
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
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        temp = self.get_temp()
        type_ = self.get_type(p.boolexpr.type, p.boolterm.type)
        converted_operands = self.get_converted_operands(p.boolexpr, p.boolterm)
        self.generate_three_adress_code(type_, '+', [temp] + [ operand.val for operand in converted_operands ])
        self.generate_three_adress_code(type_, '>', [temp, temp, self._ZERO])
        return temp
       

    @_('boolterm')
    def boolexpr(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return p.boolterm
       

    @_('boolterm AND boolfactor')
    def boolterm(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        temp = self.get_temp()
        type_ = self.get_type(p.boolterm.type, p.boolfactor.type)
        converted_operands = self.get_converted_operands(p.boolterm, p.boolfactor)
        self.generate_three_adress_code(type_, '+', [temp] + [ operand.val for operand in converted_operands ])
        self.generate_three_adress_code(type_, '==', [temp, temp, self._TWO])
        return temp


    @_('boolfactor')
    def boolterm(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return p.boolfactor
       

    @_('NOT "(" boolexpr ")"')
    def boolfactor(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return self.three_address_code('!=', [p.boolexpr, self._ONE])


    @_('expression RELOP expression')
    def boolfactor(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        opcode = ops.get(p.RELOP)
        temp =self.get_temp()
        type_ = self.get_type(p.expression0.type, p.expression1.type)
        converted_operands = self.get_converted_operands(type_, [p.expression0, p.expression1])
        operands_list = [ operand.val for operand in converted_operands ]
        if not opcode:
            temp2 = self.get_temp()
            self.generate_three_adress_code(type_, p.RELOP[0], [temp] + operands_list)
            self.generate_three_adress_code(type_, p.RELOP[1], [temp2] + operands_list)
            self.generate_three_adress_code(type_, '+', [temp, temp, temp2])
        else:
            self.generate_three_adress_code(type_, p.RELOP, [temp] + operands_list)
        return self.Operand(temp, _INT)
       

    @_('expression ADDOP term')
    def expression(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return self.three_address_code(p.ADDOP, [p.expression, p.term])
    

    @_('term')
    def expression(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return p.term
       

    @_('term MULOP factor')
    def term(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return self.three_address_code(p.MULOP, [p.term, p.factor])
    

    @_('factor')
    def term(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return p.factor
       

    @_('"(" expression ")"')
    def factor(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return p.expression


    @_('CAST "(" expression ")"')
    def factor(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return self.convert_type(p.CAST[1], p.expression.val)


    @_('ID')
    def factor(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return self.Operand(p.ID, self.get_from_symbol_table(p.ID))
    

    @_('NUM')
    def factor(self, p):
        """
        
        """

        # Sets the current line number
        self.lineno = p.lineno
        return self.Operand(p.NUM, _FLOAT if '.' in p.NUM else _INT)
