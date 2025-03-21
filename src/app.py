import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime
import json
from dotenv import load_dotenv
import sys
import traceback

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import data processing functions
from src.data_processing import (
    load_data, 
    get_project_names,
    filter_data_by_project,
    create_gantt_chart,
    create_project_status_table,
    create_dev_type_pie_chart,
    create_stage_bar_chart,
    create_process_area_pie_chart,
    create_landing_page_overview,
    create_milestone_table,
    query_groq_api
)

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Project Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0078ff;
        color: white;
    }
    .status-table th {
        background-color: #f0f2f6;
        font-weight: bold;
    }
    .overview-card {
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
    }
    .milestone-complete {
        color: green;
        font-weight: bold;
    }
    .milestone-partial {
        color: orange;
    }
    .milestone-pending {
        color: red;
    }
    .green-100 {
        background-color: #28a745 !important;
        color: white !important;
    }
    .green-50 {
        background-color: #d4edda !important;
    }
    .amber {
        background-color: #ffeeba !important;
    }
    .red {
        background-color: #f8d7da !important;
    }
    .nav-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }
    .nav-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-right: 20px;
    }
    .divider {
        border-top: 1px solid #e9ecef;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def main_dashboard(df):
    """Main dashboard function displaying all project analytics"""
    if df is not None:
        # Get project names
        project_names = get_project_names(df)
        
        # Create navigation options
        nav_options = ["Overview"] + project_names
        
        # Create top navigation menu
        st.markdown('<div class="nav-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown('<span class="nav-title">Navigation:</span>', unsafe_allow_html=True)
        
        with col2:
            selected_nav = st.selectbox(
                "",
                options=nav_options,
                index=0,
                key="navigation_menu",
                label_visibility="collapsed"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display content based on the selected option
        if selected_nav == "Overview":
            # Overview Tab
            st.title("Project Portfolio Overview")
            
            # Top metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Projects", len(project_names))
            
            with col2:
                total_developments = len(df)
                st.metric("Total Developments", total_developments)
            
            with col3:
                completed_dev = len(df[pd.notna(df['Dev Actual Delivery Date'])])
                if total_developments > 0:
                    completion_percentage = round(completed_dev / total_developments * 100, 1)
                else:
                    completion_percentage = 0
                st.metric("Completed Developments", f"{completed_dev} ({completion_percentage}%)")
            
            with col4:
                in_progress = len(df[(pd.notna(df['Dev Actual Start Date'])) & (pd.isna(df['Dev Actual Delivery Date']))])
                if total_developments > 0:
                    in_progress_percentage = round(in_progress / total_developments * 100, 1)
                else:
                    in_progress_percentage = 0
                st.metric("In Progress", f"{in_progress} ({in_progress_percentage}%)")
            
            # Projects overview
            st.subheader("Projects Overview")
            overview_df = create_landing_page_overview(df)
            st.dataframe(overview_df, use_container_width=True)
            
            # Milestone table
            st.subheader("Project Milestones")
            milestone_df = create_milestone_table(df)
            
            # Define a function to color code the milestone cells
            def color_milestone_cells(val):
                if "%" not in str(val):
                    return ""
                
                # Extract percentage value
                try:
                    percent_val = float(str(val).split('(')[-1].split('%')[0])
                    
                    if percent_val == 100:
                        return 'background-color: #28a745; color: white'  # Green for 100%
                    elif percent_val >= 50:
                        return 'background-color: #d4edda'  # Light green for ≥50%
                    elif percent_val > 0:
                        return 'background-color: #ffeeba'  # Amber for >0% and <50%
                    else:
                        return 'background-color: #f8d7da'  # Red for 0%
                except:
                    return ""
            
            # Display the styled dataframe
            display_cols = [col for col in milestone_df.columns if '%' not in col]  # Filter out percentage columns
            styled_df = milestone_df[display_cols].style.applymap(color_milestone_cells)
            st.dataframe(styled_df, use_container_width=True)
            
            # Overall charts
            st.subheader("Portfolio Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Overall Dev Type distribution
                dev_type_counts = df['Dev Type'].value_counts().reset_index()
                dev_type_counts.columns = ['Dev Type', 'Count']
                
                fig1 = px.pie(dev_type_counts, values='Count', names='Dev Type', 
                             title='Development Type Distribution',
                             color_discrete_sequence=px.colors.qualitative.Plotly)
                fig1.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Overall Stage distribution
                stage_counts = df['Stage'].value_counts().reset_index()
                stage_counts.columns = ['Stage', 'Count']
                
                fig2 = px.bar(stage_counts, x='Stage', y='Count', 
                             title='Development Stages',
                             color='Count',
                             color_continuous_scale='Viridis')
                st.plotly_chart(fig2, use_container_width=True)
        else:
            # Project-specific tab
            project_name = selected_nav
            project_df = filter_data_by_project(df, project_name)
            
            st.title(f"{project_name} Dashboard")
            
            # Project metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_items = len(project_df)
                st.metric("Total Developments", total_items)
            
            with col2:
                completed = len(project_df[pd.notna(project_df['Dev Actual Delivery Date'])])
                if total_items > 0:
                    completion_percentage = round(completed / total_items * 100, 1)
                else:
                    completion_percentage = 0
                st.metric("Completed", f"{completed} ({completion_percentage}%)")
            
            with col3:
                in_progress = len(project_df[(pd.notna(project_df['Dev Actual Start Date'])) & (pd.isna(project_df['Dev Actual Delivery Date']))])
                if total_items > 0:
                    in_progress_percentage = round(in_progress / total_items * 100, 1)
                else:
                    in_progress_percentage = 0
                st.metric("In Progress", f"{in_progress} ({in_progress_percentage}%)")
            
            with col4:
                on_hold = len(project_df[pd.notna(project_df['ON Hold Reason'])])
                if total_items > 0:
                    on_hold_percentage = round(on_hold / total_items * 100, 1)
                else:
                    on_hold_percentage = 0
                st.metric("On Hold", f"{on_hold} ({on_hold_percentage}%)")
            
            # Project charts in 3 sections
            project_tabs = st.tabs(["Dev Types & Process Areas", "Project Status", "Gantt Chart"])
            
            # Dev Types and Process Areas
            with project_tabs[0]:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Dev Type pie chart
                    dev_type_fig = create_dev_type_pie_chart(df, project_name)
                    st.plotly_chart(dev_type_fig, use_container_width=True)
                
                with col2:
                    # Process Area pie chart
                    process_area_fig = create_process_area_pie_chart(df, project_name)
                    st.plotly_chart(process_area_fig, use_container_width=True)
                
                # Stage bar chart
                stage_fig = create_stage_bar_chart(df, project_name)
                st.plotly_chart(stage_fig, use_container_width=True)
            
            # Project Status Table
            with project_tabs[1]:
                st.subheader("Project Status Details")
                
                # Filters for project status
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    sprint_options = ["All"] + sorted(project_df['Sprint'].dropna().unique().tolist())
                    selected_sprint = st.selectbox("Sprint", sprint_options, key=f"status_sprint_{project_name}")
                    sprint_filter = None if selected_sprint == "All" else selected_sprint
                
                with col2:
                    dev_name_filter = st.text_input("Development Name Contains", key=f"status_dev_{project_name}")
                
                with col3:
                    stage_options = ["All"] + sorted(project_df['Stage'].dropna().unique().tolist())
                    selected_stage = st.selectbox("Stage", stage_options, key=f"status_stage_{project_name}")
                    stage_filter = None if selected_stage == "All" else selected_stage
                
                with col4:
                    complexity_options = ["All"] + sorted(project_df['Complexity'].dropna().unique().tolist())
                    selected_complexity = st.selectbox("Complexity", complexity_options, key=f"status_complexity_{project_name}")
                    complexity_filter = None if selected_complexity == "All" else selected_complexity
                
                # Create and display status table
                status_table = create_project_status_table(
                    df, 
                    project_name, 
                    sprint=sprint_filter, 
                    dev_name=dev_name_filter if dev_name_filter else None, 
                    stage=stage_filter, 
                    complexity=complexity_filter
                )
                st.dataframe(status_table, use_container_width=True)
                
                # Development details table with filtered data
                st.subheader("Development Items")
                filtered_project_df = project_df.copy()
                
                if sprint_filter:
                    filtered_project_df = filtered_project_df[filtered_project_df['Sprint'] == sprint_filter]
                if dev_name_filter:
                    filtered_project_df = filtered_project_df[filtered_project_df['FSD / Development Name'].str.contains(dev_name_filter, na=False)]
                if stage_filter:
                    filtered_project_df = filtered_project_df[filtered_project_df['Stage'] == stage_filter]
                if complexity_filter:
                    filtered_project_df = filtered_project_df[filtered_project_df['Complexity'] == complexity_filter]
                
                # Select important columns to display - handle variations in column names
                display_columns = []
                
                # Add core columns if they exist
                for col_name in ['Development ID', 'FSD / Development Name', 'Stage', 'Process Area', 'Complexity', 'Priority of Delivery']:
                    if col_name in filtered_project_df.columns:
                        display_columns.append(col_name)
                
                # Handle Dev Lead column variations
                dev_lead_col = None
                if 'Dev Lead' in filtered_project_df.columns:
                    dev_lead_col = 'Dev Lead'
                elif 'Dev Lead ' in filtered_project_df.columns:  # Note the space
                    dev_lead_col = 'Dev Lead '
                else:
                    # Try to find a column that contains "Dev Lead"
                    dev_lead_cols = [col for col in filtered_project_df.columns if 'Dev Lead' in col]
                    if dev_lead_cols:
                        dev_lead_col = dev_lead_cols[0]
                
                if dev_lead_col:
                    display_columns.append(dev_lead_col)
                
                # Add date and status columns if they exist
                date_status_cols = [
                    'Dev Planned Delivery Date', 'Dev Actual Delivery Date', 
                    'ABAP Status', 'PI Status', 'FUT Status'
                ]
                
                for col in date_status_cols:
                    if col in filtered_project_df.columns:
                        display_columns.append(col)
                
                # Only show available columns
                available_columns = display_columns
                
                st.dataframe(filtered_project_df[available_columns], use_container_width=True)
            
            # Gantt Chart
            with project_tabs[2]:
                st.subheader("Project Timeline")
                
                # Filters for Gantt chart
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    gantt_sprint_options = ["All"] + sorted(project_df['Sprint'].dropna().unique().tolist())
                    gantt_selected_sprint = st.selectbox("Sprint", gantt_sprint_options, key=f"gantt_sprint_{project_name}")
                    gantt_sprint_filter = None if gantt_selected_sprint == "All" else gantt_selected_sprint
                
                with col2:
                    gantt_stage_options = ["All"] + sorted(project_df['Stage'].dropna().unique().tolist())
                    gantt_selected_stage = st.selectbox("Stage", gantt_stage_options, key=f"gantt_stage_{project_name}")
                    gantt_stage_filter = None if gantt_selected_stage == "All" else gantt_selected_stage
                
                with col3:
                    # Handle case where Dev Lead column might be named differently
                    try:
                        if 'Dev Lead' in project_df.columns:
                            dev_lead_col = 'Dev Lead'
                        elif 'Dev Lead ' in project_df.columns:  # Note the space
                            dev_lead_col = 'Dev Lead '
                        else:
                            # Try to find a column that contains "Dev Lead"
                            dev_lead_cols = [col for col in project_df.columns if 'Dev Lead' in col]
                            dev_lead_col = dev_lead_cols[0] if dev_lead_cols else None
                        
                        if dev_lead_col:
                            gantt_lead_options = ["All"] + sorted(project_df[dev_lead_col].dropna().unique().tolist())
                            gantt_selected_lead = st.selectbox("Dev Lead", gantt_lead_options, key=f"gantt_lead_{project_name}")
                            gantt_lead_filter = None if gantt_selected_lead == "All" else gantt_selected_lead
                        else:
                            st.text("Dev Lead column not found")
                            gantt_lead_filter = None
                    except Exception as e:
                        st.warning(f"Could not load Dev Lead options: {str(e)}")
                        gantt_lead_filter = None
                
                # Create and display Gantt chart
                gantt_fig = create_gantt_chart(
                    df, 
                    project_name, 
                    sprint=gantt_sprint_filter, 
                    stage=gantt_stage_filter, 
                    dev_lead=gantt_lead_filter
                )
                
                if gantt_fig:
                    st.plotly_chart(gantt_fig, use_container_width=True)
                else:
                    st.warning("No timeline data available with the selected filters.")
                
                # Show deadline information
                st.subheader("Development Deadlines")
                
                deadline_df = project_df.copy()
                
                if gantt_sprint_filter:
                    deadline_df = deadline_df[deadline_df['Sprint'] == gantt_sprint_filter]
                if gantt_stage_filter:
                    deadline_df = deadline_df[deadline_df['Stage'] == gantt_stage_filter]
                if gantt_lead_filter and dev_lead_col:
                    deadline_df = deadline_df[deadline_df[dev_lead_col] == gantt_lead_filter]
                
                # Select and display deadline information
                deadline_columns = [
                    'Development ID', 'FSD / Development Name',
                    'Dev Planned Start Date', 'Dev Planned Delivery Date', 
                    'Dev Actual Start Date', 'Dev Actual Delivery Date',
                    'ABAP Planned Delivery Date', 'ABAP Actual Delivery Date',
                    'PI Planned Delivery Date', 'PI Actual Delivery Date'
                ]
                
                # Only show available columns that exist in the dataframe
                available_deadline_columns = [col for col in deadline_columns if col in deadline_df.columns]
                
                st.dataframe(deadline_df[available_deadline_columns], use_container_width=True)

def main():
    """Main application entry point handling data loading and UI setup"""
    # Sidebar for file upload and project selection
    st.sidebar.title("Project Analytics Dashboard")
    st.sidebar.image("https://img.icons8.com/color/96/000000/dashboard-layout.png", width=100)

    uploaded_file = st.sidebar.file_uploader("Upload Excel Data File", type=["xlsx", "xls"])

    # Data holder
    if 'data' not in st.session_state:
        st.session_state.data = None

    # Load data from file
    if uploaded_file is not None:
        try:
            # Load the data
            df = load_data(uploaded_file)
            
            # Save to session state
            st.session_state.data = df
            
            st.sidebar.success("Data loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")
            st.stop()
    # If no file is uploaded, try to load from default path
    elif st.session_state.data is None:
        try:
            default_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "Data_dump.xlsx")
            if os.path.exists(default_path):
                df = load_data(default_path)
                st.session_state.data = df
                st.sidebar.info("Using default data file")
            else:
                st.sidebar.warning("No data file found. Please upload an Excel file.")
                st.stop()
        except Exception as e:
            st.sidebar.error(f"Error loading default data: {str(e)}")
            st.stop()
    else:
        # Use data from session state
        df = st.session_state.data

    # GROQ AI Query Section in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Ask about your data")
    query = st.sidebar.text_area("Enter your question", height=100)

    if st.sidebar.button("Ask AI"):
        if query:
            with st.sidebar:
                with st.spinner("Processing your question..."):
                    # Create a simplified context from the data
                    context_df = df.head(100)  # Limit to prevent too large context
                    data_context = context_df.to_string()
                    
                    # Query the AI
                    response = query_groq_api(query, data_context)
                    
                    # Display response
                    st.markdown("### AI Response")
                    st.markdown(response)
        else:
            st.sidebar.warning("Please enter a question")

    # Run the main dashboard
    main_dashboard(df)

# Entry point
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())
        
        # Provide more helpful error information
        if "Dev Lead" in str(e):
            st.warning("""
            The error seems to be related to the 'Dev Lead' column. This can happen if:
            1. The column is named differently in your Excel file (e.g., 'Dev Lead ' with an extra space)
            2. The column doesn't exist in your Excel file
            
            Check the column names and try uploading the file again.
            """)
        
        # Show dataframe sample to help with debugging
        try:
            if 'df' in locals() and df is not None:
                with st.expander("Show data sample for debugging"):
                    st.write("First 5 rows of the dataset:")
                    st.dataframe(df.head())
        except Exception:
            pass