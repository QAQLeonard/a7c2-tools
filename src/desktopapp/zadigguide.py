"""Manual Zadig driver steps for Windows; the same procedure as the README."""
URL = 'https://zadig.akeo.ie/'
TITLE = 'Install the driver manually with Zadig'
TEXT = """When automatic driver installation fails, most computers succeed with a manual install through Zadig. The whole process never writes to the camera; it only changes the drivers this computer uses for the camera's two USB identities.

The camera has two USB identities, and both need a driver:
· Normal connection: shown in Zadig as ILCE-7CM2, USB ID 054C 0E8A. Appears when the camera is on, set to Mass Storage and connected to the computer.
· Service mode: shown in Zadig as Sony USB Device, USB ID 054C 0336. Appears only after this software authenticates; the camera usually shows "Please check the connected device".

Preparation
1. Click "Open Zadig download page" below and download the latest zadig-x.x.exe (a single file, no installation needed).
2. Turn the camera on and set the menu's USB connection to Mass Storage. Connect it directly to the computer with a data-capable cable, not through a hub; on a desktop PC use a port on the back of the case.

Part 1: install the driver for 0E8A
1. Right-click Zadig and choose "Run as administrator". When asked whether to check for updates, either answer is fine.
2. In the Options menu, tick List All Devices. Without it the camera does not appear.
3. In the drop-down at the top, select ILCE-7CM2.
4. Check that the USB ID field reads 054C 0E8A. If it does not, you picked the wrong device; choose another and check again. Never change the driver of a keyboard, mouse, USB stick, network adapter or any other device.
5. In the driver box to the right of the green arrow, use the up/down arrows to select libusbK.
6. Click Replace Driver (shown as Install Driver when no driver is present) and wait 1–2 minutes until it reports The driver was installed successfully.
7. After the change, it is normal for the camera drive to disappear from the computer and for the camera to show "Please check the connected device".

Part 2: make 0336 appear, then install its driver
1. Keep Zadig open. On this page, click "Prepare two-stage drivers and test connection".
2. The software authenticates using the 0E8A driver you just installed; the camera then becomes Sony USB Device (054C 0336).
· If the log shows "Service connection succeeded; driver preparation finished": you are done, go straight to Part 3.
· If the log says 0336 has no driver, the interface cannot be opened, or 0336 never appears: do not unplug or turn off the camera; continue with the next step.
3. Back in Zadig, click Options → List All Devices again to refresh the list, select Sony USB Device and check that the USB ID is 054C 0336.
· If 0336 is not in the list, the camera has already left service mode: go back to step 1 of this part and test again, then refresh Zadig as soon as 0336 appears.
4. Again select libusbK as the driver, click Replace Driver or Install Driver, and wait for the success message.

Part 3: power-cycle and test again
1. Unplug USB, turn the camera off and remove the battery for about 1 minute. Reinsert the battery, power on, select Mass Storage and reconnect.
2. On this page, click "Prepare two-stage drivers and test connection" once more. When the log shows "Service connection succeeded; driver preparation finished", you can go to the Home page and run the one-click install.

To check the installation: open Windows Device Manager; there should be a "libusbK USB Devices" category containing ILCE-7CM2, and also Sony USB Device once 0336 has been installed.

Troubleshooting
· libusbK fails to install: run Zadig as administrator again and retry; if it still fails, choose WinUSB instead. This software works with any of WinUSB, libusbK or libusb0.
· The camera is not in the drop-down: make sure List All Devices is ticked, the camera is on and set to Mass Storage, and try another data-capable cable.
· To undo everything: on this page click "Uninstall camera drivers and restore Windows default connection"; drivers installed by Zadig are removed too. Then unplug and replug USB and the camera shows up as a USB drive again.
"""
