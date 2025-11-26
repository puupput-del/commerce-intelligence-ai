# utils.py
import pandas as pd
import numpy as np
import plotly.express as px

def safe_to_numeric(s):
    return pd.to_numeric(s, errors='coerce')

def infer_and_prepare_df(df):
    df = df.copy()
    # basic normalization
    df.columns = [c.strip() for c in df.columns]
    lower_map = {c.lower(): c for c in df.columns}

    # find likely columns
    date_col = next((lower_map[c] for c in ['date','order_date','orderdate'] if c in lower_map), df.columns[0])
    product_col = next((lower_map[c] for c in ['product','product_name','item','nama_produk'] if c in lower_map), df.columns[1] if len(df.columns)>1 else df.columns[0])
    category_col = next((lower_map[c] for c in ['category','kategori','brand'] if c in lower_map), product_col)
    price_col = next((lower_map[c] for c in ['price','harga','unit_price'] if c in lower_map), None)
    qty_col = next((lower_map[c] for c in ['qty','quantity','kuantitas'] if c in lower_map), None)
    totals_col = next((lower_map[c] for c in ['totalsales','total_sales','grand_total','grand total','harga_total'] if c in lower_map), None)

    # conversions
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    except Exception:
        df[date_col] = pd.NaT

    if totals_col and totals_col in df.columns:
        df[totals_col] = safe_to_numeric(df[totals_col]).fillna(0)
    else:
        # compute totals if possible
        if price_col and qty_col and price_col in df.columns and qty_col in df.columns:
            df['TotalSales'] = safe_to_numeric(df[price_col]).fillna(0) * safe_to_numeric(df[qty_col]).fillna(0)
            totals_col = 'TotalSales'
        else:
            # fallback: sum of numeric columns
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if numeric_cols:
                df['TotalSales'] = df[numeric_cols].iloc[:,0].fillna(0)
                totals_col = 'TotalSales'
            else:
                df['TotalSales'] = 0
                totals_col = 'TotalSales'

    if qty_col is None or qty_col not in df.columns:
        df['Qty'] = 1
        qty_col = 'Qty'

    return df, {
        'date_col': date_col,
        'product_col': product_col,
        'category_col': category_col,
        'price_col': price_col,
        'qty_col': qty_col,
        'totals_col': totals_col
    }

def aggregate_sales(df, category_col, totals_col):
    grouped = df.groupby(category_col, dropna=False)[totals_col].sum().reset_index().sort_values(by=totals_col, ascending=False)
    return grouped

def compute_key_metrics(df, totals_col, qty_col, date_col=None):
    out = {}
    out['total_sales'] = float(df[totals_col].sum())
    out['num_transactions'] = int(len(df))
    out['avg_transaction_value'] = float(df[totals_col].mean()) if len(df) else 0
    out['avg_basket_size'] = float(df[qty_col].mean()) if qty_col in df.columns else 0
    # minimal monthly growth
    if date_col and date_col in df.columns and df[date_col].notna().any():
        df2 = df.copy()
        df2[date_col] = pd.to_datetime(df2[date_col], errors='coerce')
        df2['period'] = df2[date_col].dt.to_period('M').dt.to_timestamp()
        monthly = df2.groupby('period')[totals_col].sum().sort_index()
        if len(monthly) >= 2:
            last = monthly.iloc[-1]; prev = monthly.iloc[-2]
            out['mom_growth_pct'] = float((last-prev)/prev*100) if prev != 0 else None
            out['monthly_series'] = monthly.reset_index().to_dict(orient='records')
        else:
            out['mom_growth_pct'] = None
            out['monthly_series'] = []
    else:
        out['mom_growth_pct'] = None
        out['monthly_series'] = []
    return out

def prepare_groq_context_for_summary(kpis, top_products, top_categories, n=10):
    ctx = {
        'total_sales': kpis.get('total_sales'),
        'num_transactions': kpis.get('num_transactions'),
        'avg_transaction_value': kpis.get('avg_transaction_value'),
        'avg_basket_size': kpis.get('avg_basket_size'),
        'mom_growth_pct': kpis.get('mom_growth_pct'),
        'top_products': top_products.head(n).to_dict(orient='records') if hasattr(top_products, 'to_dict') else [],
        'top_categories': top_categories.head(n).to_dict(orient='records') if hasattr(top_categories, 'to_dict') else []
    }
    return ctx

# Plot helpers
def plot_top_products(top_df, product_col, totals_col):
    fig = px.bar(top_df, x=product_col, y=totals_col, labels={product_col:'Product', totals_col:'Sales'}, title='Top Products by Sales')
    return fig

def plot_sales_trend(df, date_col, totals_col, freq='M'):
    df = df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['period'] = df[date_col].dt.to_period(freq).dt.to_timestamp()
        trend = df.groupby('period')[totals_col].sum().reset_index()
        fig = px.line(trend, x='period', y=totals_col, title='Sales Trend')
        return fig
    else:
        return px.line(title='Sales Trend (no date)')

def plot_category_pie(cat_df, category_col, totals_col):
    fig = px.pie(cat_df, names=category_col, values=totals_col, title='Sales by Category')
    fig.update_traces(hole=0.4)
    return fig\n