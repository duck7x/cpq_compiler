import sys
import os
from cpq_lexer import CPQLexer
from cpq_parser import CPQParser

def handle_error(error):
    print(f'CRITICAL: {error}, exiting cpq!', file=sys.stderr)
    
def ensure_input():
    
    if len(sys.argv) == 1:
        handle_error("no file was given")
        return
    
    if len(sys.argv) > 2:
        handle_error("too many arguments")
        return
    
    if sys.argv[1].split(".")[-1] != "ou":
        handle_error("wrong file type")
        return
    
    if os.path.exists(f'{sys.argv[1].split(".")[0]}.qud'):
        handle_error("output file already exists")
        return
    
    if not os.path.exists(sys.argv[1]):
        handle_error("input file doesn't exist")
        return
    
    return True

# TODO: ensure errors in code include the line of the error
def main():
    
    print("Efrat Elisha :)", file=sys.stderr)
    
    if not ensure_input():
        return
    
    input_file_name = sys.argv[1]
    # input_file_name = "test1.ou"
    ouput_file_name = f'{input_file_name.split(".")[0]}.qud'
    
    with open(input_file_name, 'r') as file:    
        code_to_translate = file.read()
    
    lexer = CPQLexer()
    tokens = lexer.tokenize(code_to_translate)
    # print(f'DEBUG: {tokens}')
    # return
    parser = CPQParser()
    translated_code = parser.parse(tokens)
    
    translated_code.append('Efrat Elisha :)')
    
    if lexer.found_errors or parser.found_errors:
        handle_error('Encountered errors during complication')
        return
    
    with open(ouput_file_name, 'w') as file:
        file.write('\n'.join(translated_code))
    

if __name__ == "__main__":
    main()