<a name="readme-top"></a>

<!-- Top Links Bar -->

[![LinkedIn][linkedin-shield]][linkedin-url]
[![Instagram][instagram-shield]][instagram-url]

<!-- PROJECT LOGO -->
<br />

<div align="center">
  <img src="images/logo.png" alt="Logo" width="80" height="80">
  <h1 align="center">Pen and Paper Generators</h1>

  <p align="center">
    A collection of Python tools for generating materials for tabletop role-playing games
    <br />
    <a href="https://github.com/foxnoir/pen_and_paper_generators"><strong>Explore the generators »</strong></a>
    <br />
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#available-generators">Available Generators</a>
      <ul>
        <li><a href="#clan-sheet-generator">Clan Sheet Generator</a></li>
      </ul>
    </li>
    <li>
      <a href="#installation">Installation</a>
      <ul>
        <li><a href="#requirements">Requirements</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
    </li>
    <li>
      <a href="#contributing">Contributing</a>
    </li>
    <li>
      <a href="#technical-details">Technical Details</a>
    </li>
  </ol>
</details>

## About The Project

Pen and Paper Generators is a collection of Python tools designed to help players and game masters create professional materials for tabletop role-playing games. Each generator focuses on a specific aspect of game preparation, making it easier to create high-quality reference sheets, character materials, and other game resources.

**Key Features:**
- Multiple specialized generators for different game systems
- Professional output formats (PNG, PDF)
- High-resolution output suitable for printing
- Easy-to-use command-line interfaces
- Customizable templates and layouts

**Currently Available Generators:**
- **Clan Sheet Generator** - Generate clan reference sheets for Vampire: The Masquerade (2nd/3rd edition)

**Coming Soon:**
- More generators for various RPG systems
- Additional customization options
- Template library

<p align="right"><a href="#readme-top">back to top</a></p>

## Available Generators

### Clan Sheet Generator

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

For detailed documentation, see the [Clan Sheet Generator README](clan_sheet_generator/README.md).

<p align="right"><a href="#readme-top">back to top</a></p>

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

## Contributing

This project is open to contributions! If you'd like to add a new generator or improve an existing one:

1. Create a new directory for your generator
2. Follow the existing structure and naming conventions
3. Include a comprehensive README.md
4. Add a requirements.txt file
5. Test your generator thoroughly

<p align="right"><a href="#readme-top">back to top</a></p>

## Technical Details

- **Language**: Python 3.7+
- **Output Formats**: PNG, PDF
- **Resolution**: High-resolution output (typically 300 DPI)
- **Platform**: Cross-platform (macOS, Linux, Windows)

Each generator is self-contained and can be used independently. Check individual generator documentation for specific technical requirements.

<p align="right"><a href="#readme-top">back to top</a></p>

[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/tanja-polz-5636401a5/
[twitter-shield]: https://img.shields.io/badge/Twitter-%231DA1F2.svg?style=for-the-badge&logo=Twitter&logoColor=white
[twitter-url]: https://twitter.com/_foxnoir_?lang=de
[instagram-shield]: https://img.shields.io/badge/Instagram-%23E4405F.svg?style=for-the-badge&logo=Instagram&logoColor=white
[instagram-url]: https://www.instagram.com/codeincouture/
