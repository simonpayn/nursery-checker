#!/usr/bin/env python3
"""
Nursery Inventory Query Tool
A flexible query tool for nursery inventory management.
Supports both CSV and Excel (.xls/.xlsx) files.
"""

import argparse
import os
import sys
import pandas as pd
from tabulate import tabulate


def load_excel_inventory(file_path):
    """Load inventory from an Excel file with multiple category sheets.

    Each sheet represents a category. The first row containing 'Botanical'
    is treated as a header row and skipped. The sheet name becomes the
    Category column.
    """
    xls = pd.ExcelFile(file_path)

    column_map = {
        0: 'Botanical name',
        1: 'CommonNames',
        2: 'ProductSKU',
        3: 'OnHand',
        4: 'Price',
        5: 'VolumePrice',
        6: 'Order',
    }

    frames = []
    for sheet in xls.sheet_names:
        raw = pd.read_excel(xls, sheet_name=sheet, header=None)

        # Find the header row (contains "Botanical") and skip it
        header_idx = None
        for i in range(min(5, len(raw))):
            if raw.iloc[i].astype(str).str.contains('Botanical', case=False, na=False).any():
                header_idx = i
                break

        if header_idx is not None:
            data = raw.iloc[header_idx + 1:].reset_index(drop=True)
        else:
            data = raw.copy()

        # Rename columns by position
        data.columns = range(len(data.columns))
        data = data.rename(columns=column_map)

        # Add category from sheet name
        data['Category'] = sheet

        # Convert numeric columns
        data['OnHand'] = pd.to_numeric(data['OnHand'], errors='coerce').fillna(0).astype(int)
        data['Price'] = pd.to_numeric(data['Price'], errors='coerce')
        data['VolumePrice'] = pd.to_numeric(data['VolumePrice'], errors='coerce')

        frames.append(data)

    if not frames:
        return None

    return pd.concat(frames, ignore_index=True)


class InventoryQuery:
    def __init__(self, file_path):
        """Initialize with a CSV or Excel file path."""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ('.xls', '.xlsx'):
                self.df = load_excel_inventory(file_path)
                if self.df is None:
                    raise Exception("No data found in Excel file")
            else:
                # CSV loading with encoding fallback
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                self.df = None
                for encoding in encodings:
                    try:
                        self.df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                if self.df is None:
                    raise Exception("Could not decode CSV with any supported encoding")

            self.file_path = file_path
            print(f"Loaded {len(self.df)} records from {file_path}")
            print(f"Columns: {', '.join(self.df.columns)}\n")
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)
        except pd.errors.EmptyDataError:
            print(f"Error: File '{file_path}' is empty.")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading file: {e}")
            sys.exit(1)

    def show_all(self):
        """Display all records."""
        return self.df

    def search(self, term):
        """Search for a term across all columns."""
        mask = self.df.astype(str).apply(
            lambda row: row.str.contains(term, case=False, na=False).any(),
            axis=1
        )
        return self.df[mask]

    def filter_by_column(self, filters):
        """
        Filter by column conditions.

        Args:
            filters: List of filter strings in format "column=value" or "column>value" etc.
        """
        result = self.df.copy()

        for filter_str in filters:
            # Parse the filter
            operators = ['>=', '<=', '!=', '>', '<', '=']
            operator = None
            column = None
            value = None

            for op in operators:
                if op in filter_str:
                    parts = filter_str.split(op, 1)
                    if len(parts) == 2:
                        column = parts[0].strip()
                        value = parts[1].strip()
                        operator = op
                        break

            if not operator or column not in self.df.columns:
                print(f"Warning: Invalid filter '{filter_str}' - skipping")
                continue

            # Apply the filter
            try:
                if operator == '=':
                    # String comparison (case-insensitive)
                    result = result[result[column].astype(str).str.contains(value, case=False, na=False)]
                elif operator == '!=':
                    result = result[result[column].astype(str).str.contains(value, case=False, na=False) == False]
                else:
                    # Numeric comparison
                    numeric_value = pd.to_numeric(value)
                    numeric_column = pd.to_numeric(result[column], errors='coerce')

                    if operator == '>':
                        result = result[numeric_column > numeric_value]
                    elif operator == '<':
                        result = result[numeric_column < numeric_value]
                    elif operator == '>=':
                        result = result[numeric_column >= numeric_value]
                    elif operator == '<=':
                        result = result[numeric_column <= numeric_value]
            except Exception as e:
                print(f"Warning: Error applying filter '{filter_str}': {e}")
                continue

        return result

    def display(self, df, max_rows=None):
        """Display a dataframe in a nice table format."""
        if df.empty:
            print("No records found.")
            return

        display_df = df if max_rows is None else df.head(max_rows)
        print(tabulate(display_df, headers='keys', tablefmt='grid', showindex=False))

        if max_rows and len(df) > max_rows:
            print(f"\n... showing {max_rows} of {len(df)} records")
        else:
            print(f"\nTotal records: {len(df)}")

    def export(self, df, output_path):
        """Export filtered results to a new CSV file."""
        try:
            df.to_csv(output_path, index=False)
            print(f"Exported {len(df)} records to {output_path}")
        except Exception as e:
            print(f"Error exporting: {e}")

    def interactive_mode(self):
        """Start an interactive query session."""
        print("=== Interactive Mode ===")
        print("Commands:")
        print("  all                    - Show all records")
        print("  search <term>          - Search across all columns")
        print("  filter <col>=<val>     - Filter by column (supports =, !=, >, <, >=, <=)")
        print("  columns                - Show available columns")
        print("  export <filename>      - Export last results to CSV")
        print("  help                   - Show this help")
        print("  quit                   - Exit")
        print()

        last_result = self.df

        while True:
            try:
                command = input("query> ").strip()

                if not command:
                    continue

                if command.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break

                elif command.lower() == 'help':
                    print("\nCommands:")
                    print("  all                    - Show all records")
                    print("  search <term>          - Search across all columns")
                    print("  filter <col>=<val>     - Filter by column")
                    print("  columns                - Show available columns")
                    print("  export <filename>      - Export last results to CSV")
                    print("  quit                   - Exit\n")

                elif command.lower() == 'all':
                    last_result = self.show_all()
                    self.display(last_result, max_rows=50)

                elif command.lower() == 'columns':
                    print("\nAvailable columns:")
                    for col in self.df.columns:
                        print(f"  - {col}")
                    print()

                elif command.lower().startswith('search '):
                    term = command[7:].strip()
                    last_result = self.search(term)
                    self.display(last_result, max_rows=50)

                elif command.lower().startswith('filter '):
                    filter_str = command[7:].strip()
                    last_result = self.filter_by_column([filter_str])
                    self.display(last_result, max_rows=50)

                elif command.lower().startswith('export '):
                    filename = command[7:].strip()
                    self.export(last_result, filename)

                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Query nursery inventory from CSV or Excel files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s inventory.xls
  %(prog)s inventory.xls --interactive
  %(prog)s inventory.xls --search "Maple"
  %(prog)s inventory.xls --filter "OnHand>10"
  %(prog)s inventory.xls --filter "Category=Trees" --filter "OnHand>5"
        """
    )

    parser.add_argument('file', help='Path to the inventory file (CSV or Excel .xls/.xlsx)')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Start interactive query mode')
    parser.add_argument('-s', '--search', help='Search term across all columns')
    parser.add_argument('-f', '--filter', action='append', dest='filters',
                        help='Filter by column (format: column=value or column>value)')
    parser.add_argument('-o', '--output', help='Export results to CSV file')
    parser.add_argument('--max-rows', type=int, default=50,
                        help='Maximum rows to display (default: 50)')

    args = parser.parse_args()

    # Initialize query tool
    inventory = InventoryQuery(args.file)

    # Interactive mode
    if args.interactive:
        inventory.interactive_mode()
        return

    # Build query based on arguments
    result = inventory.df

    if args.search:
        result = inventory.search(args.search)

    if args.filters:
        result = inventory.filter_by_column(args.filters)

    # Display results
    inventory.display(result, max_rows=args.max_rows)

    # Export if requested
    if args.output:
        inventory.export(result, args.output)


if __name__ == '__main__':
    main()
