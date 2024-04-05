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


    def raise_warning(self, error):
        """
        Handles a warning by using the print_error function with WARNING severity
        Does not adjust the found_errors variable, as this is only a warning and does not prevent compilation.
        """

        print_error(error, line=self.lineno, severity="WARNING")


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

        This function does not return a value since it does not provide any information for further parsing.
        """

        pass
    

    @_('declarations stmt_block')
    def program(self, p):
        """
        The starting symbol, represents the whole program

        Returns the list which represents the entire quad code
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

        This function does not return a value since it does not provide any information for further parsing.
        """

        pass
    

    @_('idlist ":" type_ ";"')
    def declaration(self, p):
        """
        Declaration grammer rule
        Consists of a list of ID names and their type
        Here we add the IDs to the symbol table

        Returns the symbol table
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

        Returns the list of IDs
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

        Returns the newly created list
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
        
        This function does not return a value since it does not provide any information for further parsing.
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
    

    @_('INPUT "(" ID ")" ";"')
    def input_stmt(self, p):
        """
        Input_stmt grammer rule
        Makes sure that the given ID is in the symbol table
        Then generates the code for reading a real or an integer (based on the ID type) into the ID
        
        This function does not return a value since it does not provide any information for further parsing.
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Get the ID type from the symbol table
        # If the ID is not in the symbol table, the get_from_symbol_table function will raise an error
        # The get_from_symbol_table defaults to float type in case of an error,
        # So that if indeed an error was encountered, we can continue with the parsing without any issues
        type_ = self.get_from_symbol_table(p.ID)

        # Generate the code for reading the input into the given ID
        self.gen(f'{types.get(type_)}INP {p.ID}')
    

    @_('OUTPUT "(" expression ")" ";"')
    def output_stmt(self, p):
        """
        Output_stmt grammer rule
        Generates the code for pritning the value of the given expression, based on the expression type.
        
        This function does not return a value since it does not provide any information for further parsing.
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Generates the code for printing the given expression
        self.gen(f'{types.get(p.expression.type)}PRT {p.expression.val}')
    

    @_('IF "(" boolexpr ")" jump_if_false stmt jump_to_end ELSE false_label stmt')
    def if_stmt(self, p):
        """
        If_stmt grammer rule
        With the help of all non-terminals in the rule, the entire if statement code will be generated.
        Firstly, boolexpr will store the boolexpr value(/location).
        Secondly, jump_if_false will create a label for the false else statement.
            Additionally, jump_if_false will generate a conditional jump to that label, based on boolexpr's value.
        During each stmt, the relevant code of the stmt will be generated (at the right time).
        Afterwards, jump_to_end will generate a label for the end of the entire if statement,
            As well as create an uncoditional jump for it
        Then, false_label will generate the label that was created in jump_if_false, right before the else stmt.
        Lastly, once the entire rule has been read, we will generate the label created by jump_to_end.

        This function does not return a value since it does not provide any information for further parsing.
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Get the label created by jump_to_end
        continue_label = p.jump_to_end

        # Generate the label to anchor the end of the entire if statement
        self.gen_label(continue_label)
    

    @_('WHILE label "(" boolexpr ")" jump_if_false stmt')
    def while_stmt(self, p):
        """
        While_stmt grammer rule
        With the help of all non-terminals inm the rule, the entire while statement code will be generated.
        Firstly, label will create a new label and generate the code for it, to anchor the while condition.
        Secondly, boolexpr will generate the evaluation of the while expression.
        Afterwards, jump_if_false will create a new label which will be used as an anchor for the end of the while,
            And jump_if_false will generate a conditional jump to that label as an exit from the while statement.
        Then, stmt will generate the code for the while loop content.
        Lastly, once the entire rule has been read, we will generate an unconditional jump back to the while condition
            Also, the label that anchors the end of the while will be generated.

        This function does not return a value since it does not provide any information for further parsing.
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Get the labels that were created by label and jump_if_false
        while_label = p.label
        continue_label = p.jump_if_false

        # Generate an unconditional jump back to the while condition
        self.gen_jump_to_label(while_label)

        # Generate the label to anchor the end of the entire while statement
        self.gen_label(continue_label)
       

    @_('')
    def jump_if_false(self, p):
        """
        This is used to create a "jump if false" sort of condition.
        The function assumes that the second symbol to its left is an Operand object on which the jump will be based.
        The function will create a new label (used for the jump), then generate the conditional jump code.
        
        Returns the created label for further use of the parser (assuming the rule that called this function,
            will later generate the label at the right place in the code)
        """

        # Create a new label to which the jump will refer
        jump_label = self.get_label()

        # Generate a conditiona jump to the created label, based on the value of the second symbol to the left
        self.gen_cond_jump(jump_label, p[-2].val)

        # Return the created label for further use of the parser
        return jump_label
    

    @_('')
    def jump_to_end(self, p):
        """
        This is used to create an unconditional jump to a label that represents the end of a bit of code.
        Used for loops and conditions (such as if).
        
        Returns the created label for further use of the parser (assuming the rule that called this function,
            will later generate the label at the right place in the code)
        """

        # Create a new label to which the jump will refer
        end_label = self.get_label()

        # Generate the unconditional jump to the created label
        self.gen_jump_to_label(end_label)

        # Return the created label for further use of the parser
        return end_label
    

    @_('')
    def false_label(self, p):
        """
        Generates a label from the fourth symbol to the left
        This is used for the else bit of an if statement
        
        This function does not return a value since it does not provide any information for further parsing.
        """

        # Generate the label based on the fourth symbol to the left
        self.gen_label(p[-4])
    

    @_('')
    def label(self, p):
        """
        This is used to create and generate a new label
        
        Returns the newly created label for further use of the parser
        """

        # Create a new label
        label = self.get_label()

        # Generate the newly created label
        self.gen_label(label)

        # Return the created label for further use of the parser
        return label
       

    @_('"{" stmtlist "}"')
    def stmt_block(self, p):
        """
        Stmt_block grammer rule
        Nothing should be done here

        This function does not return a value since it does not provide any information for further parsing.
        """

        pass
       

    @_('stmtlist stmt',
       'empty')
    def stmtlist(self, p):
        """
        Stmtlist grammer rule
        Nothing should be done here

        This function does not return a value since it does not provide any information for further parsing.
        """

        pass
       

    @_('boolexpr OR boolterm')
    def boolexpr(self, p):
        """
        Boolexpr grammer rule for an OR expression
        
        The expression is evaluated by adding the values of the given boolexpr and boolterm
        If the value of the addition is greater than 0, then at least one of them is true
        Otherwise, both of them are false and thus the OR expression is also false
        
        Returns a temp in which the result of the OR is stored
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Create a new temp to store the result of the bool expression in
        temp = self.get_temp()

        # Check for the type of the boolean expression
        type_ = self.get_type(p.boolexpr.type, p.boolterm.type)

        # Convert the operands, if needed
        converted_operands = self.get_converted_operands(type_, [p.boolexpr, p.boolterm])

        # Generates the three address code for adding both operands
        self.generate_three_adress_code(type_, '+', [temp] + [ operand.val for operand in converted_operands ])

        # Generates the three address code for comparing the result of the operands' addition to the constant zero
        self.generate_three_adress_code(type_, '>', [temp, temp, self._ZERO])

        # Returns the temp in which the result of the boolean expression is stored
        return temp
       

    @_('boolterm')
    def boolexpr(self, p):
        """
        Boolexpr grammer rule for a single boolterm

        Returns the boolterm itself
        """

        # Sets the current line number
        self.lineno = p.lineno
        
        return p.boolterm
       

    @_('boolterm AND boolfactor')
    def boolterm(self, p):
        """
        Boolterm grammer rule for an AND term
        
        The term is evaluated by adding the values of the given boolterm and boolfactor
        If the value of the addition is exactly 2, then both of them are true
        Otherwise, at least one of them is false and thus the AND term is also false
        
        Returns a temp in which the result of the AND is stored
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Create a new temp to store the result of the bool term in
        temp = self.get_temp()

        # Check for the type of the boolean term
        type_ = self.get_type(p.boolterm.type, p.boolfactor.type)

        # Convert the operands, if needed
        converted_operands = self.get_converted_operands(type_, [p.boolterm, p.boolfactor])

        # Generates the three address code for adding both operands
        self.generate_three_adress_code(type_, '+', [temp] + [ operand.val for operand in converted_operands ])

        # Generates the three address code for comparing the result of the operands' addition to the constant two
        self.generate_three_adress_code(type_, '==', [temp, temp, self._TWO])

        # Returns the temp in which the result of the boolean term is stored
        return temp


    @_('boolfactor')
    def boolterm(self, p):
        """
        Boolterm grammer rule for a single boolfactor

        Returns the boolfactor itself
        """

        # Sets the current line number
        self.lineno = p.lineno

        return p.boolfactor
       

    @_('NOT "(" boolexpr ")"')
    def boolfactor(self, p):
        """
        Boolfactor grammer rule for a NOT expression
        
        Uses the three_address_code function to generate a != operation
        
        Returns the Operand object which is returned from the three_address_code function
        """

        # Sets the current line number
        self.lineno = p.lineno
        
        # Generate the three address code for the != operation and return the result
        return self.three_address_code('!=', [p.boolexpr, self._ONE])


    @_('expression RELOP expression')
    def boolfactor(self, p):
        """
        Boolfactor grammer rule for a RELOP expression

        In most cases, the code can be generated by getting the opcode for the RELOP from the ops dict
            And using the generate_three_adress_code function to generate the relevant operation
        In the case of a two-part RELOP (such as >=), each of the operations need to be done seperately
            And then the results of both operations should be combined to the final result

        Returns a temp in whch the result of the RELOP is stored
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Get the opcode of the given RELOP from the dict of operations
        opcode = ops.get(p.RELOP)

        # Create a new temp to store the result of the RELOP in
        temp =self.get_temp()

        # Get the expected type of the operation
        type_ = self.get_type(p.expression0.type, p.expression1.type)

        # Convert the operands, if needed
        converted_operands = self.get_converted_operands(type_, [p.expression0, p.expression1])

        # A list of the operand values
        operands_list = [ operand.val for operand in converted_operands ]

        # If the RELOP is not in the ops dictionary, it means it's a RELOP/EQUAL sort of operation
        # In such case, we handle the specific case using an additional temp and an add operation
        # Otherwise (else), this is a typical RELOP which can be generated in a more general way as done in the else bit
        if not opcode:
            temp2 = self.get_temp()
            self.generate_three_adress_code(type_, p.RELOP[0], [temp] + operands_list)
            self.generate_three_adress_code(type_, p.RELOP[1], [temp2] + operands_list)
            self.generate_three_adress_code(type_, '+', [temp, temp, temp2])
        else:
            self.generate_three_adress_code(type_, p.RELOP, [temp] + operands_list)

        # Return the temp in which the result of the RELOP is stored
        return self.Operand(temp, _INT)
       

    @_('expression ADDOP term')
    def expression(self, p):
        """
        Expression grammer rule for an ADDOP operation

        Uses the three_address_code function to generate the relevant ADDOP operation

        Returns the Operand object which is returned from the three_address_code function
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Generate the three address code for the ADDOP operation and return the result
        return self.three_address_code(p.ADDOP, [p.expression, p.term])
    

    @_('term')
    def expression(self, p):
        """
        Expression grammer rule for a single term

        Returns the term itself
        """

        # Sets the current line number
        self.lineno = p.lineno

        return p.term
       

    @_('term MULOP factor')
    def term(self, p):
        """
        Term grammer rule for a MULOP operation

        Uses the three_address_code function to generate the relevant MULOP operation

        Returns the Operand object which is returned from the three_address_code function
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Generate the three address code for the MULOP operation and return the result
        return self.three_address_code(p.MULOP, [p.term, p.factor])
    

    @_('factor')
    def term(self, p):
        """
        Term grammer rule for a single term

        Returns the factor itself
        """

        # Sets the current line number
        self.lineno = p.lineno

        return p.factor
       

    @_('"(" expression ")"')
    def factor(self, p):
        """
        Factor grammer rule for a single expression

        Returns the expression itself
        """

        # Sets the current line number
        self.lineno = p.lineno

        return p.expression


# CONTINUE DOCUMENTING FROM HERE
    @_('CAST "(" expression ")"')
    def factor(self, p):
        """
        Factor grammer rule for CAST action

        If the target type and the expression type are different
            The convert_type function will be called for generating the casting code.
        Otherwise, a warning will be raised and the return value will be expression itself.

        Returns the temp in which the converted expression is stored in case of a conversion,
            Or the original expression if no conversion was done.
        """

        # Sets the current line number
        self.lineno = p.lineno
        
        target_type = p.CAST[1]
        
        # Check if a conversion is requried
        if target_type == p.expression.type:
            self.raise_warning(f"{target_type} casting of {p.expression.type} operand ({p.expression.val})")
            return p.expression
        else:
            # Generate the code for converting the expression and return the temp in which the coversion is stored
            return self.convert_type(p.CAST[1], p.expression.val)


    @_('ID')
    def factor(self, p):
        """
        Factor grammer rule for an ID

        Returns an Operand object of the given ID based on symbol table
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Return an Operand object of the given ID and its type in the symbol table
        # If the ID is not in the symbol table, the get_from_symbol_table function will raise an error for it
        return self.Operand(p.ID, self.get_from_symbol_table(p.ID))
    

    @_('NUM')
    def factor(self, p):
        """
        Factor grammer rule for a number

        Returns an Operand ibject of the given number with the matching type
        """

        # Sets the current line number
        self.lineno = p.lineno

        # Return an Operand object of the given number and its matching type
        return self.Operand(p.NUM, _FLOAT if '.' in p.NUM else _INT)
