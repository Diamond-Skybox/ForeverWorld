# ForeverWorld

NeoForge 1.21.1 modpack, kept up to date with [packwiz](https://packwiz.infra.link/).

## Install (Prism Launcher)

1. Create an instance: Minecraft **1.21.1**, NeoForge **21.1.259**. Give it at least 12 GB of memory (Settings → Java).
   Java 21 or newer; Java 25 is needed for C2ME's GPU acceleration.
2. Download [`packwiz-installer-bootstrap.jar`](https://github.com/packwiz/packwiz-installer-bootstrap/releases) and
   [`PackHelper.jar`](https://raw.githubusercontent.com/Diamond-Skybox/ForeverWorld/main/PackHelper.jar) and put both in
   the instance's `minecraft` folder (Prism: right-click the instance → Folder → `minecraft`).
3. Instance → Edit → Settings → Custom commands → tick **Custom commands** and set the **Pre-launch command** to:

   ```
   "$INST_JAVA" -jar PackHelper.jar https://raw.githubusercontent.com/Diamond-Skybox/ForeverWorld/main/pack.toml
   ```

4. Launch. The mods are downloaded on the first start and updated on every start after that.

Some CurseForge mods do not allow automatic downloads. PackHelper then opens a window listing them with direct download
links; download each one and it is picked up from your Downloads folder (or save it straight into the `mods` folder), and
the update finishes on its own. PackHelper keeps itself up to date with the pack.
