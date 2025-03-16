import plotly.express as px
from fasthtml.common import Div, NotStr, Script, Titled, fast_app, serve

from evals.util.db import read_all

app, rt = fast_app(
    live=True, hdrs=(Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js"),)
)


@rt("/")
def get():
    fig = px.line(x=range(12), y=range(12))

    results = read_all()

    plots = []
    for eval_name, df in results.groupby("eval_name"):
        fig = px.bar(df, x="result", y="model_name")

        fig.update_layout(
            title=eval_name,
            xaxis_title="Score",
            yaxis_title="Model",
        )

        plots.append(NotStr(fig.to_html(full_html=False, include_plotlyjs=False)))

    return Titled(
        "Chart Demo",
        Div(id="myDiv"),
        *plots,
    )


serve()
