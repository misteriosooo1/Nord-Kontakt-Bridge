# Nord Kontakt Bridge

## Windows installer

The Windows Installer and Portable executables include the `nord.exe` decoder from `bin/`, so end users do not have to install Python, Rust, or Cargo separately. Use `SUPORTE_RECUPERACAO/FERRAMENTAS_COMPILACAO/GERAR_PORTABLE_E_INSTALLER.bat` on Windows (requires Python and Inno Setup only on the build machine), or use the included GitHub Actions workflow. See `SUPORTE_RECUPERACAO/DOCUMENTACAO/INSTALADOR_LEIA_PRIMEIRO.md`.


**Turn your Nord piano instruments into Kontakt 8 libraries, your way.**

**Nord Kontakt Bridge** was created to make preparing and converting **Nord** piano instruments for **Kontakt 8** easier. It takes compatible **Nord Piano Library** `.npno` files and helps create `.nki` instruments, the format used by Kontakt.

The application is intended exclusively for compatible Nord piano `.npno` files. It does not convert `.npmo`, `.nsmp`, other manufacturers' formats, or files that have simply been renamed.

With a straightforward interface, Nord Kontakt Bridge brings together the tools needed to prepare, convert, and customize your instrument—even if this is your first time using the application.

### How does it work?

Start by selecting the Nord `.npno` piano file you want to convert, entering an instrument name, choosing an output folder, and locating the installed `Kontakt 8.exe` executable.

Conversion requires **Kontakt 8 (standalone)** and a compatible Nord decoder (`nord.exe`, distributed separately). The application prepares the necessary audio files and scripts; Kontakt is involved in creating the final `.nki` file.

You can also select a valid `.nkr` resource file if you already have a compatible resource template. **An `.nkr` file is not necessarily included in the distribution** and should not be confused with the original `.npno` piano file.

Once you have configured the required options, start the process to prepare and create your `.nki` instrument for Kontakt 8.

### Customize your instrument

In addition to conversion, Nord Kontakt Bridge provides tools to customize the appearance and behavior of your library.

You can choose your own **wallpaper**, **instrument icon**, and **library cover**, supply a **custom KSP script**, and design the effect controls using the **FX Editor**.

The FX Editor lets you customize knob designs, effect names, fonts, colors, titles, and **Piano / FX** pages so the interface matches your preferences.

**All these customizations are optional.** You do not need to create artwork or know how to program to get started. The application provides default settings for new users.

If you do not select custom images, Nord Kontakt Bridge automatically uses its default wallpaper and icon.

### Library Manager integration

The application also includes an option to **prepare files for Library Manager**, including identification and presentation resources for the library.

**We recommend leaving this option enabled.** It makes the later library-addition step easier, but you still need to add the library manually in Library Manager; this option does not register it automatically.

### Ready to get started?

Nord Kontakt Bridge lets you prepare Kontakt 8 `.nki` instruments from compatible Nord `.npno` piano files, while giving you the freedom to customize your library's appearance.

**Choose your Nord instrument, set your preferences, and start converting!**

### Application screenshots

**1. Conversion —** Select your Nord file, enter an instrument name, choose an output directory, and locate Kontakt 8.

![Nord Kontakt Bridge - Conversion screen in English](screenshots/en-conversion.png)

**2. Visual Design —** Customize the wallpaper, instrument icon, library cover, and other appearance settings.

![Nord Kontakt Bridge - Visual Design screen in English](screenshots/en-visual-design.png)

**3. FX Editor —** Customize effects, knobs, titles, colors, fonts, and Piano / FX pages.

![Nord Kontakt Bridge - FX Editor screen in English](screenshots/en-fx-editor.png)

### Downloads and requirements

Download the executable you prefer from this repository's **Releases** section:

- **`Nord Kontakt Bridge Portable.exe`** — runs on Windows without installation or Python.
- **`Nord Kontakt Bridge Installer.exe`** — installs the app, shortcuts and an uninstaller.

**Requirements:** Windows, Kontakt 8 standalone, a compatible `.npno` piano file and the separately obtained `nord.exe` decoder. Kontakt 8 and the decoder are not bundled. Conversion may not work without a configured decoder.

Run either EXE. For your first conversion, select the Nord piano file, instrument name, output folder, and the `Kontakt 8.exe` path.

> **Disclaimer:** Nord Kontakt Bridge is an independent project and is not officially affiliated with Nord or Native Instruments. It does not include Kontakt 8, commercial Nord instruments, an external decoder, or third-party licenses.
