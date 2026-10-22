# ForeverWorld

NeoForge 1.21.1 modpack, kept up to date with [packwiz](https://packwiz.infra.link/).

## Install (Prism Launcher)

1. Create an instance: Minecraft **1.21.1**, NeoForge **21.1.259**. Give it at least 12 GB of memory (Settings → Java).
   Java 21 or newer; Java 25 is needed for C2ME's GPU acceleration.
2. Download [`packwiz-installer-bootstrap.jar`](https://github.com/packwiz/packwiz-installer-bootstrap/releases) and put it in
   the instance's `minecraft` folder (Prism: right-click the instance → Folder → `minecraft`).
3. Instance → Edit → Settings → Custom commands → tick **Custom commands** and set the **Pre-launch command** to:

   ```
   "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/Diamond-Skybox/ForeverWorld/main/pack.toml
   ```

4. Launch. The installer downloads the mods on the first start and updates them on every start after that.

Some CurseForge mods do not allow automatic downloads; the installer then lists them with a link to download by hand.
