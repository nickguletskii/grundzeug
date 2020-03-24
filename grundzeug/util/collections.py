#  Copyright 2019 Nick Guletskii
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from itertools import zip_longest
from typing import Dict, TypeVar

from grundzeug.util.sentinels import make_sentinel

DictKeyT = TypeVar("DictKeyT")
DictValueT = TypeVar("DictValueT")


def dictionary_union(*dictionaries: Dict[DictKeyT, DictValueT]) -> Dict[DictKeyT, DictValueT]:
    """
    Given an iterable of dictionaries, return the union of these dictionaries.

    :param dictionaries: The dictionaries to combine.
    :return: A dictionary containing the keys present in the input dictionaries.
    """
    return dict(item for dictionary in dictionaries for item in dictionary.items())


_, _SENTINEL = make_sentinel()


def zip_equal(*args):
    """
    Like ``zip``, but throws an error if the number of elements in the iterables are different.
    """
    for i, tup in enumerate(zip_longest(*args, fillvalue=_SENTINEL)):
        tup: tuple = tup
        if _SENTINEL in tup:
            pos = tup.index(_SENTINEL)
            raise ValueError(f"Iterable {pos} only had {i} elements, but the other iterables are longer! Please ensure "
                             f"that all iterables have the same length.")
        yield tup


__all__ = ["dictionary_union", "zip_equal"]
