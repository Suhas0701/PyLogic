import os

files = {
    # --- 1. HARDENED APP ENTRY (Global Error Handling) ---
    "main.py": """import flet as ft
import traceback
from app.engine.simulation.controller import SimulationController
from app.ui.canvas.renderer import CanvasRenderer
from app.ui.bridge import UIEngineBridge
from app.ui.panels import ToolboxPanel, InspectorPanel

def main(page: ft.Page):
    page.title = "PyLogic Simulator"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    
    # PRODUCTION HARDENING: Global Error Boundary
    def on_global_error(e):
        print(f"Unhandled Exception: {e.data}")
        # Extract meaningful message for the user
        error_msg = str(e.data).split("\\n")[-2] if "\\n" in str(e.data) else str(e.data)
        sb = ft.SnackBar(content=ft.Text(f"Crash Prevented: {error_msg}", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_900)
        page.snack_bar = sb
        sb.open = True
        page.update()
        
    page.on_error = on_global_error

    # Initialize Core Systems
    engine = SimulationController()
    renderer = CanvasRenderer(page)
    bridge = UIEngineBridge(engine, renderer)
    
    # Initialize UI Panels
    toolbox = ToolboxPanel(bridge)
    inspector = InspectorPanel(bridge)
    
    # Construct Application Layout
    layout = ft.Row(
        controls=[
            toolbox.view,
            renderer.view,
            inspector.view
        ],
        expand=True,
        spacing=0
    )

    page.add(layout)

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(main)
""",

    # --- 2. PYTHON DEPENDENCIES ---
    "requirements.txt": """flet>=0.24.0
""",

    # --- 3. BUILD AUTOMATION SCRIPT ---
    "build.sh": """#!/bin/bash
echo "🚀 Building PyLogic Simulator for WebAssembly..."

# Clean previous build
rm -rf dist/

# Flet Publish command packages the Python code, Pyodide, and Flutter engine into static files
flet publish main.py --app-name "PyLogic" --app-short-name "PyLogic" --description "Interactive Digital Logic Simulator" --route-url-strategy path

echo "✅ Build complete! Static assets are located in the /dist folder."
""",

    # --- 4. GITHUB PAGES CI/CD PIPELINE ---
    ".github/workflows/deploy.yml": """name: Deploy to GitHub Pages

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build-and-deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install Flet
        run: pip install -r requirements.txt
        
      - name: Build WebAssembly Static App
        # IMPORTANT: Replace 'PyLogic' with your exact GitHub repository name!
        run: flet publish main.py --base-url /PyLogic/ --app-name "PyLogic"
        
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './dist'
          
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
""",

    # --- 5. VERCEL HOSTING CONFIGURATION ---
    "vercel.json": """{
  "version": 2,
  "buildCommand": "pip install -r requirements.txt && flet publish main.py",
  "outputDirectory": "dist",
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Cross-Origin-Embedder-Policy", "value": "require-corp" },
        { "key": "Cross-Origin-Opener-Policy", "value": "same-origin" }
      ]
    }
  ]
}
"""
}

for filepath, content in files.items():
    directory = os.path.dirname(filepath)
    if directory: os.makedirs(directory, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# Make the build script executable
os.chmod("build.sh", 0o755)

print("✅ Phase 9 Deployed: WebAssembly Build Pipeline, CI/CD, and Production Configs generated.")