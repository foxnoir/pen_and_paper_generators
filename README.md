<a name="readme-top"></a>

<!-- Top Links Bar -->

[![LinkedIn](assets/badges/linkedin.svg)](https://www.linkedin.com/in/tanja-polz-5636401a5/)
[![X](assets/badges/x.svg)](https://twitter.com/_foxnoir_?lang=de)
[![Instagram](assets/badges/instagram.svg)](https://www.instagram.com/codeincouture/)

<!-- PROJECT LOGO -->
<br />

<div align="center">
  <img src="assets/logo.png" alt="Logo" width="179" height="179">
  <h1 align="center">Pen and Paper Generators</h1>
  <p>
    A collection of Python tools for generating materials for tabletop role-playing games
  </p>
</div>

---

<div align="left">

[![Python](assets/badges/python.svg)](https://www.python.org/)
[![Pillow](assets/badges/pillow.svg)](https://pillow.readthedocs.io/)
[![PyMuPDF](assets/badges/pymupdf.svg)](https://pymupdf.readthedocs.io/)
[![PDF](assets/badges/pdf.svg)](https://www.iso.org/standard/75839.html)
[![PNG](assets/badges/png.svg)](https://www.libpng.org/pub/png/)
[![macOS](assets/badges/macos.svg)](https://www.apple.com/macos/)
[![Linux](assets/badges/linux.svg)](https://www.kernel.org/)
[![Windows](assets/badges/windows.svg)](https://www.microsoft.com/windows)

</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li>
      <a href="#available-generators">Available Generators</a>
      <ul>
        <li><a href="#clan-sheet-generator">Clan Sheet Generator</a></li>
        <li><a href="#sl-journal-generator">SL Journal Generator</a></li>
        <li><a href="#character-journal-generator">Character Journal Generator</a></li>
      </ul>
    </li>
    <li>
      <a href="#installation">Installation</a>
      <ul>
        <li><a href="#requirements">Requirements</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#technical-details">Technical Details</a></li>
    <li><a href="#badges">Badges</a></li>
  </ol>
</details>

---

## About The Project

Pen and Paper Generators is a collection of Python tools designed to help players and game masters create professional materials for tabletop role-playing games. Each generator focuses on a specific aspect of game preparation, making it easier to create high-quality reference sheets, character materials, and other game resources.

[![Python](assets/badges/python.svg)](https://www.python.org/)
[![PDF](assets/badges/pdf.svg)](https://www.iso.org/standard/75839.html)
[![PNG](assets/badges/png.svg)](https://www.libpng.org/pub/png/)

**Key Features:**
- Multiple specialized generators for different game systems
- Professional output formats (PNG, PDF)
- High-resolution output suitable for printing
- Easy-to-use command-line interfaces
- Customizable templates and layouts

**Currently Available Generators:**
- **[Clan Sheet Generator](clan_sheet_generator/README.md)** - Generate clan reference sheets for Vampire: The Masquerade (2nd/3rd edition)
- **[SL Journal Generator](SL_journal_generator/README.md)** - Generate dynamic PDF journals with interactive navigation for Vampire: The Masquerade sessions
- **[Character Journal Generator](character_journal_generator/README.md)** - Generate dynamic PDF journals with interactive navigation for character journals

**Coming Soon:**
- More generators for various RPG systems
- Additional customization options
- Template library

The root README stays short: a link and a rough summary per generator. Getting started and the detailed notes live in the README of that generator.

<p align="right"><a href="#readme-top">back to top</a></p>

---

## Available Generators

<h3>
  <a href="clan_sheet_generator/">Clan Sheet Generator »</a>
</h3>

Generate beautiful clan reference sheets for **Vampire: The Masquerade** (2nd/3rd edition). Create professional-looking reference sheets for any clan with customizable content.

**Features:**
- Generate clan sheets for any Vampire: The Masquerade clan
- Professional layout with customizable sections
- Support for multiple clans (Brujah, Malkavianer, Toreador, etc.)
- Outputs both PNG and PDF formats
- High-resolution output (300 DPI)
- Customizable CLANESSENZ (clan essence/philosophy statement)

**Quick Start:**
```bash
cd clan_sheet_generator
python3 clan_sheet_gen.py --clan BRUJAH --quick
```

[README »](clan_sheet_generator/README.md)

<h3>
  <a href="SL_journal_generator/">SL Journal Generator »</a>
</h3>

Generate dynamic PDF journals with interactive navigation tabs for **Vampire: The Masquerade** sessions. Create professional-looking session journals with customizable structure and clickable navigation.

**Key Features:**
- Dynamic PDF generation from JSON structure
- Interactive navigation (right-side vertical tabs and top-left horizontal tabs)
- Customizable tab structure (tabs, subsections, sub-subsections)
- Modern design with jade green color scheme
- Hyperlink support for easy navigation

**Quick Start:**
```bash
cd SL_journal_generator
python3 journal_generator.py
```

[README »](SL_journal_generator/README.md)

<h3>
  <a href="character_journal_generator/">Character Journal Generator »</a>
</h3>

Generate dynamic PDF journals with interactive navigation tabs for **character journals**. Create professional-looking character journals with customizable structure and clickable navigation.

**Key Features:**
- Dynamic PDF generation from JSON structure
- Interactive navigation (right-side vertical tabs and top-left horizontal tabs)
- Customizable tab structure (tabs, subsections, sub-subsections)
- Modern design with jade green color scheme
- Hyperlink support for easy navigation

**Quick Start:**
```bash
cd character_journal_generator
python3 journal_generator.py
```

[README »](character_journal_generator/README.md)

<p align="right"><a href="#readme-top">back to top</a></p>

---

## Installation

**Important:** If you're using a virtual environment (`.venv`), install the packages there!

### Requirements

Each generator has its own requirements. Navigate to the generator's directory and install dependencies:

```bash
# Example for Clan Sheet Generator
cd clan_sheet_generator
pip install -r requirements.txt

# Or in virtual environment:
.venv/bin/pip install -r requirements.txt
```

See each generator's `requirements.txt` file for specific dependencies.

<p align="right"><a href="#readme-top">back to top</a></p>

---

## Usage

Each generator is located in its own directory and can be run independently:

```bash
# Navigate to the generator directory
cd clan_sheet_generator

# Run the generator (see generator-specific README for options)
python3 clan_sheet_gen.py --help
```

For detailed usage instructions, see each generator's README file.

<p align="right"><a href="#readme-top">back to top</a></p>

---

## Contributing

This project is open to contributions! If you'd like to add a new generator or improve an existing one:

1. Create a new directory for your generator
2. Follow the existing structure and naming conventions
3. Include a comprehensive README.md
4. Add a requirements.txt file
5. Test your generator thoroughly

<p align="right"><a href="#readme-top">back to top</a></p>

---

## Technical Details

- **Language**: Python 3.7+
- **Output Formats**: PNG, PDF
- **Resolution**: High-resolution output (typically 300 DPI)
- **Platform**: Cross-platform (macOS, Linux, Windows)

Each generator is self-contained and can be used independently. Check individual generator documentation for specific technical requirements.

<p align="right"><a href="#readme-top">back to top</a></p>

---

## Badges

Tech-stack and social badges live once in [`assets/badges/`](assets/badges/). After changing labels or colors:

```
python3 assets/badges/generate.py
```

Target URLs sit **on the badge line** (`[![Python](assets/badges/python.svg)](https://www.python.org/)`). GitHub cannot import another file into a README, so there is no footer of `[python-url]:` refs. The href list is [`assets/badges/links.json`](assets/badges/links.json) when you add a badge.

Every badge is a vertical dark → mid → light gradient (same contrast as Instagram). The mid stop is the brand or project color. Official colors stay official, except black — it is hard to see. Everything else uses purple, blue, turquoise, pink, or green — not black, orange, red, or yellow.

| File | Color (dark → mid → light) | Why |
| --- | --- | --- |
| `python.svg` | `#1E415E` → `#3776AB` → `#97B8D3` | official Python |
| `pillow.svg` | `#194C4A` → `#2D8A86` → `#92C2C0` | teal |
| `pymupdf.svg` | `#012F55` → `#02569B` → `#7BA7CB` | blue (PDF tooling) |
| `pdf.svg` | `#294D3D` → `#4A8C6F` → `#A1C3B4` | green |
| `png.svg` | `#343A5C` → `#5E6AA8` → `#ABB2D2` | blue-violet |
| `macos.svg` | `#2A656C` → `#4DB8C4` → `#A2DAE0` | pastel turquoise |
| `linux.svg` | `#17564F` → `#2A9D8F` → `#90CCC5` | turquoise |
| `windows.svg` | `#01406B` → `#0175C2` → `#7BB7DF` | blue |
| `linkedin.svg` | `#06386B` → `#0A66C2` → `#80AFDF` | official LinkedIn |
| `instagram.svg` | `#4C3469` → `#8B5FBF` → `#C3ACDE` | lilac |
| `x.svg` | `#456576` → `#7EB8D6` → `#BCDAEA` | pastel light blue |

<p align="right"><a href="#readme-top">back to top</a></p>
