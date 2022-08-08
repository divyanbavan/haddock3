"""Test config reader."""
import os
from datetime import datetime
from math import isnan
from pathlib import Path, PosixPath, WindowsPath

import pytest

from haddock.gear import config_reader


@pytest.mark.parametrize(
    'line,expected',
    [
        ('[header]', 'header'),
        ('[under_scores_work]', 'under_scores_work'),
        ],
    )
def test_main_header_re(line, expected):
    """Test header regex."""
    result = config_reader._main_header_re.match(line)
    assert result[1] == expected


@pytest.mark.parametrize(
    'line,expected,expected2',
    [
        ('[another.header]', 'another', '.header'),
        ('[another.header_2]', 'another', '.header_2'),
        ('[another.header.h3]', 'another', '.header.h3'),
        ],
    )
def test_sub_header_re(line, expected, expected2):
    """Test header regex."""
    group = config_reader._sub_header_re.match(line)
    assert group[1] == expected
    assert group[2] == expected2


@pytest.mark.parametrize(
    'line',
    [
        '[[header]]',
        '[héàder]',
        'value = "some_string"',
        '[header with spaces]',
        '[not.valid]',
        ],
    )
def test_main_header_re_wrong(line):
    """Test main header wrong."""
    assert config_reader._main_header_re.match(line) is None


@pytest.mark.parametrize(
    'line',
    [
        '[[header]]',
        'value = "some_string"',
        '[header with spaces]',
        '[not.valid with spaces]',
        '[single]',
        ],
    )
def test_sub_header_re_wrong(line):
    """Test sub header wrong."""
    assert config_reader._sub_header_re.match(line) is None


@pytest.mark.parametrize(
    'header,name',
    [
        ('header', 'header'),
        ('header.1', 'header'),
        ('header.1.1..1', 'header'),
        ],
    )
def test_get_module_name(header, name):
    """Test get module name."""
    assert config_reader.get_module_name(header) == name


_config_example_1 = """
# some comment
num1 = 10
name="somestring"
w_vdw_1 = 1.0
w_vdw_0 = 0.01
w_vdw_2 = 1.0
[headerone]
name = "theotherstring"
_list = [
    12,
    15,
    ]

[headerone.weights]
val = 1
bsa = 0.1
elec = -1
list1 = [1, 2,3]

[headerone] #some comment
[headerone.weights]
other = 50
"""

_config_example_dict_1 = {
    "num1": 10,
    "name": "somestring",
    "w_vdw_0": 0.01,
    "w_vdw_1": 1.0,
    "w_vdw_2": 1.0,
    "headerone.1": {
        "name": "theotherstring",
        "_list": [12, 15],
        "weights": {
            "val": 1,
            "bsa": 0.1,
            "elec": -1,
            "list1": [1, 2, 3],
            },
        },
    "headerone.2": {'weights': {'other': 50}},
    }

_config_example_2 = """num1 = 10
molecules = ["../some/file", "../some/otherfile"]
[module]
some_path_fname = "./pointing/to/some/path"
[module.d1]
var1 = 1
[module.d1.d2]
var3 = true
list_ = [
    1,
    2,
    3, 4
    ]
"""


_config_example_dict_2 = {
    "num1": 10,
    "molecules": [Path("../some/file"), Path("../some/otherfile")],
    "module": {
        "some_path_fname": Path("pointing", "to", "some", "path"),
        "d1": {
            "var1": 1,
            "d2": {
                "var3": True,
                "list_": [1, 2, 3, 4],
                },
            },
        },
    }

# this examples shows the behaviour of subkey repetition
_config_example_3 = """
val = 1
[header]
[header.d1]
val2 = 10
val3 = 20
"""

_config_example_dict_3 = {
    "val": 1,
    "header": {
        "d1": {
            "val2": 10,
            "val3": 20,
            }
        }
    }


@pytest.mark.parametrize(
    'config,expected',
    [
        (_config_example_1, _config_example_dict_1),
        (_config_example_2, _config_example_dict_2),
        (_config_example_3, _config_example_dict_3),
        ],
    )
def test_load(config, expected):
    """Test read config."""
    r = config_reader.loads(config)
    assert r == expected


def test_load_nan_vlaue():
    """Test read config."""
    r = config_reader.loads("param=nan")
    assert isnan(r["param"])
