import pandas as pd
from pathlib import Path

# LangGraph Studio does not guarantee that the server's current working
# directory is the repository root.  Resolve the bundled sample data relative
# to this module instead.
DATA_PATH = Path(__file__).resolve().with_name("sales_data.csv")


def load_dataframe() -> pd.DataFrame:
    """Return a new dataset for each graph run instead of sharing mutable state."""
    return pd.read_csv(DATA_PATH)


# Backward compatibility for exploratory scripts. Graph nodes must call
# `load_dataframe()` so concurrent Studio runs cannot affect each other.
global_df = load_dataframe()
    
