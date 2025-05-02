import re


def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase or camelCase string to snake_case.

    Examples:
        camel_to_snake("CamelCaseExample") ➜ "camel_case_example"
        camel_to_snake("userID") ➜ "user_id"

    Args:
        name (str): String in camelCase or CamelCase format.

    Returns:
        str: Converted snake_case string.
    """
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)  # Handle transition from lower → Upper
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)  # Handle lower or number → Upper
    return name.lower()
