#!/bin/bash

if [ ! -z ${TOKEN+x} ]; then
        export TOKEN=${TOKEN}
fi

exec "$@"