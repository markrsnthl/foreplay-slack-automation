#!/bin/bash

echo "========================================="
echo "MacBook Trackpad Scale - Installation"
echo "========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This only works on macOS"
    exit 1
fi

echo "✓ macOS detected"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION found"

# Install PyObjC
echo ""
echo "Installing PyObjC framework..."
pip3 install pyobjc-framework-Cocoa --break-system-packages

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✓ Installation complete!"
    echo "========================================="
    echo ""
    echo "To run the scale:"
    echo "  python3 trackpad_scale.py"
    echo ""
    echo "Quick calibration:"
    echo "  1. Click TARE with nothing on trackpad"
    echo "  2. Click Calibrate with a 5g nickel"
    echo "  3. Start measuring!"
    echo ""
    echo "See SETUP_GUIDE.md for detailed instructions"
    echo ""
else
    echo ""
    echo "❌ Installation failed"
    echo "Try running manually:"
    echo "  pip3 install pyobjc-framework-Cocoa --break-system-packages"
    exit 1
fi
