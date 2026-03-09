#!/usr/bin/env python3
"""
Nursery Inventory Web App
A user-friendly web interface for searching and viewing nursery inventory.
"""

import streamlit as st
import pandas as pd
import sys

# Page configuration
st.set_page_config(
    page_title="Nursery Inventory Search",
    page_icon="🌿",
    layout="wide"
)

@st.cache_data
def load_inventory(file_path):
    """Load inventory from an Excel file with multiple sheets.

    Each sheet represents a category. Row 0 of each sheet contains
    the column headers (Botanical, Common name, Size, Quantity, Price,
    25 plus price, Order). The sheet name becomes the Category column.
    """
    try:
        xls = pd.ExcelFile(file_path)
    except Exception as e:
        st.error(f"Could not open file: {e}")
        return None

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

    df = pd.concat(frames, ignore_index=True)
    return df

DISPLAY_COLUMNS = [
    'Botanical name',
    'CommonNames',
    'ProductSKU',
    'Category',
    'OnHand',
    'Price',
    'VolumePrice',
]


def show_results_table(filtered_df, key_suffix=""):
    """Display a results table with summary metrics and a download button."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Items", len(filtered_df))
    with col2:
        in_stock = len(filtered_df[filtered_df['OnHand'] > 0])
        st.metric("In Stock", in_stock)
    with col3:
        out_of_stock = len(filtered_df[filtered_df['OnHand'] <= 0])
        st.metric("Out of Stock", out_of_stock)
    with col4:
        total_quantity = filtered_df['OnHand'].sum()
        st.metric("Total Quantity", f"{int(total_quantity):,}")

    st.markdown("---")

    if len(filtered_df) > 0:
        display_df = filtered_df[DISPLAY_COLUMNS].copy()
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )

        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"nursery_inventory_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key=f"download_{key_suffix}",
        )
    else:
        st.info("No items found.")


def main():
    st.title("🌿 Nursery Inventory")
    st.markdown("---")

    # Load inventory
    inventory_file = "NVK+availability.xls"

    try:
        df = load_inventory(inventory_file)

        if df is None:
            st.error("Could not load inventory file. Please check the file format.")
            return

        categories = sorted(df['Category'].dropna().unique().tolist())

        # Quick stats in sidebar
        st.sidebar.subheader("Quick Stats")
        st.sidebar.write(f"Total Items: {len(df):,}")
        st.sidebar.write(f"Categories: {len(categories)}")
        st.sidebar.write(f"In Stock Items: {len(df[df['OnHand'] > 0]):,}")

        # --- Tabs ---
        tab_search, tab_browse = st.tabs(["Search", "Browse by Category"])

        # ---- Search tab ----
        with tab_search:
            st.subheader("Search Inventory")

            search_col1, search_col2, search_col3 = st.columns([3, 1, 1])

            with search_col1:
                search_term = st.text_input(
                    "Search by plant name (botanical or common name)",
                    placeholder="e.g., Maple, Abies, Rose..."
                )

            with search_col2:
                cat_options = ['All Categories'] + categories
                selected_category = st.selectbox("Category", cat_options)

            with search_col3:
                stock_filter = st.selectbox(
                    "Stock Status",
                    ["All Items", "In Stock", "High Stock (>50)", "Low Stock (<10)"]
                )

            filtered_df = df.copy()

            if selected_category != 'All Categories':
                filtered_df = filtered_df[filtered_df['Category'] == selected_category]

            if stock_filter == "In Stock":
                filtered_df = filtered_df[filtered_df['OnHand'] > 0]
            elif stock_filter == "High Stock (>50)":
                filtered_df = filtered_df[filtered_df['OnHand'] > 50]
            elif stock_filter == "Low Stock (<10)":
                filtered_df = filtered_df[(filtered_df['OnHand'] > 0) & (filtered_df['OnHand'] < 10)]

            if search_term:
                mask = filtered_df.astype(str).apply(
                    lambda row: row.str.contains(search_term, case=False, na=False).any(),
                    axis=1
                )
                filtered_df = filtered_df[mask]

            st.markdown("---")
            show_results_table(filtered_df, key_suffix="search")

        # ---- Browse tab ----
        with tab_browse:
            st.subheader("Browse by Category")

            # Show category cards with item counts
            counts = df.groupby('Category').agg(
                Items=('OnHand', 'size'),
                InStock=('OnHand', lambda x: (x > 0).sum()),
            ).reindex(categories)

            selected = st.radio(
                "Select a category",
                categories,
                horizontal=True,
            )

            cat_df = df[df['Category'] == selected]

            st.markdown(f"**{selected}** — {len(cat_df)} items, "
                        f"{len(cat_df[cat_df['OnHand'] > 0])} in stock")
            st.markdown("---")

            show_results_table(cat_df, key_suffix="browse")

    except FileNotFoundError:
        st.error(f"❌ File '{inventory_file}' not found. Please make sure the inventory file is in the same directory as this app.")
    except Exception as e:
        st.error(f"❌ Error loading inventory: {e}")

if __name__ == "__main__":
    main()
