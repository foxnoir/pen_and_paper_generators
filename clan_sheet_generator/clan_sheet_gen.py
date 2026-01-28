#!/usr/bin/env python3
"""
Unified Clan Sheet Generator
Generates clan sheets for any Vampire: The Masquerade clan (2nd/3rd edition)

Vampire: The Masquerade is a trademark of White Wolf Entertainment AB.
This tool is not affiliated with or endorsed by White Wolf Entertainment AB.
Assets ({clan_name}.png logos or clan_name.png, watermark.png) are property of White Wolf Entertainment AB.
"""

import argparse
import os
import sys
from clan_sheet import ClanSheetGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Generate a clan sheet for Vampire: The Masquerade (2nd/3rd edition)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 clan_sheet_gen.py --clan BRUJAH --interactive
  
  # Using generic files
  python3 clan_sheet_gen.py --clan BRUJAH --input example_input.txt --clanessenz example_clanessenz.txt
  
  # Quick generation with default files (tries clan-specific, then generic)
  python3 clan_sheet_gen.py --clan BRUJAH --quick
        """
    )
    
    parser.add_argument(
        '--clan',
        type=str,
        required=True,
        help='Clan name (e.g., BRUJAH, MALKAVIANER, TOREADOR)'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        help='Path to input text file with clan sections (optional, defaults to {clan}_example_input.txt)'
    )
    
    parser.add_argument(
        '--clanessenz',
        type=str,
        help='Path to CLANESSENZ text file (optional, defaults to {clan}_clanessenz.txt)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for generated files (default: current directory)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode: use default file names ({clan}_example_input.txt and {clan}_clanessenz.txt)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive mode: enter text manually'
    )
    
    args = parser.parse_args()
    
    clan_name = args.clan.upper()
    
    # Determine input source
    if args.interactive:
        # Interactive mode
        print("=" * 60)
        print("CLAN SHEET GENERATOR")
        print("=" * 60)
        print()
        print(f"Generating sheet for clan: {clan_name}")
        print()
        print("Please enter the text for the sections.")
        print("Use the following headers (all UPPERCASE):")
        print(f"- {clan_name} INFOBOX")
        print(f"- {clan_name} KURZÜBERBLICK")
        print(f"- {clan_name} SPEZIFISCHE SCHWÄCHE")
        if clan_name == "MALKAVIANER":
            print(f"- {clan_name} DAS MALKAVIANER-NETZWERK")
        print(f"- {clan_name} CLANHALTUNG & ROLLE")
        print(f"- {clan_name} BEZIEHUNGEN")
        print(f"- {clan_name} INTERNE SPANNUNGEN")
        print(f"- {clan_name} DISZIPLINEN")
        print()
        print("Enter the text.")
        print("Tip: You can paste the text with all headers at once.")
        print("End input with 'ENDE' on a new line:")
        print()
        
        lines = []
        while True:
            try:
                line = input()
                line_stripped = line.strip().upper()
                
                if line_stripped == "ENDE":
                    break
                
                lines.append(line)
            except EOFError:
                break
        
        user_text = '\n'.join(lines)
        
        print()
        clanessenz = input("Please enter the CLANESSENZ: ").strip()
        if not clanessenz:
            print("Warning: No CLANESSENZ provided. Using default.")
            clanessenz = f"{clan_name} feel first – and act then."
    
    elif args.quick or args.input or args.clanessenz:
        # File-based mode
        # Determine input file
        if args.input:
            input_file = args.input
        else:
            # Try clan-specific first, then generic
            clan_specific = f"{clan_name.lower()}_example_input.txt"
            if os.path.exists(clan_specific):
                input_file = clan_specific
            else:
                input_file = "example_input.txt"
        
        # Determine CLANESSENZ file
        if args.clanessenz:
            clanessenz_file = args.clanessenz
        else:
            # Try clan-specific first, then generic
            clan_specific = f"{clan_name.lower()}_clanessenz.txt"
            if os.path.exists(clan_specific):
                clanessenz_file = clan_specific
            else:
                clanessenz_file = "example_clanessenz.txt"
        
        # Read input file
        if not os.path.exists(input_file):
            print(f"Error: Input file not found: {input_file}")
            sys.exit(1)
        
        with open(input_file, 'r', encoding='utf-8') as f:
            user_text = f.read()
        
        # Read CLANESSENZ file
        if not os.path.exists(clanessenz_file):
            print(f"Warning: CLANESSENZ file not found: {clanessenz_file}")
            print("Using default CLANESSENZ.")
            clanessenz = f"{clan_name} feel first – and act then."
        else:
            with open(clanessenz_file, 'r', encoding='utf-8') as f:
                clanessenz = f.read().strip()
    
    else:
        # Default: try quick mode
        # Try clan-specific first, then generic
        clan_specific_input = f"{clan_name.lower()}_example_input.txt"
        generic_input = "example_input.txt"
        
        if os.path.exists(clan_specific_input):
            input_file = clan_specific_input
        elif os.path.exists(generic_input):
            input_file = generic_input
        else:
            print(f"Error: Input file not found. Tried: {clan_specific_input} and {generic_input}")
            print("Use --interactive to enter text manually, or --input to specify a file.")
            sys.exit(1)
        
        with open(input_file, 'r', encoding='utf-8') as f:
            user_text = f.read()
        
        # Try clan-specific first, then generic
        clan_specific_clanessenz = f"{clan_name.lower()}_clanessenz.txt"
        generic_clanessenz = "example_clanessenz.txt"
        
        if os.path.exists(clan_specific_clanessenz):
            with open(clan_specific_clanessenz, 'r', encoding='utf-8') as f:
                clanessenz = f.read().strip()
        elif os.path.exists(generic_clanessenz):
            with open(generic_clanessenz, 'r', encoding='utf-8') as f:
                clanessenz = f.read().strip()
        else:
            print(f"Warning: CLANESSENZ file not found. Tried: {clan_specific_clanessenz} and {generic_clanessenz}")
            clanessenz = f"{clan_name} feel first – and act then."
    
    # Create generator
    generator = ClanSheetGenerator(clan_name)
    
    # Parse text
    sections = generator.parse_user_input(user_text)
    
    if not sections:
        print("Error: No sections found in input text.")
        print("Make sure you're using the correct section headers.")
        sys.exit(1)
    
    # Generate sheet
    print()
    print(f"Generating {clan_name} clan sheet...")
    sheet = generator.generate_sheet(sections, clanessenz)
    
    # Save files
    output_base = os.path.join(args.output_dir, f"{clan_name.lower()}_clan_sheet")
    
    # PNG
    png_filename = f"{output_base}.png"
    sheet.save(png_filename, "PNG", dpi=(300, 300))
    print(f"Clan sheet saved as: {png_filename}")
    
    # PDF
    try:
        pdf_filename = f"{output_base}.pdf"
        sheet.save(pdf_filename, "PDF", resolution=300.0)
        print(f"Clan sheet also saved as PDF: {pdf_filename}")
    except Exception as e:
        print(f"Note: PDF could not be created: {e}")


if __name__ == "__main__":
    main()
