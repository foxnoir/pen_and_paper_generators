<a name="readme-top"></a>

<!-- Top Links Bar -->

[![LinkedIn][linkedin-shield]][linkedin-url]
[![Instagram][instagram-shield]][instagram-url]

<!-- PROJECT LOGO -->
<br />

<div align="center">
  <img src="../images/logo.png" alt="Logo" width="80" height="80">
  <h1 align="center">Small Character Journal Generator</h1>

  <p align="center">
    Generate dynamic PDF journals with interactive navigation for compact character journals
    <br />
    <a href="https://github.com/foxnoir/pen_and_paper_generators"><strong>Explore the project »</strong></a>
    <br />
  </p>
</div>

<Dossier>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#features">Features</a>
    </li>
    <li>
      <a href="#installation">Installation</a>
      <ul>
        <li><a href="#requirements">Requirements</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#basic-usage">Basic Usage</a></li>
        <li><a href="#configuration">Configuration</a></li>
        <li><a href="#customizing-tabs">Customizing Tabs</a></li>
      </ul>
    </li>
    <li>
      <a href="#file-structure">File Structure</a>
    </li>
    <li>
      <a href="#technical-Dossier">Technical Dossier</a>
    </li>
    <li>
      <a href="#customization">Customization</a>
    </li>
    <li>
      <a href="#troubleshooting">Troubleshooting</a>
    </li>
  </ol>
</Dossier>

## About The Project

The Small Character Journal Generator creates a compact, fully navigable PDF character journal from JSON configuration and uploaded background images. This restructured edition replaces the older monolithic layout with a modular tab system, dedicated image folders, and configurable cover typography.

The current journal includes sections such as **Charakter** (Dossier, Ressourcen, Vorgeschichte), **Netzwerk**, **Domäne**, **Sitzungen**, **Impressionen**, **Gefallen**, and **Offene Fragen** — with nested navigation (for example Inspiration under Dossier with Ja / Nein / Vielleicht / Schuld / Loyalität / Sonstiges).

![Example Journal](../images/exmple.png)

> **Note:** This is part of the [Pen and Paper Generators](../README.md) project. For an overview of all available generators, see the main [README](../README.md).

**Key Features:**
- Dynamic PDF generation from `tab_structure.json` and `cover_pages.json`
- Interactive navigation (right-side vertical tabs and top-left horizontal tabs)
- Background images from `assets/images/` (folder-based random picks and fixed sequences)
- Custom cover fonts and colors (Whispering Signature, Alex Brush)
- Hyperlink support for easy navigation

<p align="right"><a href="#readme-top">back to top</a></p>

## Features

- **Dynamic PDF Generation**: Builds the full journal (~380+ pages) from JSON structure and cover configuration
- **Interactive Navigation**: Right-side vertical tabs and top-left horizontal tabs (up to three rows for nested sub-subsections)
- **Image-Driven Layout**: Backgrounds from `assets/images/` — dossier, contacts, allies, enemies, weapons, audio, refuge, inspiration, impressions, and more
- **Smart Random Backgrounds**: `random_*` keywords pick from matching folders; the same image never appears on two consecutive pages
- **Sequence Backgrounds**: Special keywords such as `impressions_once` and `refuge_once` for ordered or folder-based page sequences
- **Dynamic Tab Sizing**: Right tab height is calculated from label length with uniform spacing
- **Cover Typography**: Main and sub-section covers use configurable fonts, colors, and golden-ratio text placement
- **Modern Design**: Beige tab scheme, rounded upper tabs, and professional layout
- **Hyperlink Support**: All tabs are clickable and navigate to their respective pages

<p align="right"><a href="#readme-top">back to top</a></p>

## Installation

**Important:** If you're using a virtual environment (`.venv`), install the packages there!

### Requirements

- Python 3.7+
- PyMuPDF>=1.23.0
- Pillow (for image compression)

Install dependencies:
```bash
cd small_character_journal_generator
pip install -r requirements.txt

# Or in virtual environment:
.venv/bin/pip install -r requirements.txt
```

<p align="right"><a href="#readme-top">back to top</a></p>

## Usage

### Basic Usage

Run the generator:
```bash
cd small_character_journal_generator
python3 journal_generator.py
```

This will:
- Load the structure from `tab_structure.json`
- Load page backgrounds and cover settings from `cover_pages.json`
- Scan image folders under `assets/images/` (e.g. dossier, refuge, inspiration, impressions)
- Generate `character_journal.pdf` with all tabs, covers, and backgrounds

### Configuration

The journal is controlled by two JSON files:

#### `tab_structure.json`

Defines navigation and page counts:

- **Right-side tabs**: Vertical navigation along the right edge (Charakter, Netzwerk, Domäne, …)
- **Subsections**: First row of upper tabs (e.g. Dossier, Ressourcen under Charakter)
- **Sub-subsections**: Second (and third) row of upper tabs — supports nested entries (e.g. Inspiration with child tabs)
- **Metadata**: Page dimensions, tab width, start position, and spacing

#### `cover_pages.json`

Defines backgrounds and cover pages per section:

- **`cover_pages`**: Main tab covers, subsection covers, and per-page `page_1` … `page_N` entries
- **`sub_subsections`**: Background images for each sub-subsection page
- **`default_font`** / **`text_position`**: Cover title sizing and placement
- **Background keywords**: `random_dossier`, `random_contacts`, `random_audio`, `refuge_once`, `impressions_once`, or explicit paths like `assets/images/refuge/1.png`

#### JSON Structure

The tab structure follows this pattern:

```json
{
    "right_tabs": [
        {
            "name": "Charakter",
            "subsections_left_top_tabs": [
                {
                    "name": "Dossier",
                    "seconnd_subsections_left_tabs": [
                        "Steckbrief",
                        "Wahnsinn",
                        {
                            "name": "Inspiration",
                            "seconnd_subsections_left_tabs": ["Ja", "Nein", "Vielleicht", "Sonstiges"]
                        }
                    ]
                },
                {
                    "name": "Sitzungen",
                    "page_count": 1,
                    "seconnd_subsections_left_tabs": []
                }
            ]
        },
        {
            "name": "Impressionen",
            "page_count": 19,
            "subsections_left_top_tabs": []
        }
    ],
    "upper_tabs": [],
    "metadata": {
        "page_width": 595.2755737304688,
        "page_height": 841.8897705078125,
        "tab_width": 35.0,
        "right_tab_x_position": 560.2755737304688,
        "right_tab_start_y": 65.0,
        "right_tab_spacing": 8.0,
        "upper_tabs_position": {
            "x": 10.0,
            "y": 20.0
        }
    }
}
```

### JSON Logic and Field Reference

#### Right-Side Tabs (`right_tabs`)

Each right-side tab object can contain:

- **`name`** (required): Tab label displayed vertically (rotated 270°)
- **`page_count`** (optional): Number of pages for tabs without subsections (e.g. Impressionen, Offene Fragen)
- **`subsections_left_top_tabs`** (optional): Array of subsection objects that appear as upper tabs
- **`seconnd_subsections_left_tabs`** (optional): Array of strings for direct sub-subsections (if no subsections)

Tab **height** and **Y position** are calculated automatically from the label length and `right_tab_spacing` in metadata (no manual `height` / `y_position` required).

#### Subsections (`subsections_left_top_tabs`)

Each subsection object can contain:

- **`name`** (required): Subsection label displayed horizontally in the first row
- **`page_count`** (optional): Pages for flat subsections without sub-subsections (e.g. Plan & Ziele with 50 pages)
- **`seconnd_subsections_left_tabs`** (optional): Array of strings **or nested objects** for sub-subsections (second/third upper tab rows)
- **`sub_subsections`** (optional): Alternative field name for sub-subsections
- **`keywords`** (optional): Reserved for keyword-based page detection

Nested sub-subsection example (third tab row when parent is active):

```json
{
    "name": "Inspiration",
    "seconnd_subsections_left_tabs": ["Ja", "Nein", "Vielleicht", "Sonstiges"]
}
```

**Note:** The generator checks `seconnd_subsections_left_tabs`, `sub_subsections`, and `second_subsections_left_tabs`.

#### Page Generation Logic

1. **Main tab page**: First page for each right tab
2. **Additional tab pages**: When `page_count` > 1 (multi-page tabs like Impressionen)
3. **Subsection pages**: Cover page plus optional `page_count` pages
4. **Sub-subsection pages**: Count derived from `cover_pages.json` (`page_1` … `page_N`) or defaults

Impressionen page count is synced automatically from `assets/images/impressions/` (+ 10 dossier pages).

#### Metadata (`metadata`)

- **`page_width`**: Page width in points (default: 595.28 for A4)
- **`page_height`**: Page height in points (default: 841.89 for A4)
- **`tab_width`**: Width of right-side tabs in points (default: 35.0)
- **`right_tab_x_position`**: X position of right-side tabs
- **`right_tab_start_y`**: Top offset for the first right tab (default: 65.0)
- **`right_tab_spacing`**: Vertical gap between right tabs in points (default: 8.0)
- **`upper_tabs_position`**: Object with `x` and `y` for upper-left tabs

### Customizing Tabs

**Right-side tabs** in `tab_structure.json`:
- `name`: Tab label (vertical, Alex Brush)
- `subsections_left_top_tabs`: Subsections as upper tabs
- `page_count`: For tabs without subsections

**Backgrounds** in `cover_pages.json`:
- Explicit paths: `"background_image": "assets/images/eps/1.png"`
- Folder random: `"background_image": "random_contacts"` → `assets/images/contacts/`
- Dossier random: `"random_dossier"` → `assets/images/dossier/`
- Sequences: `"impressions_once"`, `"refuge_once"`

**Image folders** (add PNG/JPG files; the generator picks them up dynamically):

| Folder | Used for |
|--------|----------|
| `dossier/` | Default random backgrounds |
| `contacts/`, `allies/`, `enemies/` | Netzwerk |
| `weapons/`, `favors/` | Ressourcen, Gefallen |
| `audio/` | Sitzungen → Aufnahmen |
| `refuge/` | Zufluchten (first images via `refuge_once`, then random) |
| `inspiration/` | Inspiration sub-tabs (yes/no/maybe images) |
| `impressions/` | Impressionen (fixed order 1,3,4,5,6 + random rest + dossier) |
| `research/` | Vorgeschichte → Archiv |
| `section_cover/` | Main and sub-section cover backgrounds |

### Output

The generator creates `character_journal.pdf` with:
- All pages dynamically generated from JSON structure and image assets
- Interactive navigation tabs (right-side and top-left)
- Section cover pages with custom typography
- Proper hyperlinks between pages

<p align="right"><a href="#readme-top">back to top</a></p>

## File Structure

```
small_character_journal_generator/
├── journal_generator.py       # Main generator script
├── layout_generator.py        # Layout, tabs, covers, random backgrounds
├── content_processor.py       # Content extraction and processing
├── tab_structure.json         # Tab hierarchy and page counts
├── cover_pages.json           # Backgrounds, covers, fonts, text positions
├── character_journal.pdf      # Generated output
├── assets/
│   ├── fonts/
│   │   ├── alex.ttf                    # Upper tab labels
│   │   └── WhisperingSignature.ttf     # Cover page titles
│   └── images/
│       ├── dossier/           # Random dossier backgrounds
│       ├── contacts/          # Netzwerk → Kontakte
│       ├── allies/            # Netzwerk → Verbündete
│       ├── enemies/           # Netzwerk → Feinde
│       ├── weapons/           # Waffen
│       ├── favors/            # Gefallen
│       ├── audio/             # Aufnahmen
│       ├── refuge/            # Zufluchten
│       ├── inspiration/       # Inspiration (Ja/Nein/Vielleicht)
│       ├── impressions/       # Impressionen
│       ├── research/          # Archiv
│       ├── section_cover/     # main_cover.png, sub_section_cover.png
│       └── …                  # calendar, crazy, eps, domain, etc.
└── requirements.txt           # Python dependencies
```

<p align="right"><a href="#readme-top">back to top</a></p>

## Technical Dossier

- **PDF Library**: PyMuPDF (fitz)
- **Image Processing**: Pillow (compression before embed)
- **Page Format**: A4 (595.28 x 841.89 points)
- **Tab Colors**: Beige/cream scheme (`#EEDCC8` inactive, `#D0C4B4` active) in `layout_generator.py`
- **Tab Label Font**: Alex Brush (`assets/fonts/alex.ttf`)
- **Cover Font**: Whispering Signature (`assets/fonts/WhisperingSignature.ttf`)
- **Cover Text Colors**: Main cover `#514328`, sub-section cover `#43201F`
- **Cover Text Position**: Golden-ratio anchor with offsets from `cover_pages.json` → `text_position`
- **Language**: Python 3.7+
- **Output Format**: PDF
- **Platform**: Cross-platform (macOS, Linux, Windows)

<p align="right"><a href="#readme-top">back to top</a></p>

## Customization

### Tab Colors

Edit `layout_generator.py` to change tab colors:
```python
self.tab_colors = {
    "background": (238 / 255, 220 / 255, 200 / 255),  # #EEDCC8 (inactive)
    "active": (208 / 255, 196 / 255, 180 / 255),      # #D0C4B4 (active)
    "border": (208 / 255, 196 / 255, 180 / 255),
    "text": (0.15, 0.15, 0.15),
    "shadow": (200 / 255, 190 / 255, 175 / 255)
}
```

### Cover Fonts and Colors

Cover typography is configured in `layout_generator.py`:

```python
MAIN_COVER_TEXT_COLOR_HEX = "#514328"           # main_cover.png sections
SUB_SECTION_COVER_TEXT_COLOR_HEX = "#43201F"    # sub_section_cover.png sections
COVER_GOLDEN_RATIO_PHI = (1.0 + math.sqrt(5.0)) / 2.0
```

Font sizes and vertical offsets are set in `cover_pages.json`:

```json
"default_font": {
    "title_size": 48,
    "subtitle_size": 24,
    "description_size": 14
},
"text_position": {
    "title_y_offset": 0,
    "subtitle_y_offset": 40,
    "description_y_offset": 85
}
```

Sub-section cover titles render slightly smaller than main covers (automatic scale in `layout_generator.py`).

Replace `assets/fonts/alex.ttf` or `assets/fonts/WhisperingSignature.ttf` to change tab or cover typefaces.

### Random Background Keywords

Add or use entries in `RANDOM_FOLDER_MAP` inside `layout_generator.py`:

```python
"random_refuge": ("refuge",),
"random_audio": ("audio",),
```

Then reference them in `cover_pages.json` as `"background_image": "random_refuge"`.

<p align="right"><a href="#readme-top">back to top</a></p>

## Troubleshooting

**Issue**: Tabs are cut off or overlapping
- **Solution**: Adjust `max_width` in `layout_generator.py` or reduce upper-tab label length

**Issue**: Right tab too large/small for its label
- **Solution**: Tab height is auto-calculated; adjust `right_tab_vertical_padding` or `right_tab_label_max_font` in `layout_generator.py`

**Issue**: Background image not found
- **Solution**: Check path in `cover_pages.json` and that the file exists under `assets/images/` (Unicode filenames on macOS are normalized automatically)

**Issue**: Same random image on consecutive pages
- **Solution**: Should not occur — the generator tracks the last pick globally; if a folder contains only one image, repetition is unavoidable

**Issue**: Page count mismatch (section shorter than expected)
- **Solution**: Align `page_count` in `tab_structure.json` with the highest `page_N` key in `cover_pages.json` for that section

**Issue**: PDF generation fails
- **Solution**: Validate both JSON files; ensure PyMuPDF and Pillow are installed

<p align="right"><a href="#readme-top">back to top</a></p>

## License

See [LICENSE](../LICENSE) file for Dossier.

<p align="right"><a href="#readme-top">back to top</a></p>

[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/tanja-polz-5636401a5/
[twitter-shield]: https://img.shields.io/badge/Twitter-%231DA1F2.svg?style=for-the-badge&logo=Twitter&logoColor=white
[twitter-url]: https://twitter.com/_foxnoir_?lang=de
[instagram-shield]: https://img.shields.io/badge/Instagram-%23E4405F.svg?style=for-the-badge&logo=Instagram&logoColor=white
[instagram-url]: https://www.instagram.com/codeincouture/
