import pandas as pd
import os
import plotly.express as px
import plotly.figure_factory as ff
from dotenv import load_dotenv
import datetime
import streamlit as st

def standardize_column_names(df):
    """
    Standardize column names to handle common variations and whitespace issues
    """
    # Create a mapping of common variations
    column_mapping = {}
    
    # Clean up column names (trim whitespace, etc.)
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    
    # Check for specific column variations
    for col in df.columns:
        # Handle 'Dev Lead' variations
        if isinstance(col, str) and 'dev lead' in col.lower() and col != 'Dev Lead':
            column_mapping[col] = 'Dev Lead'
    
    # Rename columns based on the mapping
    if column_mapping:
        df = df.rename(columns=column_mapping)
    
    return df

def load_data(file_path):
    """
    Load data from an Excel file into a pandas DataFrame
    """
    try:
        df = pd.read_excel(file_path)
        
        # Standardize column names
        df = standardize_column_names(df)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def get_project_names(df):
    """
    Get unique project names from the DataFrame
    """
    return sorted(df['Project Name'].unique())

def filter_data_by_project(df, project_name):
    """
    Filter data by project name
    """
    return df[df['Project Name'] == project_name]

def create_gantt_chart(df, project_name, sprint=None, stage=None, dev_lead=None):
    """
    Create a Gantt chart for project milestones
    """
    # Filter data
    filtered_df = df[df['Project Name'] == project_name]
    
    if sprint:
        filtered_df = filtered_df[filtered_df['Sprint'] == sprint]
    if stage:
        filtered_df = filtered_df[filtered_df['Stage'] == stage]
    if dev_lead:
        # Handle case where Dev Lead column might be named differently
        if 'Dev Lead' in df.columns:
            filtered_df = filtered_df[filtered_df['Dev Lead'] == dev_lead]
        elif 'Dev Lead ' in df.columns:  # Note the space
            filtered_df = filtered_df[filtered_df['Dev Lead '] == dev_lead]
        else:
            # Try to find a column that contains "Dev Lead"
            dev_lead_cols = [col for col in df.columns if 'Dev Lead' in col]
            if dev_lead_cols:
                filtered_df = filtered_df[filtered_df[dev_lead_cols[0]] == dev_lead]
    
    # Prepare data for Gantt chart
    gantt_data = []
    
    for _, row in filtered_df.iterrows():
        # Development dates
        if pd.notna(row.get('Dev Planned Start Date')) and pd.notna(row.get('Dev Planned Delivery Date')):
            gantt_data.append(dict(
                Task=f"Dev: {row.get('Development ID', 'Unknown')}",
                Start=row['Dev Planned Start Date'].date() if isinstance(row['Dev Planned Start Date'], datetime.datetime) else row['Dev Planned Start Date'],
                Finish=row['Dev Planned Delivery Date'].date() if isinstance(row['Dev Planned Delivery Date'], datetime.datetime) else row['Dev Planned Delivery Date'],
                Resource='Development'
            ))
        
        # ABAP development dates
        if pd.notna(row.get('Dev Actual Start Date')) and pd.notna(row.get('ABAP Planned Delivery Date')):
            gantt_data.append(dict(
                Task=f"ABAP: {row.get('Development ID', 'Unknown')}",
                Start=row['Dev Actual Start Date'].date() if isinstance(row['Dev Actual Start Date'], datetime.datetime) else row['Dev Actual Start Date'],
                Finish=row['ABAP Planned Delivery Date'].date() if isinstance(row['ABAP Planned Delivery Date'], datetime.datetime) else row['ABAP Planned Delivery Date'],
                Resource='ABAP'
            ))
        
        # PI development dates
        if pd.notna(row.get('Dev Actual Start Date')) and pd.notna(row.get('PI Planned Delivery Date')):
            gantt_data.append(dict(
                Task=f"PI: {row.get('Development ID', 'Unknown')}",
                Start=row['Dev Actual Start Date'].date() if isinstance(row['Dev Actual Start Date'], datetime.datetime) else row['Dev Actual Start Date'],
                Finish=row['PI Planned Delivery Date'].date() if isinstance(row['PI Planned Delivery Date'], datetime.datetime) else row['PI Planned Delivery Date'],
                Resource='PI'
            ))
    
    if not gantt_data:
        return None
    
    # Create Gantt chart
    fig = ff.create_gantt(gantt_data, colors={
        'Development': 'rgb(46, 137, 205)',
        'ABAP': 'rgb(114, 44, 121)',
        'PI': 'rgb(198, 47, 105)'
    }, index_col='Resource', show_colorbar=True, group_tasks=True)
    
    fig.update_layout(
        title=f"Project Timeline: {project_name}",
        xaxis_title="Date",
        yaxis_title="Tasks",
        height=600,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    
    return fig

def create_project_status_table(df, project_name, sprint=None, dev_name=None, stage=None, complexity=None):
    """
    Create a project status table with completion metrics
    """
    # Filter data
    filtered_df = df[df['Project Name'] == project_name]
    
    if sprint:
        filtered_df = filtered_df[filtered_df['Sprint'] == sprint]
    if dev_name:
        filtered_df = filtered_df[filtered_df['FSD / Development Name'].str.contains(dev_name, na=False)]
    if stage:
        filtered_df = filtered_df[filtered_df['Stage'] == stage]
    if complexity:
        filtered_df = filtered_df[filtered_df['Complexity'] == complexity]
    
    # Calculate status metrics
    total_items = len(filtered_df)
    
    # Calculate status percentages for different aspects
    development_status = calculate_status_percentages(filtered_df, total_items)
    
    # Create a summary DataFrame
    status_df = pd.DataFrame({
        'Category': list(development_status.keys()),
        'Completed %': [development_status[key]['completed'] for key in development_status.keys()],
        'In Progress %': [development_status[key]['in_progress'] for key in development_status.keys()],
        'Pending %': [development_status[key]['pending'] for key in development_status.keys()],
        'On Hold %': [development_status[key]['on_hold'] for key in development_status.keys()],
    })
    
    return status_df

def calculate_status_percentages(df, total_items):
    """Helper function to calculate percentages of different statuses"""
    
    # Initialize status dictionary
    status_dict = {
        'Development': {'completed': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0},
        'ABAP': {'completed': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0},
        'PI': {'completed': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0},
        'FUT': {'completed': 0, 'in_progress': 0, 'pending': 0, 'on_hold': 0}
    }
    
    if total_items == 0:
        return status_dict
    
    # Development status
    completed = len(df[pd.notna(df['Dev Actual Delivery Date'])])
    on_hold = len(df[pd.notna(df['ON Hold Reason'])])
    in_progress = len(df[(pd.notna(df['Dev Actual Start Date'])) & (pd.isna(df['Dev Actual Delivery Date']))])
    pending = total_items - completed - in_progress - on_hold
    
    status_dict['Development'] = {
        'completed': round(completed / total_items * 100, 1),
        'in_progress': round(in_progress / total_items * 100, 1),
        'pending': round(pending / total_items * 100, 1),
        'on_hold': round(on_hold / total_items * 100, 1)
    }
    
    # ABAP status
    completed = len(df[pd.notna(df['ABAP Actual Delivery Date'])])
    on_hold = len(df[pd.notna(df['ON Hold Reason'])])
    in_progress = len(df[(pd.notna(df['Dev Actual Start Date'])) & (pd.isna(df['ABAP Actual Delivery Date']))])
    pending = total_items - completed - in_progress - on_hold
    
    status_dict['ABAP'] = {
        'completed': round(completed / total_items * 100, 1),
        'in_progress': round(in_progress / total_items * 100, 1),
        'pending': round(pending / total_items * 100, 1),
        'on_hold': round(on_hold / total_items * 100, 1)
    }
    
    # PI status
    completed = len(df[pd.notna(df['PI Actual Delivery Date'])])
    on_hold = len(df[pd.notna(df['ON Hold Reason'])])
    in_progress = len(df[(pd.notna(df['Dev Actual Start Date'])) & (pd.isna(df['PI Actual Delivery Date']))])
    pending = total_items - completed - in_progress - on_hold
    
    status_dict['PI'] = {
        'completed': round(completed / total_items * 100, 1),
        'in_progress': round(in_progress / total_items * 100, 1),
        'pending': round(pending / total_items * 100, 1),
        'on_hold': round(on_hold / total_items * 100, 1)
    }
    
    # FUT status
    fut_completed = len(df[df['FUT Status'] == 'Completed'])
    fut_on_hold = len(df[pd.notna(df['FUT On Hold Reason'])])
    fut_in_progress = len(df[(df['FUT Status'] == 'In Progress')])
    fut_pending = total_items - fut_completed - fut_in_progress - fut_on_hold
    
    status_dict['FUT'] = {
        'completed': round(fut_completed / total_items * 100, 1),
        'in_progress': round(fut_in_progress / total_items * 100, 1),
        'pending': round(fut_pending / total_items * 100, 1),
        'on_hold': round(fut_on_hold / total_items * 100, 1)
    }
    
    return status_dict

def create_dev_type_pie_chart(df, project_name):
    """
    Create a pie chart of Dev Type for the specified project
    """
    filtered_df = df[df['Project Name'] == project_name]
    
    # Count occurrences of each Dev Type
    dev_type_counts = filtered_df['Dev Type'].value_counts().reset_index()
    dev_type_counts.columns = ['Dev Type', 'Count']
    
    # Create pie chart
    fig = px.pie(dev_type_counts, values='Count', names='Dev Type', 
                 title=f'Development Types for {project_name}',
                 color_discrete_sequence=px.colors.qualitative.Plotly)
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    
    return fig

def create_stage_bar_chart(df, project_name):
    """
    Create a bar chart of Stages for the specified project
    """
    filtered_df = df[df['Project Name'] == project_name]
    
    # Count occurrences of each Stage
    stage_counts = filtered_df['Stage'].value_counts().reset_index()
    stage_counts.columns = ['Stage', 'Count']
    
    # Create bar chart
    fig = px.bar(stage_counts, x='Stage', y='Count', 
                 title=f'Stages for {project_name}',
                 color='Count',
                 color_continuous_scale='Viridis')
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    
    return fig

def create_process_area_pie_chart(df, project_name):
    """
    Create a pie chart of Process Areas for the specified project
    """
    filtered_df = df[df['Project Name'] == project_name]
    
    # Count occurrences of each Process Area
    process_area_counts = filtered_df['Process Area'].value_counts().reset_index()
    process_area_counts.columns = ['Process Area', 'Count']
    
    # Create pie chart
    fig = px.pie(process_area_counts, values='Count', names='Process Area', 
                 title=f'Process Areas for {project_name}',
                 color_discrete_sequence=px.colors.qualitative.Plotly)
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    
    return fig

def create_landing_page_overview(df):
    """
    Create an overview table for the landing page with all projects and key metrics
    """
    project_names = get_project_names(df)
    overview_data = []
    
    for project in project_names:
        project_df = df[df['Project Name'] == project]
        
        # Get dev leads - handle case where column might be named differently
        try:
            if 'Dev Lead' in project_df.columns:
                dev_leads = project_df['Dev Lead'].dropna().unique()
            elif 'Dev Lead ' in project_df.columns:  # Note the space
                dev_leads = project_df['Dev Lead '].dropna().unique()
            else:
                # Try to find a column that contains "Dev Lead"
                dev_lead_cols = [col for col in project_df.columns if 'Dev Lead' in col]
                if dev_lead_cols:
                    dev_leads = project_df[dev_lead_cols[0]].dropna().unique()
                else:
                    dev_leads = []
            dev_leads_str = ', '.join(dev_leads) if len(dev_leads) > 0 else 'Not assigned'
        except Exception:
            dev_leads_str = 'Not assigned'
        
        # Get process areas
        process_areas = project_df['Process Area'].dropna().unique()
        process_areas_str = ', '.join(process_areas) if len(process_areas) > 0 else 'Not specified'
        
        # Calculate stage statistics
        stages = project_df['Stage'].value_counts().to_dict()
        stage_str = ', '.join([f"{k}: {v}" for k, v in stages.items()])
        
        # Calculate FUT status
        fut_status = project_df['FUT Status'].value_counts().to_dict()
        fut_str = ', '.join([f"{k}: {v}" for k, v in fut_status.items()]) if fut_status else 'Not started'
        
        # Add to overview data
        overview_data.append({
            'Project Name': project,
            'Stages': stage_str,
            'Process Areas': process_areas_str,
            'Dev Leads': dev_leads_str,
            'FUT Status': fut_str,
            'Total Developments': len(project_df)
        })
    
    overview_df = pd.DataFrame(overview_data)
    return overview_df

def create_milestone_table(df):
    """
    Create a milestone table with project phase overall status
    """
    project_names = get_project_names(df)
    milestone_data = []
    
    for project in project_names:
        project_df = df[df['Project Name'] == project]
        
        # Calculate percentages
        total = len(project_df)
        
        fsd_received = len(project_df[pd.notna(project_df['FSD Recieved Date'])])
        fsd_walkthrough = len(project_df[pd.notna(project_df['FSD Actual Walkthrough Date'])])
        dev_started = len(project_df[pd.notna(project_df['Dev Actual Start Date'])])
        dev_completed = len(project_df[pd.notna(project_df['Dev Actual Delivery Date'])])
        abap_completed = len(project_df[pd.notna(project_df['ABAP Actual Delivery Date'])])
        pi_completed = len(project_df[pd.notna(project_df['PI Actual Delivery Date'])])
        fut_completed = len(project_df[project_df['FUT Status'] == 'Completed'])
        
        # Calculate percentages
        fsd_received_pct = round(fsd_received/total*100 if total > 0 else 0, 1)
        fsd_walkthrough_pct = round(fsd_walkthrough/total*100 if total > 0 else 0, 1)
        dev_started_pct = round(dev_started/total*100 if total > 0 else 0, 1)
        dev_completed_pct = round(dev_completed/total*100 if total > 0 else 0, 1)
        abap_completed_pct = round(abap_completed/total*100 if total > 0 else 0, 1)
        pi_completed_pct = round(pi_completed/total*100 if total > 0 else 0, 1)
        fut_completed_pct = round(fut_completed/total*100 if total > 0 else 0, 1)
        
        milestone_data.append({
            'Project Name': project,
            'FSD Received': f"{fsd_received}/{total} ({fsd_received_pct}%)",
            'FSD Received %': fsd_received_pct,
            'FSD Walkthrough': f"{fsd_walkthrough}/{total} ({fsd_walkthrough_pct}%)",
            'FSD Walkthrough %': fsd_walkthrough_pct,
            'Dev Started': f"{dev_started}/{total} ({dev_started_pct}%)",
            'Dev Started %': dev_started_pct,
            'Dev Completed': f"{dev_completed}/{total} ({dev_completed_pct}%)",
            'Dev Completed %': dev_completed_pct,
            'ABAP Completed': f"{abap_completed}/{total} ({abap_completed_pct}%)",
            'ABAP Completed %': abap_completed_pct,
            'PI Completed': f"{pi_completed}/{total} ({pi_completed_pct}%)",
            'PI Completed %': pi_completed_pct,
            'FUT Completed': f"{fut_completed}/{total} ({fut_completed_pct}%)",
            'FUT Completed %': fut_completed_pct
        })
    
    milestone_df = pd.DataFrame(milestone_data)
    return milestone_df

def query_groq_api(query, data_context):
    """
    Query the GROQ API with the given query and data context
    """
    import os
    import requests
    import json
    
    # Load API key from .env file
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return "Error: GROQ API key not found in .env file"
    
    # Prepare the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare prompt with context
    prompt = f"""
    You are a data analytics assistant. Answer the following question based on the provided project data context:
    
    Question: {query}
    
    Data Context:
    {data_context}
    
    Provide a concise and accurate response based only on the data provided.
    """
    
    data = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                                headers=headers, 
                                data=json.dumps(data))
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"Error querying GROQ API: {str(e)}"