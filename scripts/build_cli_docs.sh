#!/bin/bash

# This script generates documentation for the CLI using Typer's utils.

# Ensure the script exits on error
set -e

# Path to the CLI file
CLI_FILE="ynamazon.cli.cli"

# Output directory for the generated documentation
OUTPUT_FILENAME="CLI_README.md"
CLI_NAME="yna"

# Generate the documentation using Typer's utils
python -m typer "$CLI_FILE" utils docs --output "$OUTPUT_FILENAME" --name "$CLI_NAME"

echo "Documentation generated successfully as '$OUTPUT_FILENAME'."
