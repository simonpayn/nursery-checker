#!/usr/bin/env python3
"""
Nursery Inventory Web App
A user-friendly web interface for searching and viewing nursery inventory.
"""

import glob
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Nursery Inventory Search",
    page_icon="🌿",
    layout="wide"
)

def parse_nvk_xls(raw):
    """Parse NVK availability XLS into a normalized DataFrame.

    The format uses category header rows (col0 NaN, col1 = category name)
    interspersed with plant data rows.
    """
    current_category = "Evergreens"
    rows = []

    for _, row in raw.iterrows():
        col0 = row.iloc[0]
        col1 = row.iloc[1]

        # Category header: col0 is NaN, col1 has the category name
        if pd.isna(col0) and pd.notna(col1):
            current_category = str(col1).strip()
            continue

        # Skip the column header row
        if str(col0).strip().lower() == "botanical":
            continue

        # Skip empty rows
        if pd.isna(col0):
            continue

        rows.append({
            "Botanical name": str(col0).strip(),
            "CommonNames": str(col1).strip() if pd.notna(col1) else "",
            "ProductSKU": str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "",
            "Category": current_category,
            "OnHand": pd.to_numeric(row.iloc[3], errors="coerce"),
            "Price": row.iloc[4] if pd.notna(row.iloc[4]) else "",
            "VolumePrice": row.iloc[5] if pd.notna(row.iloc[5]) else "",
        })

    df = pd.DataFrame(rows)
    df["OnHand"] = df["OnHand"].fillna(0).astype(int)
    return df


@st.cache_data
def load_inventory(file_path):
    """Load inventory from CSV or XLS/XLSX."""
    if file_path.endswith(".xls"):
        raw = pd.read_excel(file_path, engine="xlrd", header=None)
        return parse_nvk_xls(raw)
    elif file_path.endswith((".xlsx", ".xlsm")):
        raw = pd.read_excel(file_path, engine="openpyxl", header=None)
        return parse_nvk_xls(raw)

    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def find_inventory_file():
    for pattern in ["*.xls", "*.xlsx", "*.csv"]:
        files = [f for f in glob.glob(pattern) if "sample" not in f.lower()]
        if files:
            return files[0]
    return None


def init_cart():
    if "cart" not in st.session_state:
        st.session_state.cart = {}


def add_to_cart(edited_df):
    rows = edited_df[edited_df["Order Qty"] > 0]
    for _, row in rows.iterrows():
        sku = str(row["ProductSKU"])
        qty = int(row["Order Qty"])
        if sku in st.session_state.cart:
            st.session_state.cart[sku]["qty"] += qty
        else:
            st.session_state.cart[sku] = {
                "name": row["Botanical name"],
                "sku": sku,
                "qty": qty,
            }
    return len(rows)


def render_sidebar_cart():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛒 Order Cart")

    if not st.session_state.cart:
        st.sidebar.caption("Cart is empty")
        return

    total_units = sum(item["qty"] for item in st.session_state.cart.values())
    st.sidebar.write(f"**{len(st.session_state.cart)} plants · {total_units} units**")
    st.sidebar.markdown("---")

    for sku, item in list(st.session_state.cart.items()):
        cols = st.sidebar.columns([4, 1])
        with cols[0]:
            st.write(f"**{item['name']}**")
            st.caption(f"{sku} · qty: {item['qty']}")
        with cols[1]:
            if st.button("✕", key=f"remove_{sku}", help="Remove from cart"):
                del st.session_state.cart[sku]
                st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Cart", type="secondary"):
        st.session_state.cart = {}
        st.rerun()


def main():
    init_cart()

    st.title("🌿 Nursery Inventory Search")
    st.markdown("---")

    inventory_file = find_inventory_file()
    if not inventory_file:
        st.error("❌ No inventory file found. Add a CSV or XLS file to the app directory.")
        return

    try:
        df = load_inventory(inventory_file)
        if df is None:
            st.error("Could not load inventory file.")
            return

        # --- Sidebar filters ---
        st.sidebar.header("Filters")
        categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
        selected_category = st.sidebar.selectbox("Category", categories)

        stock_filter = st.sidebar.radio(
            "Stock Status",
            ["All Items", "In Stock (OnHand > 0)", "High Stock (OnHand > 50)", "Low Stock (OnHand < 10)"]
        )

        st.sidebar.markdown("---")
        st.sidebar.subheader("Quick Stats")
        st.sidebar.write(f"Total Items: {len(df):,}")
        st.sidebar.write(f"Categories: {df['Category'].nunique()}")
        st.sidebar.write(f"In Stock Items: {len(df[df['OnHand'] > 0]):,}")

        render_sidebar_cart()

        # --- Search ---
        st.subheader("Search Inventory")
        search_term = st.text_input(
            "Search by plant name (botanical or common name)",
            placeholder="e.g., Spruce, Thuja, Cedar..."
        )

        # --- Filtering ---
        filtered_df = df.copy()

        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["Category"] == selected_category]

        if stock_filter == "In Stock (OnHand > 0)":
            filtered_df = filtered_df[filtered_df["OnHand"] > 0]
        elif stock_filter == "High Stock (OnHand > 50)":
            filtered_df = filtered_df[filtered_df["OnHand"] > 50]
        elif stock_filter == "Low Stock (OnHand < 10)":
            filtered_df = filtered_df[(filtered_df["OnHand"] > 0) & (filtered_df["OnHand"] < 10)]

        if search_term:
            mask = filtered_df[["Botanical name", "CommonNames"]].astype(str).apply(
                lambda col: col.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[mask]

        st.markdown("---")

        # --- Summary stats ---
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Records", len(df))
        with c2:
            st.metric("Filtered Results", len(filtered_df))
        with c3:
            st.metric("In Stock", len(filtered_df[filtered_df["OnHand"] > 0]))
        with c4:
            st.metric("Total Quantity", f"{int(filtered_df['OnHand'].sum()):,}")

        st.markdown("---")

        # --- Results table with Order Qty ---
        if len(filtered_df) > 0:
            st.subheader(f"Results ({len(filtered_df)} items)")
            st.caption("Enter quantities in the **Order Qty** column, then click **Add to Cart**.")

            display_df = filtered_df[
                ["Botanical name", "CommonNames", "ProductSKU", "Category", "OnHand", "Price", "VolumePrice"]
            ].copy()
            display_df.insert(0, "Order Qty", 0)

            column_config = {
                "Order Qty": st.column_config.NumberColumn(
                    "Order Qty", min_value=0, step=1, default=0,
                    help="Enter quantity to order"
                ),
                "Botanical name": st.column_config.TextColumn(disabled=True),
                "CommonNames": st.column_config.TextColumn("Common Name", disabled=True),
                "ProductSKU": st.column_config.TextColumn("SKU", disabled=True),
                "Category": st.column_config.TextColumn(disabled=True),
                "OnHand": st.column_config.NumberColumn("On Hand", disabled=True),
                "Price": st.column_config.NumberColumn(disabled=True, format="$%.0f"),
                "VolumePrice": st.column_config.NumberColumn("Volume Price (25+)", disabled=True, format="$%.0f"),
            }

            editor_key = f"editor_{search_term}_{selected_category}_{stock_filter}"
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config=column_config,
                key=editor_key,
            )

            if st.button("🛒 Add to Cart", type="primary"):
                added = add_to_cart(edited_df)
                if added > 0:
                    st.success(f"Added {added} item(s) to cart.")
                    st.rerun()
                else:
                    st.warning("No quantities entered — set Order Qty > 0 to add items.")
        else:
            st.info("No items found. Try adjusting your search or filters.")

        # --- Checkout ---
        if st.session_state.cart:
            st.markdown("---")
            st.subheader("📋 Checkout")

            project_name = st.text_input(
                "Project Name",
                placeholder="e.g., Smith Residence - Front Garden"
            )

            order_rows = [
                {
                    "Botanical name": item["name"],
                    "ProductSKU": item["sku"],
                    "Order Qty": item["qty"],
                }
                for item in st.session_state.cart.values()
            ]
            order_df = pd.DataFrame(order_rows)
            st.dataframe(order_df, use_container_width=True, hide_index=True)

            if project_name:
                csv = order_df.to_csv(index=False).encode("utf-8")
                filename = f"{project_name.replace(' ', '_')}_order_{pd.Timestamp.now().strftime('%Y%m%d')}.csv"
                st.download_button(
                    label="📥 Download Order CSV",
                    data=csv,
                    file_name=filename,
                    mime="text/csv",
                    type="primary",
                )
            else:
                st.info("Enter a project name to download your order.")

    except FileNotFoundError:
        st.error("❌ Inventory file not found.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
