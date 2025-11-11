#!/usr/bin/env python3
"""
Nursery Inventory Web App
A user-friendly web interface for searching and viewing nursery inventory.
"""

import streamlit as st
import pandas as pd
import sys
import os

# Page configuration
st.set_page_config(
    page_title="Nursery Inventory Search",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better visual design
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stAlert {
        border-radius: 10px;
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stock-high {
        color: #28a745;
        font-weight: bold;
    }
    .stock-low {
        color: #ffc107;
        font-weight: bold;
    }
    .stock-out {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_inventory_from_path(csv_path):
    """Load inventory with automatic encoding detection."""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            return df, None
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            return None, str(e)

    return None, "Could not read file with any common encoding"

@st.cache_data
def load_inventory_from_upload(uploaded_file):
    """Load inventory from uploaded file with automatic encoding detection."""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding)
            return df, None
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            return None, str(e)

    return None, "Could not read file with any common encoding"

def get_stock_status_color(quantity):
    """Return color based on stock level."""
    if quantity == 0:
        return "🔴"  # Red circle for out of stock
    elif quantity < 10:
        return "🟡"  # Yellow circle for low stock
    elif quantity < 50:
        return "🟢"  # Green circle for in stock
    else:
        return "🟢"  # Green circle for high stock

def main():
    st.title("🌿 Nursery Inventory Search")

    # Welcome message
    st.markdown("""
    ### Welcome! 👋
    This tool helps you search and filter your nursery inventory. Simply upload your CSV file to get started!
    """)

    st.markdown("---")

    # File upload section
    st.subheader("📂 Step 1: Upload Your Inventory File")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose your inventory CSV file",
            type=['csv'],
            help="Upload your nursery inventory CSV file. The app will automatically detect the file encoding."
        )

    with col2:
        st.info("💡 **Tip:** Your CSV file should contain columns like plant names, quantities, prices, etc.")

    # Try to load default file if it exists and no file uploaded
    df = None
    default_file = "NVK_October_28.csv"

    if uploaded_file is not None:
        df, error = load_inventory_from_upload(uploaded_file)
        if error:
            st.error(f"❌ Could not read your file: {error}")
            st.info("💡 Make sure your file is a valid CSV file with a header row.")
            return
        st.success("✅ File loaded successfully!")
    elif os.path.exists(default_file):
        df, error = load_inventory_from_path(default_file)
        if error:
            st.warning(f"⚠️ Could not load default inventory file. Please upload your own CSV file.")
            return
        st.info(f"📋 Using default inventory file: {default_file}")
    else:
        st.info("👆 Please upload your inventory CSV file to begin.")
        return

    # Display column info to help users understand their data
    with st.expander("📊 View Column Information"):
        st.write("**Your file contains the following columns:**")
        cols_info = pd.DataFrame({
            'Column Name': df.columns,
            'Sample Value': [df[col].iloc[0] if len(df) > 0 else 'N/A' for col in df.columns],
            'Non-Empty Count': [df[col].notna().sum() for col in df.columns]
        })
        st.dataframe(cols_info, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Detect column names (flexible for different CSV structures)
    # Try to find common column patterns
    quantity_col = None
    category_col = None
    name_cols = []
    price_cols = []

    for col in df.columns:
        col_lower = col.lower()
        if 'onhand' in col_lower or 'quantity' in col_lower or 'stock' in col_lower:
            quantity_col = col
        elif 'category' in col_lower or 'type' in col_lower:
            category_col = col
        elif 'name' in col_lower or 'botanical' in col_lower:
            name_cols.append(col)
        elif 'price' in col_lower:
            price_cols.append(col)

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Category filter (if category column exists)
    selected_category = None
    if category_col:
        categories = ['All'] + sorted(df[category_col].dropna().unique().tolist())
        selected_category = st.sidebar.selectbox(
            f"Filter by {category_col}",
            categories,
            help=f"Filter items by their {category_col}"
        )

    # Stock filter (if quantity column exists)
    stock_filter = None
    if quantity_col:
        stock_filter = st.sidebar.radio(
            "Stock Status",
            ["All Items", "In Stock (>0)", "High Stock (>50)", "Low Stock (<10)"],
            help="Filter items by their stock levels"
        )

    # Main search
    st.subheader("🔎 Step 2: Search Your Inventory")
    search_term = st.text_input(
        "Search for anything in your inventory",
        placeholder="e.g., Maple, Rose, Trees, specific SKU...",
        help="Type any keyword to search across all columns in your inventory"
    )

    # Filter dataframe
    filtered_df = df.copy()

    # Apply category filter
    if selected_category and selected_category != 'All' and category_col:
        filtered_df = filtered_df[filtered_df[category_col] == selected_category]

    # Apply stock filter
    if stock_filter and quantity_col:
        if stock_filter == "In Stock (>0)":
            filtered_df = filtered_df[filtered_df[quantity_col] > 0]
        elif stock_filter == "High Stock (>50)":
            filtered_df = filtered_df[filtered_df[quantity_col] > 50]
        elif stock_filter == "Low Stock (<10)":
            filtered_df = filtered_df[(filtered_df[quantity_col] > 0) & (filtered_df[quantity_col] < 10)]

    # Apply search term
    if search_term:
        mask = filtered_df.astype(str).apply(
            lambda row: row.str.contains(search_term, case=False, na=False).any(),
            axis=1
        )
        filtered_df = filtered_df[mask]

    # Display results
    st.markdown("---")
    st.subheader("📊 Step 3: View Your Results")

    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📋 Total Records", f"{len(df):,}")

    with col2:
        st.metric("🎯 Filtered Results", f"{len(filtered_df):,}")

    with col3:
        if quantity_col:
            in_stock = len(filtered_df[filtered_df[quantity_col] > 0])
            st.metric("✅ In Stock", f"{in_stock:,}")
        else:
            st.metric("Columns", len(df.columns))

    with col4:
        if quantity_col:
            total_quantity = filtered_df[quantity_col].sum()
            st.metric("📦 Total Quantity", f"{int(total_quantity):,}")
        else:
            st.metric("Rows", len(filtered_df))

    st.markdown("---")

    # Display results table
    if len(filtered_df) > 0:
        # Add stock status indicators if quantity column exists
        if quantity_col:
            display_df = filtered_df.copy()
            display_df.insert(0, 'Status', display_df[quantity_col].apply(get_stock_status_color))
        else:
            display_df = filtered_df.copy()

        # Sort options
        col_sort, col_order = st.columns([3, 1])
        with col_sort:
            sort_by = st.selectbox("Sort by", ['None'] + list(df.columns), help="Choose a column to sort by")
        with col_order:
            sort_order = st.radio("Order", ["↓ Descending", "↑ Ascending"], horizontal=True)

        if sort_by != 'None':
            ascending = sort_order == "↑ Ascending"
            display_df = display_df.sort_values(by=sort_by, ascending=ascending)

        st.write(f"**Showing {len(display_df):,} items:**")

        # Style the dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )

        # Download button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"filtered_inventory_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Download your filtered results as a CSV file"
        )

    else:
        st.info("🔍 No items found. Try adjusting your search or filters.")

    # Quick stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 Quick Stats")
    st.sidebar.write(f"**Total Items:** {len(df):,}")
    if category_col:
        st.sidebar.write(f"**Categories:** {df[category_col].nunique()}")
    if quantity_col:
        st.sidebar.write(f"**In Stock Items:** {len(df[df[quantity_col] > 0]):,}")
        st.sidebar.write(f"**Out of Stock:** {len(df[df[quantity_col] == 0]):,}")

    # Help section in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("❓ Need Help?")
    st.sidebar.markdown("""
    **How to use this app:**
    1. Upload your CSV file
    2. Use filters to narrow down items
    3. Search for specific items
    4. Download filtered results

    **Tips:**
    - Search works across all columns
    - Use filters for quick sorting
    - Download button saves your filtered results
    """)

if __name__ == "__main__":
    main()
