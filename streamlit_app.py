import altair as alt
import pandas as pd
import streamlit as st

from evals.util.db import EvalResult

# Pull in the data
results = pd.DataFrame([r for r in EvalResult.select().dicts()])


def prefix_strip(x):
    for prefix in ["together_ai/", "meta-llama/", "Qwen/", "gemini/"]:
        if x.startswith(prefix):
            x = x[len(prefix) :]
    return x


results = (
    results.groupby(["model_name", "eval_name"])
    .result.mean()
    .sort_values(ascending=False)
    .reset_index()
    .assign(
        model_name=lambda x: x.model_name.map(prefix_strip),
    )
)


for eval_name, df in results.groupby("eval_name"):
    st.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("result", title="Score"),
            y=alt.Y(
                "model_name",
                sort=None,
                title="Model",
                axis=alt.Axis(
                    labelLimit=200,
                ),
            ),
        )
        .properties(title=eval_name),
        use_container_width=True,
    )
