#!/bin/bash
# doesn't work in Windows unless run from a shell that supports bash
set -e

MODULE_NAME="ynamazon.cli.cli"

# Output directory for the generated documentation
OUTPUT_FILENAME="CLI_README.md"
CLI_NAME="yna"

# Generate the documentation using Typer's utils
typer "$MODULE_NAME" utils docs --output "$OUTPUT_FILENAME" --name "$CLI_NAME"

git diff --exit-code $OUTPUT_FILENAME || {
    echo "Typer docs are out of date. Please re-run the docs generator."
    exit 1
}
