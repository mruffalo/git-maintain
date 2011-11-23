#!/bin/sh
find $1 -type d -name '*.git' -exec git-maintain.py {} +
