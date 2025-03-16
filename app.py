import numpy as np
import plotly.express as px
from fasthtml.common import Div, NotStr, Script, Titled, fast_app, serve

from evals.util.db import read_all
from evals.util.env import ENV

app, rt = fast_app(
    live=ENV.DEV,
    debug=ENV.DEV,
    hdrs=(Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js"),),
)


@rt("/")
def get():
    fig = px.line(x=range(12), y=range(12))

    results = read_all()

    plots = []
    for eval_name, df in results.groupby("eval_name"):
        colour = None

        if "tictactoe" in eval_name:
            print("eval_name", eval_name)
            # red if <0, green if >0
            df["colour"] = np.where(df["result"] < 0, "red", "green")
            colour = "colour"
        fig = px.bar(
            df,
            x="result",
            y="model_name",
            color=colour,
            color_discrete_map={"red": "red", "green": "green"},
        )

        fig.update_layout(
            title=eval_name,
            xaxis_title="Score",
            yaxis_title=None,
            # remove legend
            showlegend=False,
        )

        if "tictactoe" in eval_name:
            # Change xlims
            fig.update_xaxes(range=[-1, 1])

        plots.append(NotStr(fig.to_html(full_html=False, include_plotlyjs=False)))

    return Titled(
        "LLM Evals",
        Div(id="myDiv"),
        *plots,
    )


serve()
