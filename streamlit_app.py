import pandas as pd
import streamlit as st

from llm_evals.db import EvalResult

results = [r for r in EvalResult.select().dicts()]

results = pd.DataFrame(results)
st.markdown(results.to_markdown())
