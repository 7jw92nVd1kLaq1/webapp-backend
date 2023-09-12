#!/bin/sh

# Startup Xvfb
#Xvfb -ac :1 -screen 0 1280x1024x16 > /dev/null 2>&1 &

# Export some variables
#export DISPLAY=:1.0
export PUPPETEER_EXEC_PATH="google-chrome-stable"

# Run commands
cmd="npx nodemon --watch /parserFolder/util /parserFolder/app.js"
echo "Running '$cmd'!"
if eval $cmd; then
    # no op
    echo "Successfully ran '$cmd'"
else
    exit_code=$?
    echo "Failure running '$cmd', exited with $exit_code"
    exit $exit_code
fi
