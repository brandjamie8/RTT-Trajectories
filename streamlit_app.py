import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_extras.dataframe_explorer import dataframe_explorer

# Function to load data
def load_data():
    uploaded_file = st.file_uploader("Upload your RTT dataset (CSV format)", type="csv")
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        # Rename 'Clock Stops' to 'Non-Admitted Clock Stops'
        data['Type'] = data['Type'].replace({'Clock Stops': 'Non-Admitted Clock Stops'})
        return data
    else:
        st.warning("Please upload a dataset to proceed.")
        return None

# Function to visualize data
def visualize_data(data):
    st.header("Data Visualization")

    # Filter dataframe
    filtered_data = dataframe_explorer(data)

    # Metrics filter
    metrics = ['Non-Admitted Clock Stops', 'Admitted Clock Stops', 'Incomplete Pathways', 'Incomplete Admitted Pathways', 'Clock Starts']
    selected_metric = st.selectbox("Select Metric", metrics)

    # Split by TF Name
    split_by_tf = st.checkbox("Split by TF Name")

    if split_by_tf:
        fig = px.bar(filtered_data[filtered_data['Type'] == selected_metric], 
                     x='Month', 
                     y='Pathways', 
                     color='TF Name', 
                     title=f"{selected_metric} Split by TF Name",
                     barmode='stack')
    else:
        aggregated_data = filtered_data[filtered_data['Type'] == selected_metric].groupby('Month', as_index=False)['Pathways'].sum()
        fig = px.line(aggregated_data, 
                      x='Month', 
                      y='Pathways', 
                      title=f"Total {selected_metric} Over Time")

    st.plotly_chart(fig)

# Function to set trajectories
def set_trajectories(data):
    st.header("Set Trajectories for Next Year")
    
    # Select TF Name or Total
    tf_options = ['Total'] + data['TF Name'].unique().tolist()
    selected_tf = st.selectbox("Select TF Name (or Total for all)", tf_options)

    # Trajectory setting
    start_month = "April 2025"
    end_month = "March 2026"
    months = pd.date_range(start=start_month, end=end_month, freq='MS').strftime("%B %Y").tolist()

    trajectory = {}
    st.write(f"Set trajectories for each month from {start_month} to {end_month}")
    for month in months:
        trajectory[month] = st.number_input(f"{month} Pathways", min_value=0, value=0, step=1, key=month)

    # Export trajectory as a DataFrame
    trajectory_df = pd.DataFrame(list(trajectory.items()), columns=['Month', 'Pathways'])
    st.write("Trajectory Data:")
    st.dataframe(trajectory_df)

    # Option to download trajectory
    csv = trajectory_df.to_csv(index=False)
    st.download_button("Download Trajectory Data", csv, "trajectory.csv", "text/csv")

# Main Streamlit app
def main():
    st.set_page_config(layout="wide", page_title="RTT Trajectories")
    st.title("RTT Trajectories App")

    data = load_data()
    if data is not None:
        # Visualize data
        visualize_data(data)

        # Set trajectories
        set_trajectories(data)

if __name__ == "__main__":
    main()
