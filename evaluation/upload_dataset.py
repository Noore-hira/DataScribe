from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

client = Client()

csv_path = Path(r"F:\Projects\DataScribe\src\evaluation\datasets\planner_dataset.csv")

df = pd.read_csv(csv_path)

dataset = client.create_dataset(
    dataset_name="Planner Evaluation",
    description="Planner node evaluation dataset",
)

for _, row in df.iterrows():
    client.create_example(
        inputs={
            "user_query": row["user_query"],
            #"df_schema": row["df_schema"],
            # Optional: if your dataset contains it
            #"execution_plan": row.get("execution_plan", ""),
        },
        outputs={
            "difficulty": row["difficulty"],
        },
        dataset_id=dataset.id,
    )

print(f"Dataset created: {dataset.id}")