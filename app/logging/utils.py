import ast
from typing import Any


def ascii_data_display(data: str) -> Any:
    return ast.literal_eval(data)


def get_dict_ascii_tree(items, prepend="", new_line=True):
    new_result = b'\xe2\x94\x9c'.decode()
    new_line = b'\xe2\x94\x80'.decode()
    last_result = b'\xe2\x94\x94'.decode()
    skip_result = b'\xe2\x94\x82'.decode()

    text = ""
    for num, item in enumerate(items):
        box_symbol = (
            new_result +
            new_line if num != len(items) - 1 else last_result + new_line
        )

        if type(item) == tuple:
            field_name, field_value = item
            if field_value.startswith("['"):
                is_last_item = num == len(items) - 1
                prepend_symbols = " " * 3 if is_last_item else f" {skip_result} "
                data = ascii_data_display(field_value)
                field_value = get_dict_ascii_tree(data, prepend_symbols)
            text += f"\n{prepend}{box_symbol}{field_name}: {field_value}"
        else:
            text += f"\n{prepend}{box_symbol} {item}"

    if not new_line:
        text = text[1:]

    return text
