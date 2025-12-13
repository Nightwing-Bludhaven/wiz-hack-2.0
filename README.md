# Wiz-Hack (Modified Fork)

Well, basically I modified and improved some things in the program made by “myselfshravan,” which are mainly:

## New “Auto-DJ Smart” mode
It works with different algorithms such as:

* **FFT Analysis:** Real-time frequency decomposition to isolate bass sub-bands (20-150Hz).
* **Crest Factor Logic:** Determines track dynamics (Punchy vs. Compressed) to switch visualization modes automatically.
* **RMS Normalization:** Inverse sensitivity scaling to ensure consistent lighting response across different volume levels.
* **Bass Ratio Detection:** Identifies bass-dominant tracks to prioritize low-end reactivity.

All these algorithms are designed to detect and analyze the entire audio file to be played so that the program can automatically change the sensitivity, smoothness, and lighting mode, whether it be **”spectrum pulse“** or **”spectrum gradient."**

One change implemented was the removal of the integration with the **“stock visualizer”** so that the program focuses solely on audio and music.

## Tidal Realtime Integration
Another improvement is that it now integrates with **“TidaLuna”** with WASAPI, so you can listen to audio in real time and have the lights react to it. This mode is called `tidal_realtime.py`.

Support for different languages has also been added, which changes automatically depending on the language of your device.

## Other minor fixes

* **Zero-Lag UDP:** Refactored `wiz_control.py` to use “Fire & Forget” communication, eliminating stutter on 2.4GHz Wi-Fi networks.
* **Optimized Throttling:** Adjusted update rate to ~28 FPS for smoother transitions on standard Wiz bulbs.
* **Secure CORS:** Restricted the local server to only accept requests from `desktop.tidal.com`.
