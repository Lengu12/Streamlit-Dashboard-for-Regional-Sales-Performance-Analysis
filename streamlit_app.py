import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px


st.title("Regional Sales Performance Dashboard")
st.write("Decision support for a Regional Sales Manager to monitor revenue, profit, category performance, and top-selling products across regions.")

conn = psycopg2.connect(
    host="localhost",
    database="ecommerce_performance_database",
    user="postgres",
    password=""
)

query = """
SELECT
    s.order_id,
    d.order_date,
    g.region,
    p.payment_method,
    pr.product_category,
    pr.product_name,
    s.quantity,
    s.unit_price,
    s.total_sales,
    s.shipping_cost,
    s.profit
FROM sales_table s
JOIN geography_table g ON s.geography_id = g.geography_id
JOIN payment_table p ON s.payment_id = p.payment_id
JOIN product_table pr ON s.product_id = pr.product_id
JOIN date_table d ON s.date_id = d.date_id;
"""

df = pd.read_sql(query, conn)

#Region and year filter
df["order_date"] = pd.to_datetime(df["order_date"])
df["year"] = df["order_date"].dt.year
region_options = ["All Regions"] + list(df["region"].unique())
selected_region = st.sidebar.selectbox("Select Region", region_options)

year_options = ["All Years"] + sorted(df["year"].dropna().unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", year_options)

filtered_df = df.copy()

if selected_region != "All Regions":
    filtered_df = filtered_df[filtered_df["region"] == selected_region]

if selected_year != "All Years":
    filtered_df = filtered_df[filtered_df["year"] == selected_year]

#Performance Overview
st.subheader("Performance Overview (USD)")
total_sales = filtered_df["total_sales"].sum()
total_profit = filtered_df["profit"].sum()
total_orders = filtered_df["order_id"].count()
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div style = "
            border: 2px solid #4CAF50;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            background-color:white;
             min-height: 170px;
            ">
            <h3 style="color:#333333; margin-bottom: 20px; font-size: 22px; ">Total Sales</h3>
            <h1 style="color:#4CAF50; margin: 0; font-size: 36px; ">${total_sales:,.2f}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:
    st.markdown(
        f"""
        <div style = "
            border:2px solid #2196F3;
            border-radius: 15px;
            padding:20px;
            text-align: center;
            background-color: white;
            min-height: 170px
        ">
        <h3 style= "color:#333333; margin-bottom: 20px; font-size: 22px">Profit</h3>
        <h2 style=" color:#2196F3; margin: 0; font-size: 38px">${total_profit:,.2f}</h2>
              
        </div>
        """,
        unsafe_allow_html=True

    )

with col3:
    st.markdown(
        f"""
        <div style= "
              border: 2px solid #FF9800;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            background-color: white;
            min-height: 170px;
        ">
            <h3 style="color:#333333; margin-bottom: 20px;font-size: 22px; ">Total Orders</h3>
            <h1 style="color:#FF9800; margin: 0; font_size: 38px; ">{total_orders}</h1>
    </div>
    """,
    unsafe_allow_html= True
    )
# Category Performance grouped bar chart
st.subheader("Product Category Performance")
category_summary = filtered_df.groupby("product_category")[["total_sales", "profit"]].sum().reset_index()
fig_category = px.bar(
    category_summary,
    x= "product_category",
    y=["total_sales", "profit"],
    barmode= "group",
    title="Sales vs Profit by Product Category",
    labels={
        "product_category": "Product Category",
        "value": "Amount",
        "Variable": "Metric"
    }
)

fig_category.update_traces(
    texttemplate="$%{y:,.0f}",
    textposition="outside"
)

fig_category.update_layout(
    xaxis_title="Product Category",
    yaxis_title="Amount",
    legend_title="Metric"
)

st.plotly_chart(fig_category, use_container_width=True)


# Sales Trend
st.subheader("Sales Trend")

sales_over_time = filtered_df.groupby("order_date")["total_sales"].sum()
st.line_chart(sales_over_time)

# Top Products
st.subheader("Sales Over Time by Category (Stacked)")
filtered_df["order_month"] = pd.to_datetime(filtered_df["order_date"]).dt.strftime("%Y-%m")
monthly_category_sales = filtered_df.groupby(["order_month", "product_category"])["total_sales"].sum().reset_index()

fig_stacked = px.bar(
    monthly_category_sales,
    x="order_month",
    y="total_sales",
    color="product_category",
    title="Sales Over Time by Category (Stacked)",
    labels={
        "order_month": "Month",
        "total_sales": "Total Sales",
        "product_category": "Product Category"
    }
)

fig_stacked.update_layout(barmode="stack")

st.plotly_chart(fig_stacked, use_container_width=True)

# Sales Distribution by Region
st.subheader("Sales Distribution by Region")

region_sales = filtered_df.groupby("region")["total_sales"].sum().reset_index()

fig_region = px.pie(
    region_sales,
    names="region",
    values="total_sales",
    title="Sales Share by Region"
)

fig_region.update_traces(
    textinfo="percent",
    textfont_size=14
)

st.plotly_chart(fig_region, use_container_width=True)

# Top Products
st.subheader("Top Products")

top_products = (
    filtered_df.groupby("product_name")["total_sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig_top = px.bar(
    top_products,
    x="total_sales",
    y="product_name",
    orientation="h",
    title="Top 10 Products by Sales",
    text="total_sales"
)

fig_top.update_layout(
    yaxis=dict(autorange="reversed")  # highest at the top
)

fig_top.update_traces(
    texttemplate='$%{text:,.0f}',
    textposition="outside"
)

st.plotly_chart(fig_top, use_container_width=True)

# Key Insights
top_category = category_summary.loc[category_summary["total_sales"].idxmax(), "product_category"]
top_product = top_products.loc[top_products["total_sales"].idxmax(), "product_name"]
region_summary = filtered_df.groupby("region")["total_sales"].sum().reset_index()

top_region = region_summary.loc[
    region_summary["total_sales"].idxmax(), "region"
]

top_region_sales = region_summary.loc[
    region_summary["total_sales"].idxmax(), "total_sales"
]
st.subheader("Key Insights")
st.write(f"📌 The top performing product category is **{top_category}**.")
st.write(f"🏆 The best selling product is **{top_product}**.")
st.write(f"🌍 The region with the highest sales is **{top_region}** (${top_region_sales:,.0f}).")
st.write("💡 Recommendation: Focus marketing and inventory efforts on these high-performing areas.")

# Detailed Records
st.subheader("Detailed Records")
st.write("Filtered Sales Data")
st.dataframe(filtered_df)

st.write("Full Sales Data Preview")
st.dataframe(df)
