# Installing CODESYS on a Mac with Wine and Winetricks

Install CODESYS 64-bit 3.5.22.30 on macOS using Wine and Winetricks. This guide records the setup tested on September 15, 2026.

## What works

The test machine was an Apple M1 Max running macOS 26.6, Wine 11.0 through Rosetta, and Winetricks 20260125. This is an experimental setup. We have not tested other Macs or software versions.

The IDE created, saved, and closed a project through its Scripting engine. Editors, simulation, and PLC connections still need separate testing.

| Component | Result in the tested installation |
|---|---|
| CODESYS development system | Installed; project creation/save/close passed |
| Scripting, CFC, Ladder, LD/FBD, SFC, SoftMotion, communication libraries | Installed; individual features not comprehensively tested |
| Visualization 4.10 | Installation failed; omitted |
| Separate CODESYS Installer 2.6.1 | Hung under Wine; removed |
| Windows Control Win, Gateway services, CodeMeter | Not installed |
| Physical PLC connections and licensed add-ons | Not tested |

This setup does not support the omitted components. The older [CODESYS Forge Wine guide](https://forge.codesys.com/tol/codesys-4-linux/home/Manual%20Installation/) covers earlier CODESYS releases. Use the prerequisite versions below for this release.

## What you need

- A Mac with administrator access for installing development tools.
- The official **CODESYS 64 3.5.22.30** installer, saved as `~/Downloads/codesys.exe`. Obtain it from CODESYS, not a third-party download site.
- Wine 11.0 with support for both 64-bit and 32-bit Windows programs, Winetricks, Python 3, Apple's command-line development tools, and `msitools`.
- The `helpers` directory supplied with this guide.
- Internet access and enough free disk space for the installer, extracted copies, Windows prerequisites, and the installed IDE. Allow several gigabytes for working files.

A Wine prefix holds an application's Windows files and registry. Give CODESYS its own prefix.

## 1. Install the Mac tools

Install Apple's command-line tools if they are missing:

```sh
xcode-select --install
```

On Apple Silicon, install Rosetta if macOS requests it when you run Intel software. Intel Macs do not need Rosetta.

Install [MacPorts](https://www.macports.org/install.php), then use its [Wine installation instructions](https://ports.macports.org/port/wine-stable/):

```sh
sudo port install wine-stable winetricks
```

On Apple Silicon, check the MacPorts architecture before installing Wine. The [MacPorts Wine overlay maintainer's instructions](https://github.com/Gcenx/macports-wine) describe the x86_64 requirement. If Wine installation fails on an architecture mismatch, resolve that before continuing. Do not blindly change the architecture of an existing MacPorts installation that other software depends on.

Install `msitools` through your package manager. For a Mac already using Homebrew:

```sh
brew install msitools
```

The tested machine used MacPorts Wine at `/opt/local/bin/wine` and Homebrew Winetricks at `/opt/homebrew/bin/winetricks`. The instructions above use MacPorts for both tools. That combination has not been tested here.

Check that the tools are available:

```sh
/opt/local/bin/wine --version
winetricks --version
python3 --version
command -v msiextract
```

## 2. Prepare a dedicated environment

Run subsequent Terminal commands in the same window so these settings remain active:

```sh
export WINE=/opt/local/bin/wine
export WINEPREFIX="$HOME/.wine.codesys"
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export WINEDEBUG=-all
export WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--disable-gpu
export CDS_WORK="$HOME/codesys-install"
mkdir -p "$CDS_WORK"
```

If `~/.wine.codesys` already exists, stop and determine whether it contains an installation you want to keep. Do not delete it. For a separate attempt, choose a different prefix and use that same path throughout, including in your launcher.

Copy this guide's three helper files into `$CDS_WORK`. For example, drag the contents of the supplied `helpers` folder into the `codesys-install` folder in your home directory.

Initialize Wine and install the prerequisites:

```sh
"$WINE" wineboot -u
winetricks -q dotnet48 vcrun2022 msxml6 win10
```

Let each command finish before starting the next. Do not run concurrent installations in this prefix. Wine needs to run as your normal user, not with `sudo`.

[Winetricks](https://github.com/Winetricks/winetricks) installs .NET Framework 4.8, Visual C++ runtimes, MSXML 6, and Windows 10 compatibility settings.

## 3. Install WebView2

Download Microsoft's x64 Evergreen standalone WebView2 installer from the [official Microsoft download link](https://go.microsoft.com/fwlink/p/?LinkId=2124701), save it in `$CDS_WORK`, and run:

```sh
"$WINE" "$CDS_WORK/MicrosoftEdgeWebView2RuntimeInstallerX64.exe" /silent /install
```

Use the actual filename if your browser gives it a different name. The tested installation used WebView2 153.0.4234.32; Microsoft's Evergreen download can change.

Do not install the separate bundled CODESYS Installer for this recipe. Version 2.6.1 hung under Wine, including when the IDE asked it for its version. Installing .NET 8 did not solve that problem.

## 4. Extract the CODESYS setup files

The original InstallShield launcher encountered path-handling problems. We installed its embedded MSI directly instead.

The supplied extractor supports the 3.5.22.30 EXE used in this installation. It may fail with other releases. It reads `~/Downloads/codesys.exe` and writes a `setup` folder beside itself.

```sh
cd "$CDS_WORK"
clang -dynamiclib -O2 decode.c -o decode.dylib
python3 extract.py
ls -lh "$CDS_WORK/setup/CODESYS 64 3.5.22.30.msi"
```

Stop if extraction errors occur or that exact MSI is missing. Do not try changing version numbers in this guide to make an unrelated installer fit. The helper decodes the installer archive; it does not modify the MSI or bypass package signatures.

## 5. Apply the assembly-loading fix

Wine's own `security.dll` can be mistaken for CODESYS's managed `Security.dll`, causing `BadImageFormatException`.

Set an override for each application below. A global override broke the InstallShield launcher during testing.

```sh
for cds_exe in CODESYS.exe PackageManagerCLI.exe IPMCLI.exe PackageManager.exe \
  LACUtil.exe ImportLibraryProfile.exe CoreInstallerSupport.exe \
  CoreInstallerSupport2.exe DeletePlugInCache.exe RepairMenuConfig.exe \
  Dependencies.exe PackageManagerSelfUpdater.exe VisualStylesEditor.exe \
  Html5ControlEditor.exe
 do
  "$WINE" reg add "HKCU\\Software\\Wine\\AppDefaults\\${cds_exe}\\DllOverrides" \
    /v '*security' /t REG_SZ /d native /f
 done
```

Restore OLE Automation registration and use software rendering for WPF:

```sh
"$WINE" regsvr32 /s oleaut32.dll
"$WINE" 'C:\windows\syswow64\regsvr32.exe' /s oleaut32.dll
"$WINE" reg add 'HKCU\Software\Microsoft\Avalon.Graphics' \
  /v DisableHWAcceleration /t REG_DWORD /d 1 /f
```

The WPF setting was present in the final working environment; it was not independently proven necessary.

## 6. Install the core development system

Review the vendor's license and readme before running this silent command: `AgreeToLicense=Yes` and `CDSAgreeToReadMe=Yes` record acceptance.

Use the installation directory exactly as shown. The path without spaces avoids another Wine/MSI quoting problem.

```sh
"$WINE" msiexec \
  /i "$CDS_WORK/setup/CODESYS 64 3.5.22.30.msi" /qn /norestart \
  'INSTALLDIR=C:\CODESYS-3.5.22.30' \
  'ADDLOCAL=Basic,CODESYS,CDS_Exe_x64,Compatibility,OEMCustomization_CDS,Only_x64,SubFeature' \
  CDS_INSTALL_SERVICES=0 CDS_INSTALL_NOPACK=1 \
  AgreeToLicense=Yes CDSAgreeToReadMe=Yes \
  '/L*v' 'C:\codesys-core-install.log'
printf 'Installer exit code: %s\n' "$?"
```

This installs the core IDE and compatibility package while excluding Windows services and postponing bundled add-ons. These MSI feature names and properties are specific to this installer.

The tested command returned `0`. Its log is at:

```text
~/.wine.codesys/drive_c/codesys-core-install.log
```

Confirm that this file exists:

```sh
ls "$WINEPREFIX/drive_c/CODESYS-3.5.22.30/CODESYS/Common/CODESYS.exe"
```

Files alone do not prove success: inspect the installer exit code and log too.

## 7. Repair the bundled package metadata helper

The older `CoreInstallerSupport.exe` hung when inspecting some packages. The bundled `CoreInstallerSupport2.exe` worked, but was not a direct replacement because the old package manager expects two legacy metadata queries.

The supplied `helper-launcher.c` answers those queries, removes legacy `APPDOMAIN_MANAGER_*` variables before launching helper 2, and returns the child's exit code. It does not change package-signature or licensing checks. The adapter is specific to these CODESYS assemblies and is not vendor-supported.

Install a Windows cross-compiler if needed:

```sh
sudo port install x86_64-w64-mingw32-gcc
```

Compile and install the adapter, keeping the original files:

```sh
cd "$CDS_WORK"
/opt/local/bin/x86_64-w64-mingw32-gcc -municode -Wall -Wextra -O2 -static \
  helper-launcher.c -o CoreInstallerSupport.exe
export CDS_COMMON="$WINEPREFIX/drive_c/CODESYS-3.5.22.30/CODESYS/Common"
cp -n "$CDS_COMMON/CoreInstallerSupport.exe" "$CDS_COMMON/CoreInstallerSupport.exe.wine-original"
cp -n "$CDS_COMMON/CoreInstallerSupport.exe.config" "$CDS_COMMON/CoreInstallerSupport.exe.config.wine-original"
cp CoreInstallerSupport.exe "$CDS_COMMON/CoreInstallerSupport.exe"
cp helper-launcher.c "$CDS_COMMON/CoreInstallerSupport-wine.c"
cp "$CDS_COMMON/CoreInstallerSupport2.exe.config" "$CDS_COMMON/CoreInstallerSupport.exe.config"
```

Do not replace helper 1 with an ordinary copy of helper 2. That caused a separate application-domain initialization failure in testing.

## 8. Install bundled add-ons

Extract the MSI's files with `msiextract`:

```sh
msiextract -C "$CDS_WORK/msi-files" "$CDS_WORK/setup/CODESYS 64 3.5.22.30.msi"
```

Inside the resulting folders, locate the bundled `.package` files. Start with **CODESYS Scripting 4.2.0.0.package**, which is needed for the verification below. Copy it to:

```text
~/.wine.codesys/drive_c/codesys-packages/CODESYS Scripting 4.2.0.0.package
```

Create that folder first:

```sh
mkdir -p "$WINEPREFIX/drive_c/codesys-packages"
```

Create a Windows command file. Using a `.cmd` file preserves the quoted profile name correctly:

```sh
cat > "$WINEPREFIX/drive_c/install-codesys-package.cmd" <<'CMD'
@echo off
cd /d C:\CODESYS-3.5.22.30\CODESYS\Common
PackageManagerCLI.exe --profile="CODESYS V3.5 SP22 Patch 3" --install="C:\codesys-packages\CODESYS Scripting 4.2.0.0.package" --verbose --cancelOnException
CMD
"$WINE" cmd /c 'C:\install-codesys-package.cmd' > "$CDS_WORK/package-install.log" 2>&1
printf 'Package installer exit code: %s\n' "$?"
```

For additional packages, copy each package into `C:\codesys-packages`, change the filename in the command file, and install one at a time. Check each log and exit code before continuing. Some packages may require other packages first; follow the dependency information reported by the installer.

Omit CODESYS Visualization 4.10.0.0. It failed on unsupported Windows shortcut APIs and later menu-registration errors. Installing it repeatedly left an incomplete state and complicated startup. Visualization Support is a separate package and does not replace Visualization itself.

These steps install packages one at a time. The original setup installed them in a batch before removing failed packages. This revised sequence has not been tested on a fresh prefix. A package appearing in the package database is not sufficient proof that every installation step succeeded.

## 9. Create a launcher

Create a Windows launch command:

```sh
cat > "$WINEPREFIX/drive_c/launch-codesys.cmd" <<'CMD'
@echo off
cd /d C:\CODESYS-3.5.22.30\CODESYS\Common
CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 3"
CMD
```

Create a Mac launcher you can double-click in Finder:

```sh
mkdir -p "$HOME/Applications"
cat > "$HOME/Applications/CODESYS.command" <<'SH'
#!/bin/sh
export WINEPREFIX="$HOME/.wine.codesys"
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export WINEDEBUG=-all
export WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--disable-gpu
exec /opt/local/bin/wine cmd /c 'C:\launch-codesys.cmd' >> "$WINEPREFIX/codesys-launch.log" 2>&1
SH
chmod +x "$HOME/Applications/CODESYS.command"
```

If you selected a different prefix earlier, edit the `WINEPREFIX` line in this launcher. First startup can take several minutes. Avoid opening several copies while waiting.

## 10. Verify that it actually works

For a manual check, launch CODESYS, create an empty project, save it, close it, and reopen it.

For the automated check used on the tested machine, create a script in the prefix:

```sh
cat > "$WINEPREFIX/drive_c/verify-codesys.py" <<'PY'
from scriptengine import *
project = projects.create(r"C:\codesys-verification.project")
project.save()
project.close()
print("CODESYS project create/save/close: PASS")
PY
cat > "$WINEPREFIX/drive_c/verify-codesys.cmd" <<'CMD'
@echo off
cd /d C:\CODESYS-3.5.22.30\CODESYS\Common
CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 3" --runscript="C:\verify-codesys.py" --noUI --textPrompts
CMD
"$WINE" cmd /c 'C:\verify-codesys.cmd' > "$CDS_WORK/verification.log" 2>&1
printf 'Verification exit code: %s\n' "$?"
cat "$CDS_WORK/verification.log"
ls -lh "$WINEPREFIX/drive_c/codesys-verification.project"
```

Close other CODESYS instances before testing. Use a new output filename if you repeat this test and the project already exists.

Check the result:

1. Exit code `0`.
2. `CODESYS project create/save/close: PASS` in the log.
3. An actual, nonempty `codesys-verification.project` file.

The official [CODESYS command-line documentation](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_commandline.html) explains `--runscript`, `--noUI`, and `--textPrompts`.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `BadImageFormatException` mentioning Security.dll | Apply the application-specific native overrides in step 5. Avoid a global Security override. |
| InstallShield stalls at "Initializing Engine" | Check OLE registration; rerun both `regsvr32` commands after a failed installer rollback. This fixed one observed cause, not every possible stall. |
| Profile not found or arguments split incorrectly | Use a `.cmd` file with the exact quoted profile name. |
| Package inspection hangs | Check that the compiled adapter and bundled helper 2 are both present, with matching CODESYS versions. |
| IDE waits on `APInstaller.CLI.exe --version` | The separate CODESYS Installer was incompatible in this setup. Uninstall that optional component through Wine's uninstaller; keep the IDE. |
| Visualization reports `IShellLinkDataList.RemoveDataBlock` / "not implemented" | This is an unresolved Wine shortcut API limitation. Omit that package. |
| Blank page or embedded browser graphics errors | Check WebView2 installation and the launcher's `--disable-gpu` setting. |
| Startup seems slow | Wait and inspect the log before launching again. Use the same locale and prefix as the launcher. |
| A previous package attempt left deferred installation errors | Inspect the package logs and use its uninstall/recovery path. Do not delete plugin directories or the package database to force a successful-looking state. |

Do not terminate the whole Wine environment during an active installation. Do not treat "files copied" or an installer window disappearing as successful completion.

## Repository contents

The `helpers` folder contains the extractor and adapter source code. Download this repository with **Code > Download ZIP**, or clone it, and keep the helper files with the guide. Download CODESYS and its prerequisites from their vendors.

The extractor uses the InstallShield stream format examined with [ISx](https://github.com/lifenjoiner/ISx). The results above come from the test Mac's installation and verification logs. CODESYS has not endorsed this setup.
