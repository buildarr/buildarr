# Dockerfile

FROM python:3.11-alpine

#
ENV PYTHONUNBUFFERED=1

#
COPY . /src

#
RUN python -m pip install --no-cache-dir -r /src/requirements.txt /src && \
    rm -rf /src

#
USER 1000:1000

#
VOLUME ["/config"]
WORKDIR /config

#
ENTRYPOINT ["buildarr"]
CMD ["daemon"]
