from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Union, get_args

import pandas as pd
import streamlit as st
from st_keyup import st_keyup

from .. import extra

NoneType = type(None)
UnionType = type(Union[int, float])


@dataclass
class Argument:
    argument: str
    type_hint: Any
    default: Any


def get_arg_details(func) -> list[Argument]:
    try:
        # Python 3.10 added eval_str=True
        signature = inspect.signature(func, eval_str=True)  # type: ignore
    except TypeError:
        signature = inspect.signature(func)
    return [
        Argument(argument=k, type_hint=v.annotation, default=v.default)
        for k, v in signature.parameters.items()
    ]


def is_empty(argument_attribute):
    return argument_attribute is inspect.Parameter.empty


def get_arg_from_session_state(func_name: str, argument: str):
    if func_name in st.session_state:
        if "inputs" in st.session_state[func_name]:
            return st.session_state[func_name]["inputs"][argument]


@extra
def function_explorer(
    func: Callable, default_arguments: Optional[Dict[str, Any]] = None
):
    """Gives a Streamlit UI to any function.

    Args:
        func (callable): Python function
    """

    args = get_arg_details(func)
    inputs: Dict[str, Any] = dict()

    st.write("##### Inputs")
    st.write(
        f"Go ahead and play with `{func.__name__}` parameters, see how"
        " they change the output!"
    )

    for argument_info in args:
        argument = argument_info.argument
        type_hint = argument_info.type_hint
        default = argument_info.default

        label = argument if not is_empty(default) else f"{argument}*"

        if default_arguments and argument in default_arguments:
            default = default_arguments[argument]

        if isinstance(type_hint, UnionType):
            # Replace union types with the second argument being None with the first
            # option
            if len(type_hint.__args__) == 2 and type_hint.__args__[1] == NoneType:  # type: ignore
                type_hint = type_hint.__args__[0]  # type: ignore

        if is_empty(type_hint):
            default = (
                get_arg_from_session_state(func.__name__, argument) or default
                if not is_empty(default)
                else "Sample string"
            )
            inputs[argument] = st.text_input(label, value=default)
        else:
            if hasattr(type_hint, "__name__"):
                label += f" ({type_hint.__name__})"  # type: ignore
            else:
                raise Exception(f"Not sure how to handle {type_hint}")
            if type_hint == int:
                default = get_arg_from_session_state(func.__name__, argument) or (
                    default if not is_empty(default) else 12
                )
                inputs[argument] = st.number_input(label, step=1, value=default)
            elif type_hint == float:
                default = (
                    get_arg_from_session_state(func.__name__, argument) or default
                    if not is_empty(default)
                    else 12.0
                )
                inputs[argument] = st.number_input(label, value=default)
            elif type_hint == str:
                if argument.endswith("_color"):
                    default = (
                        get_arg_from_session_state(func.__name__, argument) or default
                        if not is_empty(default)
                        else "#000000"
                    )
                    inputs[argument] = st.color_picker(label, value=default)
                else:
                    default = (
                        get_arg_from_session_state(func.__name__, argument) or default
                        if not is_empty(default)
                        else "Sample string"
                    )
                    inputs[argument] = st_keyup(label, value=default)
            elif type_hint == bool:
                default = (
                    get_arg_from_session_state(func.__name__, argument) or default
                    if not is_empty(default)
                    else True
                )
                inputs[argument] = st.checkbox(label, value=default)
            elif type_hint == pd.DataFrame:
                inputs[argument] = get_arg_from_session_state(
                    func.__name__, argument
                ) or pd.DataFrame(["abcde"])
            elif str(type_hint).startswith("typing.Literal"):
                options = get_args(type_hint)
                default = (
                    get_arg_from_session_state(func.__name__, argument) or default
                    if not is_empty(default)
                    else options[0]
                )
                idx = options.index(default)
                inputs[argument] = st.selectbox(label, options, index=idx)
            else:
                st.warning(f"`function_explorer` does not support type {type_hint}")

    st.write("##### Output")
    func(**inputs)
    if func.__name__ not in st.session_state:
        st.session_state[func.__name__] = {}
    st.session_state[func.__name__]["inputs"] = inputs


def example():
    def foo(age: int, name: str, image_url: str = "http://placekitten.com/120/120"):
        st.write(f"Hey! My name is {name} and I'm {age} years old")
        st.write("Here's a picture")
        st.image(image_url)

    function_explorer(foo)


__title__ = "Function explorer"
__desc__ = "Give a UI to any Python function! Very alpha though"
__icon__ = "👩‍🚀"
__examples__ = [example]
__author__ = "Arnaud Miribel"
