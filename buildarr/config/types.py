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
Type hints for Buildarr configuration models.
"""


from __future__ import annotations

from typing import Any, Mapping, Tuple

RemoteMapEntry = Tuple[str, str, Mapping[str, Any]]
"""
Helper type hint for defining parameters for the `remote_map` argument
in some `ConfigBase` attribute handling functions.

It is used as a specification to define how local and remote equivalents
of an attribute should be encoded and decoded.

It is a 3-tuple composed of the following elements:

* `local_attr` (`str`) - the local attribute name
* `remote_attr` (`str`) - the remote attribute name
* `params` (`Mapping[str, Any]`) - option parameters that define how to convert
   between local and remote attributes (for more details, check the handling function)

```python
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from buildarr.config import ConfigBase, RemoteMapEntry

if TYPE_CHECKING:
    from .secrets import ExampleSecrets
    class ExampleConfigBase(ConfigBase[ExampleSecrets]):
        ...
else:
    class ExampleConfigBase(ConfigBase):
        ...

class ExampleConfig(ExampleConfigBase):
    local_attr_1: bool
    local_attr_2: Optional[str] = None

    _remote_map: List[RemoteMapEntry] = [
        ("local_attr_1", "remoteAttr1", {}),
        (
            "local_attr_2",
            "remoteAttr2",
            {
                "is_field": True,
                "decoder": lambda v: v or None,
                "encoder": lambda v: v or "",
            },
        ),
    ]
```
"""
