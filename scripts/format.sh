#!/bin/sh -e
set -x

flake8 app
black app
