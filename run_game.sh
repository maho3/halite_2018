#!/bin/sh

size=$(echo 32 40 48 56 64 | xargs shuf -n1 -e)

./halite --replay-directory replays/ -vvv --width $((size)) --height $((size)) "python3 MyBot.py" "python3 MyBot_v1.py"
