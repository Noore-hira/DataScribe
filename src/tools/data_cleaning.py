from langchain_core.tools import tool
from data_frame import global_df

@tool
def clean_dataframe_tool() -> str:
    """
    Use this tool to automatically clean the dataset BEFORE writing any analysis code.
    ONLY trigger this tool if the user explicitly requests cleaning or if the schema shows nulls.
    """
    global global_df
    
    print("[TOOL EXECUTION] Imputing missing values in dataframe...")
    
    # REMOVED: global_df.columns = global_df.columns.str.lower()...
    # Do not mutate column names; it causes KeyErrors in the generated code!

    num_cols = global_df.select_dtypes(include=['number']).columns
    if len(num_cols) > 0:
        global_df[num_cols] = global_df[num_cols].fillna(global_df[num_cols].median())
        
    cat_cols = global_df.select_dtypes(include=['object']).columns
    if len(cat_cols) > 0:
        global_df[cat_cols] = global_df[cat_cols].fillna('Unknown')
        
    return "SUCCESS: Missing values imputed. You may now write the Pandas code using the ORIGINAL column names."
