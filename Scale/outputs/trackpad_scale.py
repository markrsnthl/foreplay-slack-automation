#!/usr/bin/env python3
"""
MacBook Trackpad Scale
Uses Force Touch pressure sensors to measure weight of small objects
"""

import sys
import json
import os
from pathlib import Path

try:
    from Cocoa import (
        NSApplication, NSApp, NSWindow, NSView, NSEvent, NSObject,
        NSApplicationActivationPolicyRegular, NSBackingStoreBuffered,
        NSMakeRect, NSTextField, NSButton, NSFont, NSColor, NSTimer,
        NSEventMaskPressure, NSEventTypeDirectTouch, NSEventTypePressure,
        NSEventMaskGesture, NSEventTypeGesture
    )
    from PyObjCTools import AppHelper
    import objc
except ImportError:
    print("ERROR: PyObjC not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyobjc-framework-Cocoa", "--break-system-packages"])
    print("Please run the script again.")
    sys.exit(1)


class TrackpadScale(NSView):
    def init(self):
        self = objc.super(TrackpadScale, self).init()
        if self is None:
            return None

        self.calibration_file = Path.home() / ".trackpad_scale_calibration.json"
        self.calibration_data = self.load_calibration()
        self.is_calibrating = False
        self.calibration_weight = 0
        self.calibration_readings = []
        self.current_pressure = 0
        self.tare_value = 0
        self.last_event_pressure = 0
        self.monitor = None

        return self

    def load_calibration(self):
        """Load calibration data from file"""
        if self.calibration_file.exists():
            with open(self.calibration_file, 'r') as f:
                return json.load(f)
        return {"slope": 50.0, "intercept": 0.0}  # Default values

    def save_calibration(self):
        """Save calibration data to file"""
        with open(self.calibration_file, 'w') as f:
            json.dump(self.calibration_data, f)

    def setup_ui(self, window):
        """Setup the user interface"""
        self.window = window

        # Weight display
        self.weight_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 180, 360, 60))
        self.weight_label.setStringValue_("0.0 g")
        self.weight_label.setFont_(NSFont.systemFontOfSize_(48))
        self.weight_label.setBezeled_(False)
        self.weight_label.setDrawsBackground_(False)
        self.weight_label.setEditable_(False)
        self.weight_label.setSelectable_(False)
        self.weight_label.setAlignment_(1)  # Center
        self.addSubview_(self.weight_label)

        # Status label
        self.status_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 150, 360, 25))
        self.status_label.setStringValue_("Touch trackpad to measure (no click needed)")
        self.status_label.setFont_(NSFont.systemFontOfSize_(14))
        self.status_label.setBezeled_(False)
        self.status_label.setDrawsBackground_(False)
        self.status_label.setEditable_(False)
        self.status_label.setSelectable_(False)
        self.status_label.setAlignment_(1)  # Center
        self.addSubview_(self.status_label)

        # Tare button
        self.tare_button = NSButton.alloc().initWithFrame_(NSMakeRect(20, 100, 170, 32))
        self.tare_button.setTitle_("TARE (Zero)")
        self.tare_button.setBezelStyle_(1)
        self.tare_button.setTarget_(self)
        self.tare_button.setAction_("tare:")
        self.addSubview_(self.tare_button)

        # Calibrate button
        self.calibrate_button = NSButton.alloc().initWithFrame_(NSMakeRect(210, 100, 170, 32))
        self.calibrate_button.setTitle_("Calibrate")
        self.calibrate_button.setBezelStyle_(1)
        self.calibrate_button.setTarget_(self)
        self.calibrate_button.setAction_("startCalibration:")
        self.addSubview_(self.calibrate_button)

        # Pressure indicator
        self.pressure_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 60, 360, 20))
        self.pressure_label.setStringValue_("Pressure: 0.000")
        self.pressure_label.setFont_(NSFont.systemFontOfSize_(12))
        self.pressure_label.setTextColor_(NSColor.grayColor())
        self.pressure_label.setBezeled_(False)
        self.pressure_label.setDrawsBackground_(False)
        self.pressure_label.setEditable_(False)
        self.pressure_label.setSelectable_(False)
        self.status_label.setAlignment_(1)
        self.addSubview_(self.pressure_label)

        # Instructions
        self.instructions = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 10, 360, 40))
        self.instructions.setStringValue_("💡 First: Click TARE\nThen: Click Calibrate, place object + touch trackpad gently\nMeasure: Just touch trackpad near object (no click needed)")
        self.instructions.setFont_(NSFont.systemFontOfSize_(10))
        self.instructions.setTextColor_(NSColor.grayColor())
        self.instructions.setBezeled_(False)
        self.instructions.setDrawsBackground_(False)
        self.instructions.setEditable_(False)
        self.instructions.setSelectable_(False)
        self.addSubview_(self.instructions)

        # Start continuous monitoring
        self.start_monitoring()

    def start_monitoring(self):
        """Start continuous pressure monitoring"""
        # Global event monitor for any pressure changes
        from Cocoa import NSEventMaskAny

        def global_handler(event):
            try:
                pressure = event.pressure()
                if pressure > 0:
                    self.last_event_pressure = pressure
            except:
                pass

        def local_handler(event):
            try:
                pressure = event.pressure()
                if pressure > 0:
                    self.last_event_pressure = pressure
                    self.current_pressure = pressure
            except:
                pass
            return event

        self.monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskAny,
            global_handler
        )

        # Also add local monitor
        self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskAny,
            local_handler
        )

        # Timer to continuously update display
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.05,  # Update every 50ms
            self,
            'updateFromTimer:',
            None,
            True
        )

    def updateFromTimer_(self, timer):
        """Update display from timer"""
        if self.last_event_pressure > 0:
            self.current_pressure = self.last_event_pressure

        if self.is_calibrating and self.current_pressure > 0:
            self.calibration_readings.append(self.current_pressure)

        self.update_display()

        # Decay pressure reading when no events
        if self.last_event_pressure > 0:
            self.last_event_pressure *= 0.95

    def acceptsFirstResponder(self):
        return True

    def tare_(self, sender):
        """Zero the scale"""
        self.tare_value = self.current_pressure
        self.status_label.setStringValue_("Tared! (Zero point set)")
        self.update_display()

    def startCalibration_(self, sender):
        """Start calibration process"""
        if not self.is_calibrating:
            # Ask for weight
            from Cocoa import NSAlert, NSAlertFirstButtonReturn
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Calibration")
            alert.setInformativeText_("Enter the weight in grams of the object you'll place on the trackpad (e.g., a US nickel = 5g, penny = 2.5g):")
            alert.addButtonWithTitle_("OK")
            alert.addButtonWithTitle_("Cancel")

            textfield = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 200, 24))
            textfield.setStringValue_("5.0")
            alert.setAccessoryView_(textfield)

            response = alert.runModal()

            if response == NSAlertFirstButtonReturn:
                try:
                    self.calibration_weight = float(textfield.stringValue())
                    self.is_calibrating = True
                    self.calibration_readings = []
                    self.status_label.setStringValue_(f"Place {self.calibration_weight}g object on trackpad and press gently...")
                    self.calibrate_button.setTitle_("Finish Calibration")
                except ValueError:
                    self.status_label.setStringValue_("Invalid weight entered")
        else:
            # Finish calibration
            if len(self.calibration_readings) > 10:
                avg_pressure = sum(self.calibration_readings) / len(self.calibration_readings)
                net_pressure = avg_pressure - self.tare_value

                if net_pressure > 0.001:
                    # Calculate slope: weight = slope * pressure
                    self.calibration_data["slope"] = self.calibration_weight / net_pressure
                    self.save_calibration()
                    self.status_label.setStringValue_(f"Calibrated! (slope: {self.calibration_data['slope']:.2f})")
                else:
                    self.status_label.setStringValue_("Calibration failed: not enough pressure detected")
            else:
                self.status_label.setStringValue_("Calibration failed: not enough readings")

            self.is_calibrating = False
            self.calibration_readings = []
            self.calibrate_button.setTitle_("Calibrate")

    def pressureChangeWithEvent_(self, event):
        """Handle pressure events from trackpad"""
        pressure = event.pressure()
        self.current_pressure = pressure
        self.last_event_pressure = pressure

        if self.is_calibrating:
            self.calibration_readings.append(pressure)

    def mouseDown_(self, event):
        """Handle mouse down for pressure tracking"""
        self.pressureChangeWithEvent_(event)

    def mouseDragged_(self, event):
        """Handle mouse drag for continuous pressure tracking"""
        self.pressureChangeWithEvent_(event)

    def mouseUp_(self, event):
        """Handle mouse up"""
        pass

    def dealloc(self):
        """Cleanup when view is deallocated"""
        if self.monitor:
            NSEvent.removeMonitor_(self.monitor)
        if hasattr(self, 'local_monitor') and self.local_monitor:
            NSEvent.removeMonitor_(self.local_monitor)
        if hasattr(self, 'timer') and self.timer:
            self.timer.invalidate()
        objc.super(TrackpadScale, self).dealloc()

    def update_display(self):
        """Update the weight display"""
        net_pressure = self.current_pressure - self.tare_value

        if net_pressure < 0:
            net_pressure = 0

        weight = net_pressure * self.calibration_data["slope"]

        self.weight_label.setStringValue_(f"{weight:.1f} g")
        self.pressure_label.setStringValue_(f"Pressure: {self.current_pressure:.3f} (net: {net_pressure:.3f})")


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        # Create window
        frame = NSMakeRect(100, 100, 400, 260)
        style_mask = 15  # Titled, Closable, Miniaturizable, Resizable

        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, style_mask, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("MacBook Trackpad Scale")

        # Create and setup view
        self.scale_view = TrackpadScale.alloc().init()
        self.scale_view.setFrame_(frame)
        self.scale_view.setup_ui(self.window)

        self.window.setContentView_(self.scale_view)
        self.window.makeKeyAndOrderFront_(None)
        self.window.makeFirstResponder_(self.scale_view)

    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        return True


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    app.activateIgnoringOtherApps_(True)
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()
