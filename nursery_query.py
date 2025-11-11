#!/usr/bin/env python3
"""
Nursery Inventory Query Tool
A flexible CSV query tool for nursery inventory management.
"""

import argparse
import sys
import pandas as pd
from tabulate import tabulate


class InventoryQuery:
    def __init__(self, csv_path):
        """Initialize with a CSV file path."""
        try:
            self.df = pd.read_csv(csv_path)
            self.csv_path = csv_path
            print(f"Loaded {len(self.df)} records from {csv_path}")
            print(f"Columns: {', '.join(self.df.columns)}\n")
        except FileNotFoundError:
            print(f"Error: File '{csv_path}' not found.")
            sys.exit(1)
        except pd.errors.EmptyDataError:
            print(f"Error: File '{csv_path}' is empty.")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading CSV: {e}")
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
        description='Query nursery inventory from CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s inventory.csv
  %(prog)s inventory.csv --interactive
  %(prog)s inventory.csv --search "Maple"
  %(prog)s inventory.csv --filter "quantity>10"
  %(prog)s inventory.csv --filter "category=Trees" --filter "quantity>5"
        """
    )

    parser.add_argument('csv_file', help='Path to the CSV inventory file')
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
    inventory = InventoryQuery(args.csv_file)

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
