"""Format and color-space guidance for the desktop compiler."""
TITLE = 'LUT / DCP formats and color spaces'
TEXT = """The camera write page only accepts .a7look; it never writes .cube or .dcp directly. The generator only converts files on the computer and does not connect to the camera.

1. Which CUBE does the desktop generator accept?
Input: Sony ST standard Creative Look, sRGB-encoded RGB; output: sRGB.
Not S-Log3, S-Log2, HLG, S-Gamut3.Cine, DaVinci Wide Gamut or ACES. An ordinary Rec.709 video LUT is not automatically this input either; also check its transfer curve and gamut.
Only LUTs labelled "for Sony ST / sRGB photos" can be used directly. The .cube extension carries no reliable color-space declaration, so the program cannot detect it.

2. I only have an S-Log3 LUT. What now?
A LUT such as S-Log3 / S-Gamut3.Cine → Rec.709 cannot be used directly in the current desktop generator. Applied to ST images it gives wrong contrast, exposure or color; renaming the extension or editing the header does not fix that.
Re-export a complete 3D CUBE from your grading software covering "Sony ST / sRGB input → target look → sRGB output", including the needed input and output transforms. Merely relabelling the export as sRGB is not enough.
The advanced command line supports an explicit input space plus an ST→that-space bridge CUBE; the target LUT must still output sRGB. The current GUI has no Log bridge option, and a bridge does not guarantee rebuilding Sony's native Log processing.

3. CUBE file structure
A plain-text standalone 3D LUT with LUT_3D_SIZE N; N may be 2–129, commonly 17 / 33 / 65, 33 recommended.
Followed by exactly N³ lines, each with three finite R G B numbers (not 0–255 integer values); red varies fastest. TITLE is optional; DOMAIN_MIN / DOMAIN_MAX are optional and default to 0 0 0 / 1 1 1.
Not supported: 1D LUTs, mixed 1D shaper + 3D files, .3dl, .look, .xmp or images. Output outside 0–1 is clipped before fitting; exporting within 0–1 is recommended.

4. What is a DCP?
A .dcp is an Adobe camera profile, not an S-Log3 video LUT. The generator parses the DCP's LookTable / tone curve offline and fits it directly; no Lightroom, development plug-in, renderer configuration or network is needed.
A DCP is fitted approximately through the built-in shared ST mapping. It does not copy the source camera's sensor matrix or HueSat calibration, nor does it claim to fully reproduce Adobe rendering. A standalone CUBE does not automatically become a DCP profile for Lightroom RAW.

5. How do I write it in the end?
Generate a new .a7look → Add operation → choose a slot and "Write A7Look" → choose the file and enter the in-camera name → Review and apply. Several slots can be written together; slots not listed stay unchanged.
After writing, power-cycle as the dialog describes to load it. The result is an in-camera color-table fit and an approximation; a 65-point CUBE does not mean every sample's precision is preserved, and an exact match with the original DCP / LUT is not guaranteed."""
