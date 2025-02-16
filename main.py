import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import database.adepts_sanctions
import database.managers_sanctions
import database.clubs_details

# Set page configuration
st.set_page_config(page_title="Análise de Castigos Clubes", layout="wide")

data_gps = pd.DataFrame({
    'latitude': [41.16326520961089],
    'longitude': [-8.583252689196224]
})

def initialize_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "Castigos Dirigentes/Treinadores"
    if 'selected_club' not in st.session_state: 
        st.session_state.selected_club = ""


initialize_session_state()

@st.cache_data(ttl=60)  # Cache for 1 minute
def fetch_data_from_api(type):
    """Fetch data from API with caching"""
    if type == "adepts_sanctions": 
        response = database.adepts_sanctions.get_sanctions()
    elif type == "managers_sanctions":
        response = database.managers_sanctions.get_sanctions()
    elif type == "clubs_info":
        response = database.clubs_details.get_clubs_info()
    else:
        response = {"response": [], "success": False} 
    return response

def display_dataframe(df, height="auto", type="default"):
    porpotion = [5.5, 10, 5]
    if type == "adepts":
        porpotion = [7, 9, 5]
    elif type == "details_adepts":
        porpotion = [7.5, 9, 5]
    col1, centerTable, col3 = st.columns(porpotion)
    with centerTable:
        centerTable.dataframe(df,
            column_config={
                "club_group": "Clube",
                "Total Castigos": st.column_config.NumberColumn(format="%d"),
                "Total Dias de Suspensão": st.column_config.NumberColumn(format="%d"),
            },
        hide_index=True,
        height=height)
    
# Function to load and process data
def load_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


# Function to get clubs by sanctions count
def get_clubs_data(df, limit=None, type="default"):
    if df.empty:
        return df
    
    aggregation = {
        'quantity': 'sum',
        'fines': 'sum',
        'suspension_days': 'sum'
    }

    columns = {
        'quantity': 'Total Castigos',
        'fines': 'Total Multas',
        'suspension_days': 'Total Dias de Suspensão'
    }
   
    if type != "default":
        del aggregation['suspension_days']
        del columns['suspension_days']

    data = (df.groupby('club_group').agg(aggregation).sort_values('quantity', ascending=False).reset_index().rename(
        columns=columns
    ))
    if limit:
        return data.head(limit)
    return data


def display_summary_statistics(df, type="default"):
    #st.subheader("Estatíticas")
    porpotion = [1, 6, 7, 2, 1]
    if type == "adepts":
        porpotion = [1, 6, 6, 2, 1]
    col1, col2, col3, col4, col5 = st.columns(porpotion)

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
        if type == "default":
            if 'suspension_days' in df:
                total_suspension_days = df['suspension_days'].sum()
                st.metric("Total Dias de Suspensão", f"{total_suspension_days:,}")
            else:
                st.metric("Total Dias de Suspensão", f"{0:,}")
        if type == "adepts":
            if 'club_group' in df:
                total_clubs = len(df['club_group'].unique())
                st.metric("Total de Clubes Castigados", f"{total_clubs}")
            else:
                st.metric("Total de Clubes Castigados", f"{0}")


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
        }
    )
    
    # Add markers to show points explicitly
    fig.update_traces(mode='lines+markers')
    
    # Update x-axis format to show only date
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Número de Castigos Acumulados",
        height=400,
        xaxis=dict(
            tickformat="%d %B %Y",
            tickformatstops=[
                dict(dtickrange=[None, None], value="%d %B %Y")
            ]
        ),
        legend=dict(
            orientation="h",    # horizontal orientation
            yanchor="top",
            y=-0.2,            # position below the graph
            xanchor="center",
            x=0.5
        )
    )

    #fig.add_trace(
    #    go.Scatter(x=total_daily['date'],
    #               y=total_daily['cumulative_count'],
    #               name='Total Todos Clubes',
    #               line=dict(color='black', width=3, dash='dash'),
    #               mode='lines'))

    fig.update_layout(showlegend=True,
                      #legend=dict(yanchor="top",
                     #             y=0.99,
                     #             xanchor="left",
                     #             x=1.05),
                      height=600,
                      yaxis_title="Número de Castigos Acumulados por Clube")

    return fig

def club_selector(df):
    """Creates a select box with unique club names and handles navigation"""
    # Get unique club names and sort them
    unique_clubs = sorted(df['club_group'].unique())
    
    # Create the select box with a default empty option
    col1, select_box, col3 = st.columns([3, 7, 3])
    with select_box: 
        selected_club = st.selectbox(
            "Pesquise por Clube",
            options=[""] + list(unique_clubs),
            index=0,
            key="club_selector"
        )
        
        # Navigate to details page if a club is selected
        if selected_club:
            st.session_state.previous_page = st.session_state.page
            st.session_state.page = "club_details"
            st.session_state.selected_club = selected_club
            st.rerun()

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
    display_menu()
        
    # Top 10 Clubs Table
    #st.markdown("""<h3 class="centered-title"> Castigos Dirigentes/Treinadores </h3> """, unsafe_allow_html=True)
    #st.subheader("Castigos Dirigentes/Treinadores")
    # Summary Statistics

    #st.subheader("Castigos Dirigentes/Treinadores")
    top_10_df = get_clubs_data(df, limit=10)

    if df.empty: 
        st.write("Sem dados no momento")
    else: 
        # Format the numeric columns
        formatted_df = top_10_df.copy()
        formatted_df['Total Multas'] = formatted_df['Total Multas'].map('{:,.2f}€'.format)
        #formatted_df['Detalhes'] = formatted_df["club_group"]
        
        display_summary_statistics(df)

        club_selector(df)
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
    #display_menu()
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

    club_selector(df)
    display_dataframe(formatted_df, height=table_height)

def display_menu():
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

def display_club_menu(club_name):
    col1, center, col3 = st.columns(3)  # The middle column is larger to center content
    with center:
        selection = st.selectbox(
            "Escolha uma opção",  # Label for the select box
            options=["", "Estatisticas", "Contactos"],  # List of options
            key="key"
        )
        # Action based on the selection
        if selection != st.session_state.current_view:
            if selection == "Estatisticas":
                st.session_state.page = "club_details"
                st.session_state.current_view = "Estatisticas" 
                st.session_state.selected_club = club_name
                st.rerun()

            elif selection == "Contactos":
                st.session_state.page = "club_contacts"
                st.session_state.current_view = "Contactos"
                st.session_state.selected_club = club_name
                st.rerun()

def club_contacts_page(df_clubs, df_name):
    club_info = df_clubs[df_clubs['alias'].astype(str).str.strip() == str(df_name).strip()]
    display_club_menu(df_name)
    st.markdown(f"""
        <h1 class="centered-title">{df_name}</h1>
        """, unsafe_allow_html=True)
    # Back button at the top
    col1, col2, col3, col4, col5 = st.columns([1, 6, 7, 2, 1])
    with col1:
        if st.button("Voltar"):
            st.session_state.page = st.session_state.previous_page
            st.rerun()

    info, map = st.columns(2)
    with info:
        if not club_info.empty:
            labels, image = info.columns(2)
            with image:
                image.image(club_info["img_url"].iloc[0], width=200)
            with labels:
                labels.subheader("Clube")
                labels.markdown(f"**{club_info["name"].iloc[0]}**")
                labels.subheader("Cidade")
                labels.markdown(f"**{club_info["city"].iloc[0]}**")
                labels.subheader("AF Porto Website")
                labels.page_link(page=club_info["url"].iloc[0], label=club_info["url"].iloc[0])
        else:
            st.write("Sem dados de contacto.")
        #info.dataframe(club_info)
    with map:
        if "latitude" in club_info and "longitude" in club_info: 
            gps_data = pd.DataFrame({
                'latitude': [club_info["latitude"].iloc[0]],
                'longitude': [club_info["longitude"].iloc[0]]
            })
            map.map(data=gps_data, zoom=14)
        else:
            map.map(data=data_gps, zoom=15)

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
    display_menu()

    #st.subheader("Castigos ao Público")
    # Summary Statistics

    # Top 10 Clubs Table
    top_10_df = get_clubs_data(df, limit=10, type="adepts")


    if df.empty: 
        st.write("Sem dados no momento")
    else: 
        display_summary_statistics(df, type="adepts")
        club_selector(df)
        # Format the numeric columns
        formatted_df = top_10_df.copy()
        formatted_df['Total Multas'] = formatted_df['Total Multas'].map('{:,.2f}€'.format)
        # Calculate required height based on number of rows (approximately 35px per row plus header)
        table_height = (len(formatted_df) * 35) + 40
        display_dataframe(formatted_df, height=table_height, type="adepts")

        # Centered "See More" button
        col1, centerButton, col3 = st.columns([5.6, 2, 5])
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
    display_summary_statistics(df, "adepts")
    # Full table
    full_df = get_clubs_data(df, type="clubs")

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

    club_selector(df)
    display_dataframe(formatted_df, height=table_height, type="details_adepts")

    # Centered "Back" button

# Add this new function for the club details page
def display_club_graphs(df_managers, df_adepts, club_name):
    display_club_menu(club_name)
    st.markdown(f"""
        <h1 class="centered-title">Evolução dos Castigos: {club_name}</h1>
        """, unsafe_allow_html=True)
    
    # Back button at the top
    col1, col2, col3, col4, col5 = st.columns([1, 6, 7, 2, 1])
    with col1:
        if st.button("Voltar"):
            st.session_state.page = st.session_state.previous_page
            st.rerun()
    
    # Filter data for this club
    
    # Create timeline graphs
    st.subheader("Castigos Dirigentes/Treinadores")
    if not df_managers.empty:  # Changed from not empty to length check
        club_managers = df_managers[df_managers['club_group'].astype(str).str.strip() == str(club_name).strip()]
        display_summary_statistics(club_managers)
        timeline_managers = club_managers.groupby('date')['quantity'].sum().reset_index()
        timeline_managers = timeline_managers.sort_values('date')
        print(timeline_managers)
        
        # If there's only one entry, duplicate it to show a point
        if len(timeline_managers) == 1:
            single_date = timeline_managers.iloc[0]['date']
            single_quantity = timeline_managers.iloc[0]['quantity']
            # Create a second point 1 day later with the same cumulative value
            new_row = pd.DataFrame({
                'date': [single_date+pd.Timedelta(days=-1), single_date, single_date+pd.Timedelta(days=1)],
                'quantity': [0, single_quantity, 0]
            })
            timeline_managers = pd.concat([new_row], ignore_index=True)
        
        timeline_managers['cumulative_sanctions'] = timeline_managers['quantity'].cumsum()
        
        fig_managers = px.line(timeline_managers, 
                             x='date', 
                             y='cumulative_sanctions',
                             title=f'Evolução dos Castigos Dirigentes/Treinadores - {club_name}')
        
        # Add markers to show points explicitly
        fig_managers.update_traces(mode='lines+markers')
        
        # Update x-axis format to show only date
        fig_managers.update_layout(
            xaxis_title="Data",
            yaxis_title="Número de Castigos Acumulados",
            height=400,
            xaxis=dict(
                tickformat="%d %B %Y",
                tickformatstops=[
                    dict(dtickrange=[None, None], value="%d %B %Y")
                ]
            ),
             legend=dict(
                orientation="h",    # horizontal orientation
                yanchor="top",
                y=-0.2,            # position below the graph
                xanchor="center",
                x=0.5
            )
        )
        
        # Format hover text to include daily quantity
        fig_managers.update_traces(
            hovertemplate="Data: %{x|%d %B %Y}<br>Total Acumulado: %{y}<br>Castigos no Dia: %{text}<extra></extra>",
            text=timeline_managers['quantity']
        )
        
        st.plotly_chart(fig_managers, use_container_width=True)
    else:
        st.write("Sem dados de castigos para dirigentes/treinadores")
    
    st.subheader("Castigos Público")
    if not df_adepts.empty:  # Changed from not empty to length check
        club_adepts = df_adepts[df_adepts['club_group'].astype(str).str.strip() == str(club_name).strip()]
        display_summary_statistics(club_adepts, type="club")
        timeline_adepts = club_adepts.groupby('date')['quantity'].sum().reset_index()
        timeline_adepts = timeline_adepts.sort_values('date')
        
        # If there's only one entry, duplicate it to show a point
        if len(timeline_adepts) == 1:
            single_date = timeline_adepts.iloc[0]['date']
            single_quantity = timeline_adepts.iloc[0]['quantity']
            # Create a second point 1 day later with the same cumulative value
            new_row = pd.DataFrame({
                'date': [single_date+pd.Timedelta(days=-1), single_date, single_date+pd.Timedelta(days=1)],
                'quantity': [0, single_quantity, 0]
            })
            timeline_adepts = pd.concat([new_row], ignore_index=True)
        
        timeline_adepts['cumulative_sanctions'] = timeline_adepts['quantity'].cumsum()
        
        fig_adepts = px.line(timeline_adepts, 
                            x='date', 
                            y='cumulative_sanctions',
                            title=f'Evolução dos Castigos Público - {club_name}')
        
        # Add markers to show points explicitly
        fig_adepts.update_traces(mode='lines+markers')
        
        # Update x-axis format to show only date
        fig_adepts.update_layout(
            xaxis_title="Data",
            yaxis_title="Número de Castigos Acumulados",
            height=400,
            xaxis=dict(
                tickformat="%d %B %Y",
                tickformatstops=[
                    dict(dtickrange=[None, None], value="%d %B %Y")
                ]
            ),
            legend=dict(
                orientation="h",    # horizontal orientation
                yanchor="top",
                y=-0.2,            # position below the graph
                xanchor="center",
                x=0.5
            )
        )
        
        # Format hover text to include daily quantity
        fig_adepts.update_traces(
            hovertemplate="Data: %{x|%d %B %Y}<br>Total Acumulado: %{y}<br>Castigos no Dia: %{text}<extra></extra>",
            text=timeline_adepts['quantity']
        )
        
        st.plotly_chart(fig_adepts, use_container_width=True)
    else:
        st.write("Sem dados de castigos para público")

# Update the main() function to include the new club_details page
def main():
    # Initialize session state
    initialize_session_state()
    if 'selected_club' not in st.session_state:
        st.session_state.selected_club = None
    if 'previous_page' not in st.session_state:
        st.session_state.previous_page = "main"
    
    # Load data (your existing data loading code remains the same)
    sanctions_managers = fetch_data_from_api("managers_sanctions")
    df_sanctions_managers = pd.DataFrame()
    if sanctions_managers['success'] == True:
        df_sanctions_managers = pd.DataFrame(sanctions_managers['response'])
    else:
        df_sanctions_managers = pd.read_json("sanctions_managers_db.json")
    
    if 'date' in df_sanctions_managers:
        df_sanctions_managers['date'] = pd.to_datetime(df_sanctions_managers['date'])
    
    sanctions_adepts = fetch_data_from_api("adepts_sanctions")
    df_sanctions_adepts = pd.DataFrame()
    if sanctions_managers['success'] == True:
        df_sanctions_adepts = pd.DataFrame(sanctions_adepts['response'])
    else:
        df_sanctions_adepts = pd.read_json("sanctions_adepts_db.json")
    
    if 'date' in df_sanctions_adepts:
        df_sanctions_adepts['date'] = pd.to_datetime(df_sanctions_adepts['date'])

    clubs_info = fetch_data_from_api("clubs_info")
    df_clubs_info = pd.DataFrame()
    if clubs_info['success'] == True:
        df_clubs_info = pd.DataFrame(clubs_info['response'])
    else:
        df_clubs_info = []
    
    # Display appropriate page
    if st.session_state.page == "club_details":
        display_club_graphs(df_sanctions_managers, df_sanctions_adepts, st.session_state.selected_club)
    elif st.session_state.page == "main":
        main_page(df_sanctions_managers)
    elif st.session_state.page == "details_managers":
        details_managers_sanctions_page(df_sanctions_managers)
    elif st.session_state.page == "page_adepts":
        adepts_sanctions_page(df_sanctions_adepts)
    elif st.session_state.page == "details_adepts":
        details_adepts_sanctions_page(df_sanctions_adepts)
    elif st.session_state.page == "club_contacts":
        club_contacts_page(df_clubs_info, st.session_state.selected_club)

if __name__ == "__main__":
    main()
