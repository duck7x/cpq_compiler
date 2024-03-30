import sys
from cpq_lexer import CPQLexer
from cpq_parser import CPQParser

# TODO: send errors to the stderr 
def ensure_input():
    if len(sys.argv) == 1:
        print("CRITICAL: no file was given, nothing to do!", file=sys.stderr)
    if len(sys.argv) > 2:
        print("CRITICAL: too many arguments, nothing to do!", file=sys.stderr)
    if sys.argv[1].split(".")[-1] != "ou":
        print("CRITICAL: wrong file type, nothing to do!", file=sys.stderr)

# TODO: ensure errors in code include the line of the error
def main():
    
    # TODO: Add signature to the stderr
    ensure_input()
    
    # TODO: ensure file exists and all good
    code_to_translate = ''  # TODO: get it from file
    
    # TODO: Lexical Analyzer
    tokens = CPQLexer().tokenize(code_to_translate)
    # TODO: Parser
    translated_code = CPQParser().parse(tokens)
    # TODO: Syntax Analyzer(?)
    
    # TODO: if no errors, create qud file
    # TODO: IR generator
    
    # TODO: Add signature to the quad file after the last HALT command
    

if __name__ == "__main__":
    main()