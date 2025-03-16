import dash
import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output

# Initialize the Dash app
app = dash.Dash(__name__)

# Create sample data with multiple categories
data = {
    "date": pd.date_range(start="2024-01-01", periods=12, freq="M"),
    "category": ["A"] * 4 + ["B"] * 4 + ["C"] * 4,
    "value": [10, 15, 13, 17, 20, 18, 22, 25, 30, 28, 32, 35],
}
df = pd.DataFrame(data)

# Define the app layout
app.layout = html.Div(
    [
        html.H1("Interactive Category Selector"),
        # Dropdown for category selection
        html.Div(
            [
                html.Label("Select Category:"),
                dcc.Dropdown(
                    id="category-dropdown",
                    options=[
                        {"label": "Category A", "value": "A"},
                        {"label": "Category B", "value": "B"},
                        {"label": "Category C", "value": "C"},
                    ],
                    value="A",  # Default value
                    style={"width": "50%", "margin": "20px 0"},
                ),
            ]
        ),
        # Graph
        dcc.Graph(id="category-graph"),
    ]
)


# Callback to update the graph based on dropdown selection
@app.callback(Output("category-graph", "figure"), Input("category-dropdown", "value"))
def update_graph(selected_category):
    # Filter data for selected category
    filtered_df = df[df["category"] == selected_category]

    # Create figure
    fig = px.line(
        filtered_df,
        x="date",
        y="value",
        title=f"Values for Category {selected_category}",
        labels={"value": "Value", "date": "Date"},
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
