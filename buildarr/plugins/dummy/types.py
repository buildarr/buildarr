# Copyright (C) 2023 Callum Dickinson
#
# Buildarr is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
#
# Buildarr is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Buildarr.
# If not, see <https://www.gnu.org/licenses/>.


"""
Dummy plugin type hints.
"""


from __future__ import annotations

from typing import Literal

from buildarr.types import Password

DummyApiKey = Password
"""
Constrained string type for a Dummy instance API key.

The type `Password` allows anything as long as it is not an empty string, but is a subclass
of type `pydantic.SecretStr`, allowing Buildarr to hide the value in any logging.

A more complex type for API key might look something like this:

```python
from pydantic import Field, SecretStr
from typing_extensions import Annotated

DummyApiKey = Annotated[SecretStr, Field(min_length=32, max_length=32)]
```
"""

DummyProtocol = Literal["http"]
"""
Allowed protocols for communicating with a Dummy instance.
"""
