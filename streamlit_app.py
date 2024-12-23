import pandas as pd
import streamlit as st
import plotly.express as px
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

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

# Function to filter dataframe
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 100:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

# Function to visualize data
def visualize_data(data):
    st.header("Data Visualization")

    # Filter dataframe
    filtered_data = filter_dataframe(data)

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
