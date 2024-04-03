import sys

def print_error(err, line=None, severity="ERROR"):
    """
    Prints informative errors (with sevirity and line number) to the stderr.
    """

    error_message = f"{severity}: {err}"

    if line:
        error_message += f" at line {line}"

    print(error_message, file=sys.stderr)
