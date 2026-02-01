# MacBook Trackpad Scale - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip3 install pyobjc-framework-Cocoa --break-system-packages
```

### 2. Run the Application
```bash
python3 trackpad_scale.py
```

### 3. Calibration Process

**Step 1: TARE (Zero the scale)**
- Make sure nothing is touching the trackpad
- Click "TARE (Zero)" button
- This sets your baseline

**Step 2: CALIBRATE**
- Find a known weight (examples below)
- Click "Calibrate" button
- Enter the weight in grams
- Place the object on the trackpad
- Press down gently with your finger around the object
- Click "Finish Calibration"

**Step 3: Measure**
- Place your object on the trackpad
- Press gently around it
- Read the weight!

## Known Weight References for Calibration

US Coins (most accurate):
- Penny (post-1982): 2.5g
- Nickel: 5.0g
- Dime: 2.268g
- Quarter: 5.67g

Other common items:
- Standard paperclip: ~1g
- AAA battery: ~11.5g
- AA battery: ~23g
- US $1 bill: ~1g
- Standard sugar packet: ~4g

## Tips for Best Results

1. **Pressure Technique**: Don't just place the object - you need to press gently with your finger around/near the object to activate the force sensors

2. **Consistent Placement**: Always use the same spot on the trackpad (center works best)

3. **Calibrate with Similar Weight**: For measuring 5-10g items, calibrate with a 5g nickel. For 20-50g, calibrate with multiple coins stacked.

4. **Re-tare Between Measurements**: Click TARE before each new measurement for best accuracy

5. **Stable Surface**: Make sure your MacBook is on a stable, flat surface

## How It Works

Your MacBook Pro's Force Touch trackpad contains strain gauges that measure pressure. This app:
- Reads pressure values from the trackpad (0.0 to ~1.0+ scale)
- Applies calibration to convert pressure to weight
- Stores calibration in ~/.trackpad_scale_calibration.json

## Limitations

- Accuracy: ±0.5-2g (not suitable for precision weighing)
- Range: Best for 0-50g (trackpad pressure sensors max out around 50-60g)
- Requires manual pressure application
- Environmental factors (temperature, surface) can affect readings

## Troubleshooting

**"No pressure detected"**
- Make sure you're pressing down, not just placing objects
- Try pressing harder (but don't damage your trackpad!)

**"Readings seem way off"**
- Re-run calibration
- Verify your calibration weight is accurate
- Try TARE again with clean trackpad

**"App won't launch"**
- Check PyObjC is installed: `pip3 list | grep pyobjc`
- Make sure you're running on macOS (this only works on Mac)
- Try running with: `python3 -u trackpad_scale.py`

## Safety Notes

⚠️ Don't place heavy objects (>100g) directly on trackpad
⚠️ Don't press extremely hard - you could damage the sensors
⚠️ Clean trackpad before use for best results
