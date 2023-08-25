import os
from types import ModuleType
from typing import Optional


def get_content_of(file: str) -> Optional[str]:
    """
    Returns the content of the given file.
    :param file: File to read, absolute path
    :return: Content of the given file
    """
    if not os.path.isfile(file):
        return None
    with open(file, "r", encoding="utf-8") as f:
        return f.read()


def execute_arbitrary_code(
    code: str, method: str, module_name: str = "module"
) -> None:
    """
    Executes the given code. This is a security risk, so use with caution.
    :param code: Code to execute
    :param method: Method to call
    :param module_name: Name of the module
    """
    # https://stackoverflow.com/a/19850183
    compiled = compile(code, "", "exec")
    module = ModuleType(module_name)
    function = get_attr(module, method)
    exec(compiled, module.__dict__)
    function()
