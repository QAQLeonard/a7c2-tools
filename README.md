<p align="center"><img src="docs/assets/sony-cloud-logo.png" width="112" height="112" alt="索尼云创 · Sony Imaging Cloud"></p>

# 索尼云创 · A7C II Tools

**English** · [简体中文](README.zh-CN.md)

A desktop tool for the **Sony A7C II (ILCE-7CM2)**: build card-update firmware and configure FL2/FL3, custom Creative Looks, mechanical/electronic shutter audio and Vertical Display.

[Download latest](https://github.com/QAQLeonard/a7c2-tools/releases/latest) · [Changelog](docs/en/changelog.md) · [Sony Imaging Cloud](https://sony.leonardsaikou.top)

> [!WARNING]
>
> ### Read before use · Disclaimer
>
> **This is an unofficial, independent research tool for learning and technical discussion. It is not affiliated with, authorized or endorsed by Sony.**
>
> ### Important: the camera may be bricked, and recovery is not guaranteed
>
> **Modifications can cause boot failure, repeated restarts, crashes during capture or playback, malfunctions or data loss. They may affect official updates, warranty or repairs, and may require paid repair or mainboard replacement.**
>
> **Successful writes, complete readback and passing offline tests do not establish boot safety or stability in every mode. Name, icon and other display-resource changes also carry risks. Not every feature combination has completed physical camera acceptance.**
>
> **One-click recovery is not a complete system reinstallation and may not recover the camera. Backups, camera initialization and official updates do not guarantee recovery either. On an error, disconnect or unknown result, stop writing, preserve diagnostics and do not repeatedly start installation or recovery.**
>
> ### No commercial use or profit-making
>
> **All commercial use and profit-making are prohibited. The author explicitly opposes paid flashing, paid remote installation, resale or paid bundles of the tool, paid unlocking, selling activation keys/dongles, and hardware bundles for profit. This project is provided free of charge. The author offers no paid flashing service and has not authorized anyone to offer these paid services in the author's name.**
>
> ### Do not impersonate Sony or claim author authorization
>
> **The author has never authorized anyone to offer paid services, advertise or promise warranty coverage in the author's or Sony's official name. Do not impersonate Sony, the author or an authorized service provider. Third-party fees imply no author involvement, approval, endorsement or guarantee.**
>
> **Only operate a device you lawfully own or for which the owner has given explicit permission. Back up important data. Do not proceed if you cannot accept device damage and repair costs.**
>
> **Original project code in this distribution uses [PolyForm Noncommercial License 1.0.0](LICENSE). See [Sources and licenses](docs/en/notices.md) for scope and third-party rights. This statement does not exclude liability that cannot lawfully be excluded.**
>
> **[Read the full risk notice and use statement](docs/en/notices.md#risk-notice-and-use-statement)**

## Supported cameras

> [!IMPORTANT]
> **This tool supports only the Sony A7C II (ILCE-7CM2) on firmware 2.01.** It does **not** work on any other model, including the original A7C, the A7 IV, A7CR, A7R V, A6700 and A7 V. The app refuses to connect to them; please don't try.

The following independent projects and research resources are grouped by camera. Refer to each project's own documentation for its supported scope, usage and risks.

| Camera | Projects | What they cover |
| --- | --- | --- |
| **A7R V** | [Michael (Hearts-Ace) / sony-a7r5-custom-firmware](https://github.com/Hearts-Ace/sony-a7r5-custom-firmware) | Custom firmware, FL2/FL3, look and audio resources, and RAW color research; a major source for this project's color fitting and operators. |
| **A7 IV** | [Erlla/sony-a7m4-custom-firmware](https://github.com/Erlla/sony-a7m4-custom-firmware)<br>[happyfrog2026/a7m4-color-research](https://github.com/happyfrog2026/a7m4-color-research)<br>[happyfrog2026/a74-recovery-tools](https://github.com/happyfrog2026/a74-recovery-tools)<br>[Itinerary200/a7m4-lut](https://github.com/Itinerary200/a7m4-lut)<br>[DavidBuchanan314/ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE) | Firmware customization and card updates; color pipelines, custom looks, names/icons and electronic shutter audio; backup/recovery tools; multi-space LUT conversion; low-level reverse engineering and Fastboot. |
| **A7CR** | [lzh2016zzz/a7cr-fl23-research](https://github.com/lzh2016zzz/a7cr-fl23-research)<br>[injectiver/a7cr-creative-look-tools](https://github.com/injectiver/a7cr-creative-look-tools) | FL2/FL3 porting; research tools for native/custom looks, macOS USB handling and RAW/JPEG diagnostics. |
| **A7C II** | [SONY-FW/a7c2-re](https://github.com/SONY-FW/a7c2-re)<br>[chocotan/a7c2-qemu](https://github.com/chocotan/a7c2-qemu)<br>[MDHan/a7c2-fl23-macos](https://github.com/MDHan/a7c2-fl23-macos)<br>[YuuLuo/a7c2-service-preload](https://github.com/YuuLuo/a7c2-service-preload) | Firmware, boot-chain and updater research; an independent QEMU emulator; macOS FL2/FL3 adaptation; USB service authentication and temporary code-execution research. |
| **A6700** | [xyzhangxin/sony-a6700-powerful](https://github.com/xyzhangxin/sony-a6700-powerful) | Powerful6700 feature tools, custom shutter audio, USB maintenance protocols and Pico/Fastboot backup research. |
| **A7 V** | [751K/sony-a7m5-looks · Sony Look Bridge](https://github.com/751K/sony-a7m5-looks) | Photo-development and Creative Look profiles, S-Log3 video LUTs, DCTLs and ARW decoding research covering multiple Sony models. |

**Community:** [Telegram (recommended)](https://t.me/sonyfwlab) · [Discord](https://discord.gg/SwPdfSd9c)
**Author:** Xiaohongshu [QAQLeonard（读研版）](https://www.xiaohongshu.com/user/profile/660501f7000000000600d03c) · Douyin **LeonardZ** (ID `90860261487`)

> [!IMPORTANT]
> This tool modifies programs and settings in the camera firmware. Read the whole [step-by-step guide](#step-by-step-guide) before you start. If the app reports an error, **export a diagnostic bundle first. Do not keep retrying the write.**

Each normal app launch shows a risk summary and requires manually accepting it before the interface opens. The linked [risk notice and use statement](docs/en/notices.md#risk-notice-and-use-statement) provides the full text. The tool is free and unofficial. The author opposes paid flashing and prohibits false claims of Sony/author authorization. Original project code uses the standard PolyForm Noncommercial License 1.0.0; third-party and earlier licenses are retained.

**Firmware source:** obtain the official **ILCE-7CM2 2.01 `BODYDATA.DAT`** from Sony to build installation or recovery firmware. Packages do not include complete official firmware or original voice packs. First Trust retains the original same-body public-key recovery record; keep it safe.

The interface is in Simplified Chinese. Button names below are given in Chinese with an English translation, so you can match them on screen.

## Contents

- [Supported cameras](#supported-cameras)
- [What it does](#what-it-does)
- [Download and requirements](#download-and-requirements)
- [Before you start](#before-you-start)
- [Step-by-step guide](#step-by-step-guide)
  - [Step 1: Install the drivers (Windows)](#step-1-install-the-drivers-windows)
  - [Driver errors: uninstall, then reinstall](#driver-errors-uninstall-then-reinstall)
  - [Still failing: install with Zadig](#still-failing-install-with-zadig)
  - [Step 2: Generate firmware](#step-2-generate-firmware)
  - [Step 3: First Trust and pre-flash settings](#step-3-first-trust-and-pre-flash-settings)
  - [Step 4: Card update and checks](#step-4-card-update-and-checks)
- [Using each feature on its own](#using-each-feature-on-its-own)
- [Troubleshooting](#troubleshooting)
- [Verification status](#verification-status)
- [Command line and development](#command-line-and-development)
- [Release history](#release-history)
- [Credits and licenses](#credits-and-licenses)
- [Film look comparisons](#film-look-comparisons)
- [Acknowledgements](#acknowledgements)
- [Sponsor](#sponsor)

## What it does

| Feature | Description |
| --- | --- |
| **Installation guide** | Prepare drivers, generate firmware, install trust and write settings, then update from the SD card. macOS skips driver installation. |
| **FL2 / FL3** | Choose whether to include these two Creative Looks when generating firmware. |
| **Custom Creative Looks** | Writes `.a7look` files into custom slots 1–6 with your own names, or resets slots to ST. Slots you don't list stay unchanged. |
| **Look conversion** | Produces paired `.a7look` and `.dcp` files offline, without Lightroom. Packages include six icon-bearing A7Look files; get other looks and DCPs from Sony Imaging Cloud. |
| **Lightroom plugin** | When you import RAW files, applies the DCP that matches the custom slot used for each shot. |
| **Shutter speaker sounds** | Independent mechanical/electronic on/off controls; custom audio can target mechanical only, electronic only or both. |
| **Vertical Display** | Rotates shooting information and icons when the camera is held vertically. The full MENU does not rotate. |
| **Restore factory functions** | Generate a recovery DAT from official firmware, prepare the upgrade version, then update manually from the SD card. |

## Download and requirements

| System | Download | Notes |
| --- | --- | --- |
| **Windows 10/11 x64** | `A7C2Tools-Windows-x64.zip` from [Releases](https://github.com/QAQLeonard/a7c2-tools/releases) | Extract the whole archive and run `A7C2Tools.exe`. Keep the `_internal` and `Profiles` folders next to it; don't copy the EXE out on its own. No Python install needed. |
| **macOS 14+ (Apple Silicon)** | `A7C2Tools-macOS-arm64.dmg` from [Releases](https://github.com/QAQLeonard/a7c2-tools/releases) | Drag the app into Applications. It isn't signed by a developer, so allow it once under System Settings → Privacy & Security. No Intel build. **USB on a real Mac has not been verified yet.** |

Packages include six icon-bearing `.a7look` files for the camera. Get other looks and `.dcp` profiles for Lightroom RAW development from [Sony Imaging Cloud](https://sony.leonardsaikou.top).

Firmware generation uses bundled tools. Windows needs no WSL, Ubuntu or separate Python installation; macOS needs no separate Python or Homebrew installation.

Camera: **ILCE-7CM2 on firmware 2.01**. No other model or firmware version is supported.

## Before you start

- **Battery:** at least 50%. The app asks you to confirm power before every write.
- **Cable:** use a USB cable that carries data, plugged straight into the computer (avoid docks and hubs). Connect one camera at a time.
- **USB mode:** set the camera's USB connection to **Mass Storage**.
- **Expected message:** while connecting or switching drivers, the camera may show **"Please check the connected device"** and the computer may not show a drive letter. Both are normal. Judge success by the app's progress and log, not by that message; don't unplug the cable or reinstall drivers because of it.
- **During a write:** while the app shows a task running, don't unplug the cable, power off the camera or close the app. Act only after the app says reading and writing have ended.
- **Opening the app** never connects to or writes the camera by itself.

> [!NOTE]
> **After saving looks or audio**, follow the app's cold-reload instructions to load the new content:
>
> 1. Unplug USB and any other external power.
> 2. Wait for the access light to stop blinking.
> 3. Switch the camera OFF and wait for the screen and access light to go dark.
> 4. Remove the battery and wait **at least one minute**.
> 5. Put the battery back and switch the camera on.
>
> Switching off and on again is not a cold reload. **Pre-flash settings are different: keep the camera on and start the card update immediately. If you restart first, write the settings again.**

## Step-by-step guide

Follow the default installation guide: **prepare drivers → generate firmware → First Trust → write settings and update from the SD card**. macOS starts with firmware generation.

### Step 1: Install the drivers (Windows)

The app talks to the camera through two USB identities: normal Mass Storage `054C:0E8A`, and the authenticated service connection `054C:0336`. Both need a WinUSB driver.

1. Turn on the camera, choose Mass Storage and connect it to the computer.
2. Open **高级设置 (Advanced settings)** in the left sidebar.
3. Click **检测相机与驱动 (Detect camera & drivers)**. The log should show `054C:0E8A`. If it doesn't, check the cable and the USB mode.
4. Click **准备两阶段驱动并测试连接 (Prepare two-stage drivers & test connection)**:
   - The app prepares administrator rights and its installer before handling `0E8A` and switching modes. Windows PnP detection triggers automatic driver setup when `0336` appears.
   - Approve the administrator prompt before the mode switch. Driver installation time does not consume the subsequent interface re-enumeration window; there is no need to race Device Manager.
   - An identity that already has a usable driver (WinUSB, libusbK or libusb0) is kept as it is.
   - The camera may show "Please check the connected device" during this step. That's expected.
5. You're done when the log says **"服务连接成功，驱动准备结束" (service connection succeeded; driver setup finished)**. This step **does not write the camera firmware**.
6. **Recommended:** before your first write, click **检测 USB 连接稳定性（只读）(Check USB stability, read-only)** to test the cable and port.
   - The check runs for **at least 2 minutes**. It repeatedly reads the camera's two program files (the same files a write reads back in full) and compares every round with the first, byte for byte.
   - Any read error, any mismatch, or any single read taking longer than 20 seconds fails the check.
   - It only reads and never writes to the camera.
   - If the connection drops during a write or readback, the result can become "unknown", which is hard to recover from. Confirm the connection is stable before you write.
   - If the check fails, try another cable or a USB port on the back of the computer until it passes.
   - Passing doesn't guarantee the connection will never drop during a write. Keep the cable and power steady while writing.

> [!TIP]
> One-click install also checks and prepares the drivers at the start. Doing this step separately first means any driver problem shows up before anything is written.

**macOS:** no driver installation is needed.
- Close Photos, Image Capture and anything else that might be using the camera's card.
- On **连接与驱动**, click **准备 USB 服务连接 (Prepare USB service connection)**.
- Every camera operation opens a Terminal window. Type your **Mac login password** there so the app can take over USB through sudo. The app never reads or stores the password; closing the window before typing it cancels the camera operation.

### Driver errors: uninstall, then reinstall

The driver state may be wrong if any of these happen:
- Step 1 fails, or reports that `0336` appeared but its interface couldn't be opened.
- You previously installed another driver with Zadig or a similar tool.
- Windows keeps recognizing the camera incorrectly after you connect it.

In that case, **uninstall first, then reinstall with Step 1**:

1. On **连接与驱动**, click **卸载相机驱动，恢复 Windows 默认连接 (Uninstall camera driver, restore Windows default)**. Confirm, and allow administrator permission in the Windows prompt.
   - Only third-party drivers for Sony `054C:0E8A` and `054C:0336` are removed. Other devices are untouched, and the camera firmware is not modified.
   - The driver packages are backed up to the job folder before removal.
2. Follow the log:
   - Usually: **unplug USB and plug it back in using Mass Storage mode**, so Windows rebinds its default driver.
   - If the log says Windows needs a restart, restart the computer (the app never restarts it for you).
3. Go back to [Step 1](#step-1-install-the-drivers-windows) and click **准备两阶段驱动并测试连接** again.

If it still fails, try another cable and a USB port on the back of the computer, and run **检测 USB 连接稳定性（只读）** to narrow it down. If that doesn't help, click **导出诊断包 (Export diagnostics)** at the bottom of the window and share the bundle in the community group.

### Still failing: install with Zadig

On computers where the app's automatic driver install fails, installing the driver by hand with [Zadig](https://zadig.akeo.ie/) usually works. Nothing is written to the camera; this only changes which driver this computer uses for the camera's two USB identities.

On the app's **高级设置 (Advanced settings)** page, the **用 Zadig 手动安装驱动（自动失败时） (Install with Zadig)** button sits next to **准备两阶段驱动并测试连接（自动） (automatic)** and opens these same steps with a Zadig download link.

**First: the camera has two USB identities, and both need a driver**

| Stage | Name in Zadig | USB ID | When it appears |
| --- | --- | --- | --- |
| Normal connection | `ILCE-7CM2` | `054C` `0E8A` | Camera on, Mass Storage selected, plugged in |
| Service mode | `Sony USB Device` | `054C` `0336` | Only after the app authenticates; the camera usually shows "Please check the connected device" |

**Prepare**

1. Download the latest `zadig-x.x.exe` from the Zadig website (a single file, nothing to install).
2. Close this app completely.
3. Switch the camera on and set USB connection to **Mass Storage** in its menu. Connect it directly with a data cable: no hub, and on a desktop PC use a port on the back.

**Part 1: driver for `0E8A`**

1. Right-click Zadig and choose **Run as administrator**. If it asks about checking for updates, either answer is fine.
2. In the **Options** menu, tick **List All Devices**. Without it the camera doesn't show up.
3. Pick **`ILCE-7CM2`** in the drop-down at the top.
4. **Check that the USB ID reads `054C` `0E8A`.** If it doesn't, you picked the wrong entry; try another. Don't change the driver of keyboards, mice, USB drives, network adapters or any other device.
5. The current driver (for example `USBSTOR`) is left of the green arrow. In the driver box right of the arrow, use the up/down arrows to choose **libusbK**.
6. Click the big **Replace Driver** button (it reads **Install Driver** when there is no driver yet). Wait 1–2 minutes until it says **The driver was installed successfully**.
7. Afterwards the camera's drive letter disappears and the camera shows "Please check the connected device". Both are normal.
8. Once installation ends, close Zadig. Unplug USB, turn the camera off, wait for its activity light to go out, remove the battery for at least one minute, then restart in Mass Storage mode and reconnect.

**Part 2: make `0336` appear, then give it a driver**

1. Close Zadig. Open **安装驱动 (Install drivers)** in the app and click **准备两阶段驱动并测试连接 (Prepare drivers and test connection)**. Do not run both installers together.
2. The app uses the `0E8A` driver you just installed and authenticates. The camera then becomes `Sony USB Device` (`054C 0336`).
   - If the app installs the `0336` driver itself and the log says **“服务连接成功，驱动准备结束” (service connection succeeded, drivers ready)**, you're done; go to Part 3.
   - The app prepares its installer before switching modes, installs automatically when `0336` appears and waits again for the interface. **No timed Install click is needed.**
3. Only after the automatic task has failed and stopped, if `0336` remains present, open Zadig, enable **Options → List All Devices**, select **Sony USB Device**, confirm **054C 0336** and install **libusbK**.
4. If `0336` has disappeared, preserve the log instead of repeatedly authenticating or racing two installers. Disappearance alone does not establish a return to `0E8A`.

**Part 3: power-cycle and test again**

1. Unplug USB, switch the camera off and **remove the battery for about a minute**. Put it back, switch on, select Mass Storage and reconnect.
2. In this app click **准备两阶段驱动并测试连接** again. Once the log says **“服务连接成功，驱动准备结束”**, continue with [Step 3: First Trust and pre-flash settings](#step-3-first-trust-and-pre-flash-settings).

**Check the result:** Windows Device Manager should show a **libusbK USB Devices** category containing `ILCE-7CM2`, and `Sony USB Device` once the `0336` driver is installed.

**Problems**

- **libusbK fails to install:** run Zadig as administrator again. If it still fails, choose **WinUSB** instead. The app works with WinUSB, libusbK or libusb0.
- **The camera isn't in the drop-down:** make sure **List All Devices** is ticked, the camera is on in Mass Storage mode, and try another data cable.
- **To restore computer drivers:** click **卸载相机驱动，恢复 Windows 默认连接 (Uninstall camera driver)** on the driver page. Exact-camera third-party packages are backed up before removal. Removing computer drivers cannot guarantee that a camera still reporting `0336` will return to `0E8A`.
- **Macs need no driver.**

### Step 2: Generate firmware

1. In **生成固件 (Generate firmware)**, select the official **ILCE-7CM2 2.01 `BODYDATA.DAT`** obtained from Sony.
2. Select FL2/FL3, looks, sound, Vertical Display and other desired features. Use the default six looks or your own `.a7look` files; sound can use the default material or your own audio.
3. Choose the save folder; the SD card root is supported. A successful build produces `BODYDATA.DAT`. Existing build files with the same name are replaced; unrelated files stay untouched.
4. Safely eject the SD card containing that file, put it in the camera, and continue with trust and settings below.

### Step 3: First Trust and pre-flash settings

1. Start the camera normally and connect USB in Mass Storage mode.
2. On first use, install the body public key in **首次授信 (First Trust)**. Skip this if trust is already installed. Keep the original trust recovery record saved by the tool.
3. Write this build's selected feature settings over USB and wait for the app to confirm that reading and writing have ended.
4. **Unplug USB, keep the camera on, and start the firmware update from the camera menu immediately.** Do not switch off or remove the battery first; if you restarted, write the settings again.

### Step 4: Card update and checks

Follow the camera's update instructions and keep power connected throughout the update. After a normal start, check the selected features: custom look colors, names and icons, FL2/FL3, selected shutter audio and rotated shooting information. Shutter audio also depends on the camera's Audio Signals setting.

The six default looks are:

| Slot | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Look | Classic Negative (NC) | Classic Chrome (CC) | Nostalgic Negative (NN) | Astia (AS) | Ricoh Positive Film (RP) | Ricoh Negative Film (RN) |

## Using each feature on its own

### FL2 / FL3

Choose whether to include FL2/FL3 in **生成固件 (Generate firmware)**, then write settings and update from the card using the installation guide.

### Custom Creative Looks

Select target slots, `.a7look` files and camera names on the looks page, then apply the changes. Unselected slots stay unchanged. Full icon-bearing A7Look /2 files are supported. After saving, follow the cold-reload instructions and check colors, names and icons.

The converter produces A7Look and DCP from a DCP or CUBE. For CUBE files, select the actual input and output spaces, including supported Log spaces such as S-Log3 and V-Log; see [LUT formats and color spaces](docs/en/lut-formats.md). The Lightroom plugin matches registered DCPs by the shooting slot without changing RAW data.

### Shutter speaker sounds

1. Turn mechanical and electronic speaker sounds on/off separately. Each switch preserves the other side and saved custom audio; neither changes the shutter type. The mechanical mechanism still makes a physical sound.
2. Choose an audio or video file, set the **start** and **length** (0.01–2 s), then click **转换所选片段 (Convert selected clip)**. This runs on the computer only.
3. Optionally adjust the volume with **−3 dB / +3 dB / 还原转换时音量 (reset to converted volume)**.
4. In the shared custom-audio entry, select **只修改机械 / 只修改电子 / 机械和电子都修改** (mechanical only / electronic only / both), then **保存到所选快门** (Save to selected shutter). Saving enables the selected sound and preserves the other side's switch/audio. Cold-reload as instructed.
5. **相机内临时试听 (Temporary in-camera audition)** is optional and uses electronic capture. Keep the camera on, unplug USB and take a test shot, then reconnect to save. Mechanical custom audio plays in the opening phase, with a silent closing segment to avoid playing the same clip twice.
6. **移除全部自定义音效，关闭电子快门音效** removes both custom sounds and disables electronic speaker sound, retaining the mechanical switch. The global Audio Signals setting can still suppress playback; the tool does not change it automatically.

### Vertical Display

Include portrait resources when generating firmware and enable Vertical Display in the pre-flash settings. Shooting information and icons rotate when the camera is held vertically; the full MENU does not. No in-camera Vertical Display switch is added.

### Restore factory functions

1. In **一键恢复 (Recovery)**, generate a stock-content recovery package from official **2.01 `BODYDATA.DAT`**. Both the body content and version header are **2.01**.
2. Over USB or configured SSH, set the upgrade version to **2.00**. This prepares version metadata; it does not restore firmware by itself.
3. Once reading and writing have ended, follow the app's instructions, put the recovery `BODYDATA.DAT` in the SD root and start the update manually from the camera menu.

To flash Sony-signed firmware directly, also restore the original same-body public key from **首次授信 (First Trust)** or **高级设置 (Advanced settings)**. Changing the version alone does not restore trust.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| Camera shows "Please check the connected device" | Normal. Follow the app's log. |
| `054C:0E8A` not found | The camera isn't in Mass Storage mode, or the cable can't carry data. Fix it and replug. |
| `0336` never appears | The app cools down and retries automatically, up to 3 times. If it still fails, see [Driver errors](#driver-errors-uninstall-then-reinstall) or [install with Zadig](#still-failing-install-with-zadig). |
| After authentication the camera jumps to playback and `0336` never appears | Try a USB 2.0 port on the computer (or a USB 2.0 cable or hub). On some computers the camera won't enter service mode over a USB 3 high-speed link. |
| `0336` appears but its interface can't be opened | A driver problem. Uninstall and reinstall the driver; don't keep clicking install. |
| Install or restore was interrupted | **Stop and export diagnostics first.** Continue only when the app explicitly shows a reload/verification checkpoint and follow that phase's instructions. Do not restart installation or recovery after an unknown outcome. Confirmed completed program writes are not replayed. |
| App reports an unknown result or asks for review | **Don't retry the write.** Click **导出诊断包 (Export diagnostics)** and share it in the community group. |
| No shutter sound | Check that Audio Signals is on in the camera menu. |
| Look colors differ slightly from the DCP | Expected: the in-camera table is a fitted approximation. |
| Terminal asks for a password on a Mac | Enter your Mac login password; it's used by sudo to take over USB. |

A diagnostic bundle contains device information and local paths, so review it before sharing it publicly. It never includes firmware, body calibration or photos.

## Verification status

See the [changelog](docs/en/changelog.md) for physical test coverage, model results and outstanding checks for each version. Offline tests and file readback do not establish acceptance of every capture mode or body.

## Command line and development

The interface covers everyday use. The original command-line tools remain for advanced users and development:

| Entry | Purpose |
| --- | --- |
| `python desktop.py` | Run the desktop app from source (64-bit Python 3.11; `pip install -r desktop-requirements.txt` first) |
| `FL23.cmd` | Legacy FL2/FL3 command-line installer |
| `python lut.py` | Legacy look import and single-slot restore |
| `python recovery.py` | Full rollback from an original backup |
| `python a7look_compile.py` | Offline DCP/CUBE → `.a7look` compiler |

Offline tests (no camera access): `python -m pytest dev/desktop -q`. Architecture, build and packaging: [development guide](docs/en/development.md). Read [AGENTS.md](AGENTS.md) before letting an AI change the code.

## Release history

Read the [changelog](docs/en/changelog.md) for version changes and [Releases](https://github.com/QAQLeonard/a7c2-tools/releases) for historical notes. Installers are provided only with the [latest release](https://github.com/QAQLeonard/a7c2-tools/releases/latest).

## Credits and licenses

Original project code in this distribution uses the unmodified standard [PolyForm Noncommercial License 1.0.0](LICENSE). All commercial use and profit-making are prohibited. Earlier versions and third-party material retain their original terms; see the [legacy MIT text](docs/licenses/project-legacy-MIT.txt). DCPs, reference looks and bundled third-party components keep their own licenses and attribution; see [notices](docs/en/notices.md). Fujifilm DCP references are credited to **门萨特里顿** and Ricoh references to **爸总林先森** on Xiaohongshu.

This is independent research, not affiliated with Sony, Fujifilm, Ricoh or Adobe. Look names imply neither endorsement nor exact color equivalence, and this tool is not a Sony-signed update.

## Film look comparisons

<details>
<summary>Open the scene-by-scene comparison gallery</summary>

Camera JPEGs, resized, arranged and labelled only; no exposure, white-balance or color edits. Capture settings vary, so these are visual examples rather than controlled measurements.

Each scene shows three separate comparison images in order: **ST / FL / FL2 / FL3**, **ST / NC / CC / NN**, **ST / E / GR Positive / GR Negative**. Read each grid top-left, top-right, bottom-left, bottom-right. NC = Classic Neg., CC = Classic Chrome, NN = Nostalgic Neg., E = Eterna; Astia is not included.

These images were captured with historical versions. Current looks have been refitted; the gallery illustrates the earlier results only.

**01 · Drinks cabinet**

![01 · Drinks cabinet — ST / FL / FL2 / FL3](docs/images/film-comparison/01_饮料柜/01-1_ST_FL_FL2_FL3.jpg)

![01 · Drinks cabinet — ST / NC / CC / NN](docs/images/film-comparison/01_饮料柜/01-2_ST_NC_CC_NN.jpg)

![01 · Drinks cabinet — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/01_饮料柜/01-3_ST_E_GR正片_GR负片.jpg)

**02 · Plants**

![02 · Plants — ST / FL / FL2 / FL3](docs/images/film-comparison/02_绿植/02-1_ST_FL_FL2_FL3.jpg)

![02 · Plants — ST / NC / CC / NN](docs/images/film-comparison/02_绿植/02-2_ST_NC_CC_NN.jpg)

![02 · Plants — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/02_绿植/02-3_ST_E_GR正片_GR负片.jpg)

**03 · Counter**

![03 · Counter — ST / FL / FL2 / FL3](docs/images/film-comparison/03_柜台/03-1_ST_FL_FL2_FL3.jpg)

![03 · Counter — ST / NC / CC / NN](docs/images/film-comparison/03_柜台/03-2_ST_NC_CC_NN.jpg)

![03 · Counter — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/03_柜台/03-3_ST_E_GR正片_GR负片.jpg)

**04 · Spiral staircase**

![04 · Spiral staircase — ST / FL / FL2 / FL3](docs/images/film-comparison/04_旋转楼梯/04-1_ST_FL_FL2_FL3.jpg)

![04 · Spiral staircase — ST / NC / CC / NN](docs/images/film-comparison/04_旋转楼梯/04-2_ST_NC_CC_NN.jpg)

![04 · Spiral staircase — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/04_旋转楼梯/04-3_ST_E_GR正片_GR负片.jpg)

**05 · Bookshelves**

![05 · Bookshelves — ST / FL / FL2 / FL3](docs/images/film-comparison/05_书架/05-1_ST_FL_FL2_FL3.jpg)

![05 · Bookshelves — ST / NC / CC / NN](docs/images/film-comparison/05_书架/05-2_ST_NC_CC_NN.jpg)

![05 · Bookshelves — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/05_书架/05-3_ST_E_GR正片_GR负片.jpg)

**06 · Posters**

![06 · Posters — ST / FL / FL2 / FL3](docs/images/film-comparison/06_海报/06-1_ST_FL_FL2_FL3.jpg)

![06 · Posters — ST / NC / CC / NN](docs/images/film-comparison/06_海报/06-2_ST_NC_CC_NN.jpg)

![06 · Posters — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/06_海报/06-3_ST_E_GR正片_GR负片.jpg)

</details>

## Acknowledgements

**Special thanks to [Michael (Hearts-Ace)](https://github.com/Hearts-Ace/sony-a7r5-custom-firmware).** Our color-fitting algorithms, response-modeling methods and related operator implementations are largely based on his research and code, adapted and further refined for the A7C II. His shared training tools, look resources and research materials, together with permission to use the relevant work, have provided a key foundation for this project’s color work.

This is my first open-source project, and I never expected this much attention and support. Thank you, everyone.

- **Collaborators:** thanks to [@UzLung1435](https://github.com/UzLung1435) for the FL23 refactor, the USB compatibility fixes and the photo/movie curve routing ([#5](https://github.com/QAQLeonard/a7c2-tools/pull/5), [#6](https://github.com/QAQLeonard/a7c2-tools/pull/6)), and to everyone who opened issues, sent pull requests or shared ideas.
- **Color:** thanks to **门萨特里顿** and **爸总林先森** on Xiaohongshu for the DCPs, and to the community members who helped fit and compare the color standards. The built-in looks wouldn't exist without you.
- **Projects this work builds on and cites:**
  - [Erlla/sony-a7m4-custom-firmware](https://github.com/Erlla/sony-a7m4-custom-firmware): A7 IV firmware customization, card updates and feature settings; a reference for this project's installation and resource adaptation.
  - [happyfrog2026/a7m4-color-research](https://github.com/happyfrog2026/a7m4-color-research) and [a74-recovery-tools](https://github.com/happyfrog2026/a74-recovery-tools): color pipelines, custom look names/icons, playback markers, and backup/recovery research and tools.
  - [Itinerary200/a7m4-lut](https://github.com/Itinerary200/a7m4-lut): a reference for LUT color-space conversion and compatible transfer curves.
  - [SONY-FW/a7c2-re](https://github.com/SONY-FW/a7c2-re) and [chocotan/a7c2-qemu](https://github.com/chocotan/a7c2-qemu): A7C II boot-chain, updater, AP/CP and emulator research supporting low-level analysis and offline validation.
  - [DavidBuchanan314/ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE): Sony camera boot, storage and Fastboot reverse engineering.
  - [lzh2016zzz/a7cr-fl23-research](https://github.com/lzh2016zzz/a7cr-fl23-research): FL2/FL3 porting research on the A7CR, the starting point for this project's parameter, label and WBI methods.
  - [MDHan/a7c2-fl23-macos](https://github.com/MDHan/a7c2-fl23-macos): the macOS take on the A7C II, the reference for identifying camera storage and claiming USB on a Mac.
  - [ma1co/Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE), [ma1co/fwtool.py](https://github.com/ma1co/fwtool.py) and [YuuLuo/a7c2-service-preload](https://github.com/YuuLuo/a7c2-service-preload): service-mode communication, firmware parsing and A7C II service-mode research.
  - And thanks to every developer who cites, shares or builds on this project.
- **Testers:** thanks to everyone who tested on their own cameras and patiently sent back logs. Every report made the tool safer.
- **Everyone:** thanks to all who starred, shared and joined the community chats. You brought this project to 3.0.

## Sponsor

If this project helped you, you're welcome to buy me a coffee ☕. Sponsoring is entirely optional, unlocks nothing, and the project will stay free and open source.

<table>
  <tr>
    <td align="center"><img src="docs/images/sponsor/wechat.png" alt="WeChat Pay QR code" width="200"><br>WeChat Pay</td>
    <td align="center"><img src="docs/images/sponsor/alipay.png" alt="Alipay QR code" width="200"><br>Alipay</td>
    <td align="center"><img src="docs/images/sponsor/usdt-bep20.png" alt="USDT (BEP20) QR code" width="200"><br>USDT (BEP20)</td>
  </tr>
</table>

**USDT address** (USDT on **BNB Smart Chain / BEP20** only):

```text
0xbf0b2900f7a45a029a42013b90911f796735a753
```

> [!WARNING]
> Send USDT over BEP20 only. Other networks or tokens may be lost, and please don't send NFTs to this address.
