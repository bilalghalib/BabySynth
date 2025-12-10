#!/bin/bash

# Daf/Tabla Demo Setup Script
# This script sets up the directory structure and placeholder sound files

echo "================================================"
echo "   Daf & Tabla Demo Setup"
echo "================================================"
echo ""

# Create directories
echo "Creating sound directories..."
mkdir -p sounds/tabla
mkdir -p sounds/daf

echo "✓ Directories created"
echo ""

# Check if we have existing sound files to use as placeholders
if [ -f "sounds/upla.wav" ]; then
    echo "Setting up placeholder sound files..."
    echo "(Replace these with real tabla/daf samples later)"
    echo ""

    # Copy existing sounds as placeholders for tabla
    cp sounds/upla.wav sounds/tabla/na.wav
    cp sounds/beezoo.wav sounds/tabla/tin.wav
    cp sounds/hopla.wav sounds/tabla/te.wav
    cp sounds/bisou.wav sounds/tabla/ge.wav
    cp sounds/yallah.wav sounds/tabla/ka.wav
    cp sounds/upla.wav sounds/tabla/dha.wav

    # Copy existing sounds as placeholders for daf
    cp sounds/beezoo.wav sounds/daf/dum.wav
    cp sounds/hopla.wav sounds/daf/tak.wav
    cp sounds/bisou.wav sounds/daf/roll.wav

    echo "✓ Placeholder files created"
    echo ""
    echo "Placeholder files created:"
    echo "  Tabla: na.wav, tin.wav, te.wav, ge.wav, ka.wav, dha.wav"
    echo "  Daf: dum.wav, tak.wav, roll.wav"
    echo ""
else
    echo "⚠️  No existing sound files found in sounds/ directory"
    echo ""
    echo "Please either:"
    echo "  1. Place .wav files in sounds/ directory and re-run this script"
    echo "  2. Download tabla/daf samples manually (see sounds/DAF_TABLA_SOUNDS.md)"
    echo ""
fi

echo "================================================"
echo "Next steps:"
echo "================================================"
echo ""
echo "1. Review the sound setup guide:"
echo "   cat sounds/DAF_TABLA_SOUNDS.md"
echo ""
echo "2. (Optional) Replace placeholder sounds with real tabla/daf samples"
echo ""
echo "3. Run the demo:"
echo "   python demos/daf_tabla.py"
echo ""
echo "4. Choose different layouts:"
echo "   python demos/daf_tabla.py --layout DAF_TABLA"
echo "   python demos/daf_tabla.py --layout TABLA_FULL"
echo "   python demos/daf_tabla.py --layout DAF_FULL"
echo ""
echo "5. Or use with web UI:"
echo "   python main_web.py"
echo "   # Then load the daf_tabla config in the web interface"
echo ""
echo "================================================"
echo "Setup complete! 🎵"
echo "================================================"
