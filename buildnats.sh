#!/bin/sh

if [  $# -gt 0 ]
    then
        NATS_VERSION="$1";
    else
        NATS_VERSION="master";
fi

echo "Using NATS version $NATS_VERSION"

git clone https://github.com/derekcollison/nats.git vendor/nats-server
cd vendor/nats-server
git checkout $NATS_VERSION

${TRAVIS:?"This is not a Travis build. All Done"}
