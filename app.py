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
def load_inventory(csv_path):
    """Load inventory with automatic encoding detection."""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue

    return None

def main():
    st.title("🌿 Nursery Inventory Search")
    st.markdown("---")

    # Load inventory
    csv_file = "NVK_October_28.csv"

    try:
        df = load_inventory(csv_file)

        if df is None:
            st.error("Could not load inventory file. Please check the file encoding.")
            return

        # Sidebar filters
        st.sidebar.header("Filters")

        # Category filter
        categories = ['All'] + sorted(df['Category'].dropna().unique().tolist())
        selected_category = st.sidebar.selectbox("Category", categories)

        # Stock filter
        stock_filter = st.sidebar.radio(
            "Stock Status",
            ["All Items", "In Stock (OnHand > 0)", "High Stock (OnHand > 50)", "Low Stock (OnHand < 10)"]
        )

        # Main search
        st.subheader("Search Inventory")
        search_term = st.text_input(
            "Search by plant name (botanical or common name)",
            placeholder="e.g., Maple, Abies, Rose..."
        )

        # Filter dataframe
        filtered_df = df.copy()

        # Apply category filter
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['Category'] == selected_category]

        # Apply stock filter
        if stock_filter == "In Stock (OnHand > 0)":
            filtered_df = filtered_df[filtered_df['OnHand'] > 0]
        elif stock_filter == "High Stock (OnHand > 50)":
            filtered_df = filtered_df[filtered_df['OnHand'] > 50]
        elif stock_filter == "Low Stock (OnHand < 10)":
            filtered_df = filtered_df[(filtered_df['OnHand'] > 0) & (filtered_df['OnHand'] < 10)]

        # Apply search term
        if search_term:
            mask = filtered_df.astype(str).apply(
                lambda row: row.str.contains(search_term, case=False, na=False).any(),
                axis=1
            )
            filtered_df = filtered_df[mask]

        # Display results
        st.markdown("---")

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Records", len(df))

        with col2:
            st.metric("Filtered Results", len(filtered_df))

        with col3:
            in_stock = len(filtered_df[filtered_df['OnHand'] > 0])
            st.metric("In Stock", in_stock)

        with col4:
            total_quantity = filtered_df['OnHand'].sum()
            st.metric("Total Quantity", f"{int(total_quantity):,}")

        st.markdown("---")

        # Display results table
        if len(filtered_df) > 0:
            st.subheader(f"Results ({len(filtered_df)} items)")

            # Format the display dataframe
            display_df = filtered_df[[
                'Botanical name',
                'CommonNames',
                'ProductSKU',
                'Category',
                'OnHand',
                ' Price ',
                'VolumeQuantity',
                ' VolumePrice '
            ]].copy()

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
                file_name=f"nursery_inventory_filtered_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        else:
            st.info("No items found. Try adjusting your search or filters.")

        # Quick stats in sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader("Quick Stats")
        st.sidebar.write(f"Total Items: {len(df):,}")
        st.sidebar.write(f"Categories: {df['Category'].nunique()}")
        st.sidebar.write(f"In Stock Items: {len(df[df['OnHand'] > 0]):,}")

    except FileNotFoundError:
        st.error(f"❌ File '{csv_file}' not found. Please make sure the inventory file is in the same directory as this app.")
    except Exception as e:
        st.error(f"❌ Error loading inventory: {e}")

if __name__ == "__main__":
    main()
