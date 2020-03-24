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
from typing import TypeVar, Type, Tuple

T = TypeVar("T", bound=object)


def make_sentinel() -> Tuple[Type[T], T]:
    """
    Creates a sentinel type and value.

    :return: A tuple, where the first element is the sentinel type, and the second element is the sentinel value.
    """

    class _Sentinel():
        pass

    return _Sentinel, _Sentinel()


__all__ = ["make_sentinel"]
