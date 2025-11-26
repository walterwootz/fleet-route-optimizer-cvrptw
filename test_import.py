#!/usr/bin/env python3
"""Test if app can be imported"""
import sys
import traceback

try:
    from src.app import app
    print("✅ App loaded successfully!")
    print(f"✅ App type: {type(app)}")
    print(f"✅ Routes: {len(app.routes)}")
except Exception as e:
    print(f"❌ Error loading app:")
    print(f"   {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)

