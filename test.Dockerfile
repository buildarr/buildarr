# test.Dockerfile
# Buildarr Docker image for testing within a container.
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

FROM python:3.11-alpine

# Version of Buildarr and vendored plugins to install in the Docker container.
ARG BUILDARR_SONARR_VERSION="0.4.1"
ARG BUILDARR_PROWLARR_VERSION="0.1.1"

# Ensure stdout/stderr writes straight through to the Docker logs without buffering.
ENV PYTHONUNBUFFERED=1

# Buildarr user UID/GID. User is created at runtime.
ENV PUID=1000
ENV PGID=1000

# Packages to install into the Python environment on runtime, in a space-separated list.
# Intended to be used for installing Buildarr plugins on startup.
ENV BUILDARR_INSTALL_PACKAGES=

# Mark the Buildarr configuration folder as an external volume mount point.
VOLUME ["/config"]

# Copy the container bootstrap script into the image.
COPY --chown=root:root . /src

# Run the image setup script.
RUN apk add su-exec tzdata && \
    cp /src/scripts/bootstrap.sh /bootstrap.sh && \
    echo "export BUILDARR_SONARR_VERSION=\${BUILDARR_SONARR_VERISON:-${BUILDARR_SONARR_VERSION}}" >> /versions.sh && \
    echo "export BUILDARR_PROWLARR_VERSION=\${BUILDARR_PROWLARR_VERISON:-${BUILDARR_PROWLARR_VERSION}}" >> /versions.sh && \
    chmod +x /bootstrap.sh /versions.sh && \
    python -m pip install --no-cache-dir -e "/src" \
                                         "buildarr-sonarr==${BUILDARR_SONARR_VERSION}" \
                                         "buildarr-prowlarr==${BUILDARR_PROWLARR_VERSION}"

# Set the Buildarr configuration folder as the default Docker container working folder.
WORKDIR /config

# Setup the Docker image entry point to bootstrap packages and start Buildarr daemon.
ENTRYPOINT ["/bootstrap.sh"]
CMD ["daemon"]
