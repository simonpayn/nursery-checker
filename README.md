# Nursery Inventory Query Tool

A simple, flexible tool for querying nursery inventory from CSV files. Includes both a user-friendly web interface and a command-line tool.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Web Interface (Recommended)

The easiest way to search your inventory is using the web interface:

```bash
streamlit run app.py
```

This will open a web browser with a user-friendly interface where you can:
- 🔍 Search by plant name (botanical or common)
- 🏷️ Filter by category
- 📊 Filter by stock levels (in stock, high stock, low stock)
- 📥 Download filtered results as CSV
- 📈 View summary statistics

Simply type a plant name in the search box and instantly see:
- Inventory quantities (OnHand)
- Available sizes (ProductSKU)
- Pricing (Price and VolumePrice)
- Categories and common names

## Command Line Tool

### Usage

#### Basic Query

Query your inventory CSV file:

```bash
python nursery_query.py inventory.csv
```

#### Interactive Mode

Start an interactive session to run multiple queries:

```bash
python nursery_query.py inventory.csv --interactive
```

#### Filter by Column

Search for specific values:

```bash
# Find all items with "Rose" in the name
python nursery_query.py inventory.csv --filter "name=Rose"

# Find items with quantity greater than 10
python nursery_query.py inventory.csv --filter "quantity>10"

# Multiple filters
python nursery_query.py inventory.csv --filter "category=Trees" --filter "quantity>5"
```

#### Search Across All Columns

```bash
python nursery_query.py inventory.csv --search "Maple"
```

## CSV File Format

Your CSV file should have a header row with column names. The tool is flexible and will work with any columns you define. Example:

```csv
name,category,quantity,price,location
Japanese Maple,Trees,15,45.99,Section A
Red Rose Bush,Shrubs,23,19.99,Section B
```

## Features

- Query any CSV file structure
- Filter by specific columns
- Search across all columns
- Interactive mode for multiple queries
- Display results in a formatted table
- Export filtered results to new CSV files

## Updating Your Inventory

Simply replace or update your CSV file. The tool automatically adapts to any column structure.
