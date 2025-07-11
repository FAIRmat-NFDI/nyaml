#!/bin/sh


# https://joss.readthedocs.io/en/latest/paper.html#docker
docker run --rm \
    --volume $PWD:/data \
    --user $(id -u):$(id -g) \
    --env JOURNAL=joss \
    openjournals/inara