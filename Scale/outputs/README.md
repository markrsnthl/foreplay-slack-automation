# MacBook Trackpad Scale 🔬

Turn your MacBook Pro's Force Touch trackpad into a working scale for measuring small objects (0-50g).

## Installation (3 steps)

```bash
# 1. Install dependencies
./install.sh

# 2. Run the app
python3 trackpad_scale.py

# 3. Calibrate and start measuring!
```

## How to Use

### First Time Setup (2 minutes)

1. **TARE**: Click "TARE (Zero)" with nothing on the trackpad
2. **CALIBRATE**:
   - Get a US nickel (5.0g) or use calibration_weights.txt for other options
   - Click "Calibrate" and enter "5.0"
   - Place nickel on trackpad center
   - Press gently around the nickel with your finger
   - Click "Finish Calibration"
3. **MEASURE**: Place any small object and press gently to see its weight

### Daily Use

- Place object on trackpad center
- Press gently around it (trackpad needs pressure to activate)
- Read the weight in grams
- Click TARE between measurements for best accuracy

## What Can You Measure?

Perfect for:
- ✓ Pills/supplements (portion control)
- ✓ Small parcels (estimate shipping)
- ✓ Jewelry/precious items
- ✓ Cooking ingredients (small amounts)
- ✓ Coins and collectibles
- ✓ Seeds and small hardware

Limitations:
- ✗ Best range: 0-50g (accuracy decreases above this)
- ✗ Precision: ±0.5-2g (not lab-grade)
- ✗ Requires manual pressure application

## Files Included

- `trackpad_scale.py` - Main application
- `install.sh` - One-click installer
- `SETUP_GUIDE.md` - Detailed instructions and troubleshooting
- `calibration_weights.txt` - Reference for calibration weights
- `README.md` - This file

## Technical Details

Your Force Touch trackpad uses strain gauge sensors to measure pressure. This app reads those pressure values through macOS Cocoa APIs and converts them to weight using linear calibration.

Calibration data is stored in: `~/.trackpad_scale_calibration.json`

## Safety

⚠️ Don't exceed 100g on the trackpad
⚠️ Don't press extremely hard
⚠️ Clean trackpad before use

## Requirements

- MacBook Pro with Force Touch trackpad (2015 or later)
- macOS
- Python 3
- PyObjC (auto-installed by install.sh)

---

**Need help?** See SETUP_GUIDE.md for troubleshooting and advanced tips.
