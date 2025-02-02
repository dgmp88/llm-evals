import altair as alt
import pandas as pd
import streamlit as st

from llm_evals.db import EvalResult

# Pull in the data
results = pd.DataFrame([r for r in EvalResult.select().dicts()])

results = (
    results.groupby(["model_name", "eval_name"])
    .result.mean()
    .sort_values(ascending=False)
    .reset_index()
    .assign(
        model_name=lambda x: x.model_name.str.replace("together_ai/", ""),
    )
)


for eval_name, df in results.groupby("eval_name"):
    st.altair_chart(
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                "model_name",
                sort=None,
                title="Model",
                # axis=alt.Axis(labelAngle=-45)
            ),
            y=alt.Y("result", title="Score"),
        )
        .properties(title=eval_name),
        use_container_width=True,
    )
