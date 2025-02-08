import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import database.adepts_sanctions
import database.managers_sanctions

# Set page configuration
st.set_page_config(page_title="Análise de Castigos Clubes", layout="wide")

def initialize_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "Castigos Dirigentes/Treinadores"

initialize_session_state()

@st.cache_data(ttl=60)  # Cache for 1 minute
def fetch_data_from_api(type):
    """Fetch data from API with caching"""
    if type == "adepts_sanctions": 
        response = database.adepts_sanctions.get_sanctions()
    elif type == "managers_sanctions":
        response = database.managers_sanctions.get_sanctions()
    else:
        response = {"response": [], "success": False} 
    return response

def display_dataframe(df, height="auto"):
    """Helper function to display DataFrame with custom settings"""
    st.markdown('<div class="centered-table">', unsafe_allow_html=True)
    col1, centerTable, col3 = st.columns([5.5, 10, 5])
    with centerTable:
        centerTable.dataframe(df,
                 column_config={
                     "club_group": "Clube",
                     "quantity": st.column_config.NumberColumn(format="%d"),
                     "suspension_days": st.column_config.NumberColumn(format="%d")
                 },
                 hide_index=True,
                 height=height)
    st.markdown('</div>', unsafe_allow_html=True)


# Function to load and process data
def load_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


# Function to get clubs by sanctions count
def get_clubs_data(df, limit=None):
    if df.empty:
        return df
    data = (df.groupby('club_group').agg({
        'quantity': 'sum',
        'fines': 'sum',
        'suspension_days': 'sum'
    }).sort_values('quantity', ascending=False).reset_index().rename(
        columns={
            'quantity': 'Total Castigos',
            'fines': 'Total Multas',
            'suspension_days': 'Total Dias de Suspensão'
        }
    ))
    if limit:
        return data.head(limit)
    return data


def display_summary_statistics(df):
    #st.subheader("Estatíticas")
    col1, col2, col3, col4, col5 = st.columns([1, 6, 7, 2, 1])

    with col2:
        if 'quantity' in df: 
            total_sanctions = df['quantity'].sum()
            st.metric("Total Castigos", f"{total_sanctions:,}")
        else:
            st.metric("Total Castigos", f"{0:,}")

    with col3:
        if 'fines' in df:
            total_fines = df['fines'].sum()
            st.metric("Total Multas", f"{total_fines:,.2f}€")
        else:
            st.metric("Total Multas", f"{0:,.2f}€")

    with col4:
        if 'suspension_days' in df:
            total_suspension_days = df['suspension_days'].sum()
            st.metric("Total Dias de Suspensão", f"{total_suspension_days:,}")
        else:
            st.metric("Total Dias de Suspensão", f"{0:,}")


def create_cumulative_sanctions_chart(df, top_10_clubs):
    # Filter for top 10 clubs
    filtered_df = df[df['club_group'].isin(top_10_clubs['club_group'])]

    # Create daily sanctions per club
    daily_sanctions = (filtered_df.groupby(
        ['date', 'club_group', 'quantity']).size().reset_index(name='count'))

    # Calculate cumulative sanctions for each club
    daily_sanctions = daily_sanctions.sort_values('date')
    cumulative_sanctions = []

    for club in top_10_clubs['club_group']:
        club_data = daily_sanctions[daily_sanctions['club_group'] == club].copy()

        club_data['cumulative_count'] = club_data['quantity'].cumsum()
        cumulative_sanctions.append(club_data)

    cumulative_df = pd.concat(cumulative_sanctions)

    # Calculate total cumulative sanctions
    total_daily = (daily_sanctions.groupby('date')['quantity'].sum().reset_index())
    total_daily['cumulative_count'] = total_daily['quantity'].cumsum()

    fig = px.line(cumulative_df,
                  x='date',
                  y='cumulative_count',
                  color='club_group',
                  title='Castigos Acumulados por Clube',
                  labels={
                      'cumulative_count': 'Castigos',
                      'date': 'Data',
                      'club_group': 'Clube'
                  })

    #fig.add_trace(
    #    go.Scatter(x=total_daily['date'],
    #               y=total_daily['cumulative_count'],
    #               name='Total Todos Clubes',
    #               line=dict(color='black', width=3, dash='dash'),
    #               mode='lines'))

    fig.update_layout(showlegend=True,
                      legend=dict(yanchor="top",
                                  y=0.99,
                                  xanchor="left",
                                  x=1.05),
                      height=600,
                      yaxis_title="Número de Castigos Acumulados por Clube")

    return fig


def main_page(df):
    st.markdown(
        """
        <style>
        .centered-title {
            text-align: center;
            font-size: 30px;
            font-weight: bold;
        }
        </style>
        <h1 class="centered-title">AF Porto Análise de Castigos</h1>
        """,
        unsafe_allow_html=True
    )

    # Creating columns to center the buttons
    col1, center, col3 = st.columns(3)  # The middle column is larger to center content
    with center:
        selection = st.selectbox(
            "Escolha uma opção",  # Label for the select box
            options=["Castigos Dirigentes/Treinadores", "Castigos Público"],  # List of options
            index=0 if st.session_state.current_view == "Castigos Dirigentes/Treinadores" else 1,
            key="navigation"
        )

        # Action based on the selection
        if selection != st.session_state.current_view:
            if selection == "Castigos Dirigentes/Treinadores":
                st.session_state.page = "main"
                st.session_state.current_view = "Castigos Dirigentes/Treinadores" 
                st.rerun()

            elif selection == "Castigos Público":
                st.session_state.page = "page_adepts"
                st.session_state.current_view = "Castigos Público"
                st.rerun()
        
    # Top 10 Clubs Table
    #st.markdown("""<h3 class="centered-title"> Castigos Dirigentes/Treinadores </h3> """, unsafe_allow_html=True)
    st.subheader("Castigos Dirigentes/Treinadores")
    # Summary Statistics
    display_summary_statistics(df)

    #st.subheader("Castigos Dirigentes/Treinadores")
    top_10_df = get_clubs_data(df, limit=10)

    if df.empty: 
        st.write("Sem dados no momento")
    else: 
        # Format the numeric columns
        formatted_df = top_10_df.copy()
        formatted_df['Total Multas'] = formatted_df['Total Multas'].map('{:,.2f}€'.format)

        # Calculate required height based on number of rows (approximately 35px per row plus header)
        table_height = (len(formatted_df) * 35) + 40
        display_dataframe(formatted_df, height=table_height)

        # Centered "See More" button
        col1, centerButton, col3 = st.columns([6, 2, 5])
        with centerButton: 
            if centerButton.button("Ver Mais"):
                st.session_state.page = "details_managers"
                st.rerun()

        # Cumulative Sanctions Graph
        st.subheader("Castigos ao longo do Tempo")
        fig = create_cumulative_sanctions_chart(df, top_10_df)
        st.plotly_chart(fig, use_container_width=True)


def details_managers_sanctions_page(df):
    st.markdown(
        """
        <style>
        .centered-title {
            text-align: center;
            font-size: 30px;
            font-weight: bold;
        }
        </style>
        <h1 class="centered-title">AF Porto Análise de Castigos</h1>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""<h3 class="centered-title"> Castigos Dirigentes/Treinadores </h3> """, unsafe_allow_html=True)

    #st.subheader("Tabela Completa de Castigos Dirigentes/Treinadores")
    # Summary Statistics
    display_summary_statistics(df)

    # Full table
    full_df = get_clubs_data(df)

    # Format the numeric columns
    formatted_df = full_df.copy()
    formatted_df['Total Multas'] = formatted_df['Total Multas'].map('{:,.2f}€'.format)

    # Calculate required height based on number of rows
    table_height = (len(formatted_df) * 35) + 40

    # Centered "Back" button
    col1, col2, col3, col4, col5 = st.columns([1, 6, 7, 2, 1])
    with col2: 
        if col2.button("Voltar"):
            st.session_state.page = "main"
            st.rerun()

    display_dataframe(formatted_df, height=table_height)


def adepts_sanctions_page(df):
    st.markdown(
        """
        <style>
        .centered-title {
            text-align: center;
            font-size: 30px;
            font-weight: bold;
        }
        </style>
        <h1 class="centered-title">AF Porto Análise de Castigos</h1>
        """,
        unsafe_allow_html=True
    )

    # Creating columns to center the buttons
    col1, center, col3 = st.columns(3)  # The middle column is larger to center content
    with center:
        selection = st.selectbox(
            "Escolha uma opção",  # Label for the select box
            options=["Castigos Dirigentes/Treinadores", "Castigos Público"],  # List of options
            index=0 if st.session_state.current_view == "Castigos Dirigentes/Treinadores" else 1,
            key="navigation"
        )

        # Action based on the selection
        if selection != st.session_state.current_view:
            if selection == "Castigos Dirigentes/Treinadores":
                st.session_state.page = "main"
                st.session_state.current_view = "Castigos Dirigentes/Treinadores" 
                st.rerun()

            elif selection == "Castigos Público":
                st.session_state.page = "page_adepts"
                st.session_state.current_view = "Castigos Público"
                st.rerun()

    st.subheader("Castigos ao Público")
    # Summary Statistics
    display_summary_statistics(df)

    # Top 10 Clubs Table
    top_10_df = get_clubs_data(df, limit=10)


    if df.empty: 
        st.write("Sem dados no momento")
    else: 
        # Format the numeric columns
        formatted_df = top_10_df.copy()
        formatted_df['Total Multas'] = formatted_df['Total Multas'].map('{:,.2f}€'.format)
        # Calculate required height based on number of rows (approximately 35px per row plus header)
        table_height = (len(formatted_df) * 35) + 40
        display_dataframe(formatted_df, height=table_height)

        # Centered "See More" button
        col1, centerButton, col3 = st.columns([6, 2, 5])
        with centerButton: 
            if centerButton.button("Ver Mais"):
                st.session_state.page = "details_adepts"
                st.rerun()

        # Cumulative Sanctions Graph
        st.subheader("Castigos ao longo do Tempo")
        fig = create_cumulative_sanctions_chart(df, top_10_df)
        st.plotly_chart(fig, use_container_width=True)

def details_adepts_sanctions_page(df):
    st.markdown(
        """
        <style>
        .centered-title {
            text-align: center;
            font-size: 30px;
            font-weight: bold;
        }
        </style>
        <h1 class="centered-title">AF Porto Análise de Castigos</h1>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""<h3 class="centered-title"> Castigos Público </h3> """, unsafe_allow_html=True)

    # Summary Statistics
    display_summary_statistics(df)

    # Full table
    full_df = get_clubs_data(df)

    # Format the numeric columns
    formatted_df = full_df.copy()
    formatted_df['Total Multas'] = formatted_df['Total Multas'].map(
        '{:,.2f}€'.format)

    # Calculate required height based on number of rows
    table_height = (len(formatted_df) * 35) + 40

    col1, col2, col3, col4, col5 = st.columns([1, 6, 7, 2, 1])
    with col2: 
        if col2.button("Voltar"):
            st.session_state.page = "page_adepts"
            st.rerun()

    display_dataframe(formatted_df, height=table_height)

    # Centered "Back" button

def main():
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "main"

    # File uploader
    #uploaded_file = st.file_uploader("Upload JSON file", type=['json'])

    #if uploaded_file is not None:
    # Load data
    sanctions_managers = fetch_data_from_api("managers_sanctions")
    df_sanctions_managers = pd.DataFrame()
    if sanctions_managers['success'] == True:
        print('Using managers database...')
        df_sanctions_managers = pd.DataFrame(sanctions_managers['response'])
    else: 
        print("Using managers json...")
        df_sanctions_managers = pd.read_json("sanctions_managers_db.json")
   
    if 'date' in df_sanctions_managers:
        df_sanctions_managers['date'] = pd.to_datetime(df_sanctions_managers['date'])

    sanctions_adepts = fetch_data_from_api("adepts_sanctions")
    df_sanctions_adepts = pd.DataFrame()
    if sanctions_managers['success'] == True:
        print('Using adepts database...')
        df_sanctions_adepts = pd.DataFrame(sanctions_adepts['response'])
    else: 
        print("Using adepts json...")
        df_sanctions_adepts = pd.read_json("sanctions_adepts_db.json")
    
    if 'date' in df_sanctions_adepts: 
        df_sanctions_adepts['date'] = pd.to_datetime(df_sanctions_adepts['date'])

    # Display appropriate page
    if st.session_state.page == "main":
        main_page(df_sanctions_managers)
    elif st.session_state.page == "details_managers":
        details_managers_sanctions_page(df_sanctions_managers)
    elif st.session_state.page == "page_adepts":
        adepts_sanctions_page(df_sanctions_adepts)
    elif st.session_state.page == "details_adepts":
        details_adepts_sanctions_page(df_sanctions_adepts)


if __name__ == "__main__":
    main()
