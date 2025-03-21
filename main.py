import plotly.figure_factory as ff
import pandas as pd
from datetime import datetime

# Sample data
df = [
    dict(Task="Research", Start='2023-01-01', Finish='2023-02-28', Resource='Person A'),
    dict(Task="Design", Start='2023-03-01', Finish='2023-04-15', Resource='Person B'),
    dict(Task="Development", Start='2023-04-16', Finish='2023-07-31', Resource='Person C'),
    dict(Task="Testing", Start='2023-08-01', Finish='2023-09-15', Resource='Person D'),
    dict(Task="Deployment", Start='2023-09-16', Finish='2023-10-01', Resource='Person E')
]

# Create the Gantt chart
fig = ff.create_gantt(df, colors=['#008B8B', '#DAA520', '#9370DB', '#20B2AA', '#FF4500'], 
                     index_col='Resource', show_colorbar=True, group_tasks=True)

# Customize layout
fig.update_layout(
    title='Project Timeline',
    xaxis_title='Date',
    yaxis_title='Task',
    height=600,
    width=900
)

fig.show()