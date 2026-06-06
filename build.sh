#!/bin/bash
echo "🚀 Building PyLogic Simulator for WebAssembly..."

# Clean previous build
rm -rf dist/

# Flet Publish command packages the Python code, Pyodide, and Flutter engine into static files
flet publish main.py --app-name "PyLogic" --app-short-name "PyLogic" --description "Interactive Digital Logic Simulator" --route-url-strategy path

echo "✅ Build complete! Static assets are located in the /dist folder."
