import sys
import os
from cpq_lexer import CPQLexer
from cpq_parser import CPQParser
from common_functions import print_error

INPUT_FILE_SUFFIX = '.ou'
OUTPUT_FILE_SUFFIX = '.qud'


def notifiy_critical_error(error):
    """
    Notifies of a critical error using the print_error function
    """
    
    print_error(f"{error}, not creating {OUTPUT_FILE_SUFFIX} file", severity="CRITICAL")


def ensure_input():
    """
    Ensures that exactly one parameter was given, with the correct format and that the file exists
    Returns None if the input is problematic and True if the input is as expected
    """

    if len(sys.argv) == 1:
        notifiy_critical_error("no file was given")
        return

    if len(sys.argv) > 2:
        notifiy_critical_error("too many arguments")
        return

    if not sys.argv[1].endswith(INPUT_FILE_SUFFIX):
        notifiy_critical_error("wrong file type")
        return

    if os.path.exists(sys.argv[1].replace(INPUT_FILE_SUFFIX, OUTPUT_FILE_SUFFIX)):
        notifiy_critical_error("output file already exists")
        return
    
    if not os.path.exists(sys.argv[1]):
        notifiy_critical_error("input file doesn't exist")
        return
    
    return True


def main():
    """
    CPL to QUAD compiler main function
    """
    
    # Print signature to stderr
    print("Efrat Elisha :)", file=sys.stderr)
    
    # Check input before proceeding to compilation
    if not ensure_input():
        return
    
    input_file_name = sys.argv[1]
    ouput_file_name = input_file_name.replace(INPUT_FILE_SUFFIX, OUTPUT_FILE_SUFFIX)
    
    # Read the contents of the input file
    with open(input_file_name, 'r') as file:    
        code_to_translate = file.read()
    
    # Run the lexer
    lexer = CPQLexer()
    tokens = lexer.tokenize(code_to_translate)
    
    # Run the parser
    parser = CPQParser()
    translated_code = parser.parse(tokens)
    
    # Check for compilation errors before generating .qod file
    if lexer.found_errors or parser.found_errors:
        notifiy_critical_error('Encountered errors during complication')
        return
    
    # Add signature at the end of the QUAD code
    translated_code.append('Efrat Elisha :)')
    
    # Generate .qod file with the QUAD code
    with open(ouput_file_name, 'w') as file:
        file.write('\n'.join(translated_code))
    

if __name__ == "__main__":
    main()