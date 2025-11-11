# Nursery Inventory Query Tool

A simple, flexible tool for querying nursery inventory from CSV files. Includes both a user-friendly web interface and a command-line tool.

## 🌐 Access the App Online

**The easiest way to use this tool is via the web!** No installation needed - just visit the URL and upload your CSV file.

### Deploy Your Own (Free!)

You can deploy your own version of this app for free on Streamlit Community Cloud:

1. **Fork or push this repository to GitHub**

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Sign in with GitHub**

4. **Click "New app"** and select:
   - Repository: `your-username/nursery-checker`
   - Branch: `main` (or your branch name)
   - Main file path: `app.py`

5. **Click "Deploy"** - Your app will be live at a public URL in minutes!

6. **Share the URL** with anyone who needs to search your inventory

## 💻 Run Locally

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Web Interface (Recommended)

Run the web interface locally:

```bash
streamlit run app.py
```

This will open a web browser with a user-friendly interface where you can:
- 📂 Upload any CSV inventory file
- 🔍 Search across all columns
- 🏷️ Filter by category (auto-detected)
- 📊 Filter by stock levels (auto-detected)
- 📈 View summary statistics with visual indicators
- 📥 Download filtered results as CSV
- 🎨 Enjoy color-coded stock status indicators

The app automatically adapts to your CSV structure - no configuration needed!

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
