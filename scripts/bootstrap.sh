#!/bin/sh
#
# bootstrap.sh
# Run any required pre-install routines, and then start Buildarr as PID 1.
#
# Copyright (C) 2024 Callum Dickinson
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

set -euo pipefail

# Get the installed versions of Buildarr and pre-packaged plugins.
. /versions.sh

# Install packages defined in $BUILDARR_INSTALL_PACKAGES.
# The Buildarr version pin needs to be updated every new release.
if [ -n "$BUILDARR_INSTALL_PACKAGES" ]
then
    echo "Pre-installing the following packages: $BUILDARR_INSTALL_PACKAGES"
    python -m pip install --no-cache-dir -e "/src" \
                                         "buildarr-sonarr==${BUILDARR_SONARR_VERSION}" \
                                         "buildarr-prowlarr==${BUILDARR_PROWLARR_VERSION}" \
                                         $BUILDARR_INSTALL_PACKAGES
fi

# Create the Buildarr user with the configured UID/GID.
deluser buildarr 2> /dev/null || true
delgroup buildarr 2> /dev/null || true
addgroup -S -g $PGID buildarr
adduser -S -s /bin/sh -g buildarr -u $PUID buildarr

# Start Buildarr under the Buildarr user, and replace the bootstrap shell
# with the Buildarr process as PID 1.
exec su-exec buildarr:buildarr buildarr "$@"
