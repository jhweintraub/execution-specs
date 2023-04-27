import json
import os
from typing import Any, Dict, List

import pytest

from ethereum.base_types import U64, U256, Uint
from ethereum.utils.hexadecimal import (
    Hash32,
    hex_to_bytes,
    hex_to_u256,
    hex_to_uint,
)
from ethereum.rlp import decode
from ethereum_spec_tools.evm_tools import parser, subparsers
from ethereum_spec_tools.evm_tools.b11r import B11R, b11r_arguments
from ethereum_spec_tools.evm_tools.utils import FatalException
from tests.helpers import TEST_FIXTURES

B11R_TEST_PATH = TEST_FIXTURES["evm_tools_testdata"]["fixture_path"]

ignore_tests = []


def find_test_fixtures() -> Any:
    with open(os.path.join(B11R_TEST_PATH, "b11r_commands.json")) as f:
        data = json.load(f)

    for key, value in data.items():

        final_args = []
        for arg in value["args"]:
            if "__BASEDIR__" in arg:
                final_args.append(arg.replace("__BASEDIR__", B11R_TEST_PATH))
            else:
                final_args.append(arg)
        # if key == "b11r/fixtures/expected/22/exp.json":
        yield {
            "name": key,
            "args": final_args,
            "expected": os.path.join(B11R_TEST_PATH, key),
            "success": value["success"],
        }


def idfn(test_case: Dict) -> str:
    return test_case["name"]


def get_rejected_indices(rejected: Dict) -> List[int]:
    rejected_indices = []
    for item in rejected:
        rejected_indices.append(item["index"])
    return rejected_indices

def to_hex(decoded_rlp) -> Any:
    # TODO: Remove this function after testing
    if isinstance(decoded_rlp, list):
        return [to_hex(item) for item in decoded_rlp]
    elif isinstance(decoded_rlp, bytes):
        return "0x" + decoded_rlp.hex()
    else:
        return "0x" + decoded_rlp.hex()

def b11r_tool_test(test_case: Dict) -> None:
    b11r_arguments(subparsers)
    options = parser.parse_args(test_case["args"])

    try:
        b11r_tool = B11R(options)
        b11r_tool.run()
    except Exception as e:
        raise FatalException(e)

    # json_result = b11r_tool.result.to_json()
    with open(test_case["expected"], "r") as f:
        data = json.load(f)

    assert hex_to_bytes(data["rlp"]) == b11r_tool.block_rlp
    assert hex_to_bytes(data["hash"]) == b11r_tool.block_hash

@pytest.mark.parametrize(
    "test_case",
    find_test_fixtures(),
    ids=idfn,
)
def test_b11r(test_case: Dict) -> None:
    if test_case["name"] in ignore_tests:
        pytest.xfail("Undefined behavior for specs")
    elif test_case["success"]:
        b11r_tool_test(test_case)
    else:
        with pytest.raises(FatalException):
            b11r_tool_test(test_case)
