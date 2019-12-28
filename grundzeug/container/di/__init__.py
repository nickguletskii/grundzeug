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

import warnings

from grundzeug.container.di.common import *
from grundzeug.container.di.injection import *
from grundzeug.container.di.aliases import *

import grundzeug.container.di.default

typing_extensions_found = False
try:
    import typing_extensions

    typing_extensions_found = True
except ImportError:
    warnings.warn("typing_extensions is not installed. Please install it in order to use typing-based injection.")

if typing_extensions_found:
    if hasattr(typing_extensions, "HAVE_ANNOTATED"):
        if typing_extensions.HAVE_ANNOTATED:
            import grundzeug.container.di.annotated
        else:
            warnings.warn("Can't enable typing-based injection because typing_extensions.HAVE_ANNOTATED is False.")
    else:
        warnings.warn("The currently installed version of typing_extensions does not expose HAVE_ANNOTATED. Please "
                      "ensure that all packages are up to date.")
