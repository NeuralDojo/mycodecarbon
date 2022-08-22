from ctypes import alignment
from re import X
from matplotlib.axis import XAxis
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import plotly.graph_objects as got
import psycopg2
from PIL import Image
from datetime import datetime


st.set_page_config(page_title = 'Code Carbon Dashboard',
                    layout="wide")


#DATABASE CONNECTIONS
params_db = {
    "host" : "35.173.205.131",
    "database" : "dbCodeCarbon",
    "user" : "uCodeCarbonStreamlit",
    "password" : "KmycodecarbonS1$"
}

def connect(params_db):
    conn = None
    try:
        #print("Connecting to the CodeCarbon database...")
        conn = psycopg2.connect(**params_db)
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1)
    print("Connection Successful")
    return conn

def psql_to_dataframe(conn, sql_query):
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        col_names = []
        for elt in cursor.description:
            col_names.append(elt[0])
    except(Exception, psycopg2.DatabaseError) as error:
        print("Error: %s " % error)
        return 1
    
    tupples = cursor.fetchall()
    cursor.close()
    df = pd.DataFrame(tupples, columns=col_names)
    
    return df

#DATASETS 
conn = connect(params_db)
df_emissions = psql_to_dataframe(conn,"Select * from emissions")
conn.close()

df_emissions_day = df_emissions.groupby([df_emissions['datetime'].dt.date]).sum().reset_index()

#GENERAL SELECTORS
# Add a selectbox to the sidebar:
add_selectbox_project = st.sidebar.multiselect(
    'Select Project Name',
    df_emissions.project_name.unique()
)


#Evaluating box selections
if (len(add_selectbox_project)==0):
    pass 
else:
    df_emissions = df_emissions.query('project_name==@add_selectbox_project')

#GREEN FACTORS
F_car = 4.03e-4 #car miles drive
F_ee_year = 5.139 #Homes ee use for one year
F_smartphones = 8.22e-6 #smartphones charged
F_diesel = 10.180e-3 #diesel consumed
F_coal = 9.04e-4 #pounds of coal burned
F_tree = 0.060

#LOADING IMAGES
img_time = Image.open('img/time.png')
img_co2 = Image.open('img/co2.png')
img_energy = Image.open('img/energy.png')
img_car = Image.open('img/car.png')
img_home = Image.open('img/home.png')
img_smartphone = Image.open('img/smartphone.png')
img_diesel = Image.open('img/diesel.png')
img_coal = Image.open('img/coal.png')
img_tree = Image.open('img/tree.png')

#DATA PREPROCESSIONG
df_emissions['f_car'] = df_emissions.emissions/1000/F_car
df_emissions['f_ee_year'] = df_emissions.emissions/1000/F_ee_year
df_emissions['f_smartphones'] = df_emissions.emissions/1000/F_smartphones
df_emissions['f_diesel'] = df_emissions.emissions/1000/F_diesel
df_emissions['f_coal'] = df_emissions.emissions/1000/F_coal
df_emissions['f_tree'] = df_emissions.emissions/1000/F_tree

#cumulative visual duration

df_emissions_cum = df_emissions[['duration','emissions','energy_consumed','datetime']].sort_values(by='datetime', ascending = True)
df_emissions_cum['date'] = df_emissions_cum.datetime.dt.date

df_emissions_cum = df_emissions_cum.groupby(by='date').sum().cumsum().reset_index()

#green data for only green kpi's
green_data = df_emissions.iloc[:,-6:].sum()

#COLORS
color1 = px.colors.sequential.Plasma
color2 = px.colors.sequential.Emrld
color3 = px.colors.sequential.Tealgrn

#VISUAL FIGURES
fig_geo = px.scatter_geo(df_emissions, lat='latitude',lon='longitude', size = 'emissions',
                     color = 'country_name',
                     hover_name='country_name', labels=['emissions'],color_discrete_sequence=color1,
                     width=1000, height=600)

fig_geo.update_layout(showlegend = False,legend=dict(yanchor="bottom", y=0.9, xanchor="left", x=0.1))

#bar plot emissions by country
fig_country_emissions = px.bar(df_emissions.groupby(by='country_name').sum()['emissions'].reset_index(), 
             x = 'emissions', y='country_name', title = 'Emissions by Country',
             color_discrete_sequence=color2,
            template = 'plotly_dark',
            width=600,height=600)

#Pieplot by project_name
fig_pie_emissions_project = px.pie(df_emissions, values='emissions', names='project_name', title='Emissions CO2 by Project',
             template = 'plotly_dark', color_discrete_sequence=color2,
             width=700, height=300)
                     
#Pieplot by CPU and GPU
data = [df_emissions.cpu_power.sum(), df_emissions.gpu_power.sum(), df_emissions.ram_power.sum()]
fig_hardware = px.pie(values=data, names=['cpu','gpu','ram'], title='Energy by Hardware (kwh)',
             template = 'plotly_dark', color_discrete_sequence=color2,
             width=400, height=300)

#bar plot datime
fig_daily_emissions = px.bar(df_emissions_day, x = 'datetime', y='emissions', title = 'Daily Emissions CO2',
            template = 'plotly_dark',color_discrete_sequence=color3)

fig_daily_emissions.update_layout(
    autosize=True,
    xaxis_title="Date", yaxis_title="Emissions CO2",
    width=600

)

#bar plot duration
fig_daily_duration = px.bar(df_emissions_day, x = 'datetime', y='duration', 
                             title = 'Daily Time Training (seconds)',
                            template = 'plotly_dark')

fig_daily_duration.update_layout(
    autosize=True,
    xaxis_title="Date", yaxis_title="Time Training Duration (seconds)",
    width=600
)

#cumulative duration
fig_duration = px.line(df_emissions_cum, x="date", y="duration", line_shape='spline',
                        template='plotly_dark', width=600, height=400)

fig_duration.update_layout(
    showlegend=False,
    title = "Cumulative"
)


#cumulative emissions
fig_emissions = px.line(df_emissions_cum, x="date", y="emissions", line_shape='spline',
                        template='plotly_dark', width=600, height=400)

fig_emissions.update_layout(
    showlegend=False,
    title = "Cumulative"
)

#cumulative energy
fig_energy = px.line(df_emissions_cum, x="date", y="energy_consumed", 
                        template='plotly_dark', width=600, height=400)

fig_energy.update_layout(
    showlegend=False,
    title = "Cumulative"
)

#PLOTING VISUALS STREAMLIT PANELS
#GENERAL SETTINGS

h1,h2 = st.columns([1,2])
h1.image("img/ai_green1.png",width=350)
h2.title("My Code Carbon Dashboard")
h2.write("AI can benefit society in many ways but, given the energy needed \n"+
          "to support the computing behind AI, these benefits can come at a high environmental price.")
h2.write("CodeCarbon is a lightweight software package that seamlessly integrates into your Python codebase. \n"+
        "It estimates the amount of carbon dioxide (CO2) produced by the cloud or personal computing resources used \n"+
        "to execute the code.")
h2.write("It then shows developers how they can lessen emissions by optimizing their code or by hosting their cloud \n"+
        "infrastructure in geographical regions that use renewable energy sources.")

h2.markdown("Thanks to: [Code Carbon](https://codecarbon.io/)")

##GREEN KPIS

st.markdown("""---""")
#TOTAL EMISSIONS
kpi_gl1,kpi_gl2,kpi_gl3 = st.columns(3)

kpi_gl1.metric(label="Total Training Duration (hours)", value=np.round(df_emissions.duration.sum()/3600,3))
kpi_gl1.image(img_time, width=60)
#kpi_gl1.plotly_chart(fig_duration)

kpi_gl2.metric(label="Total Training Emissions (CO2 eq. in Kg)", value=np.round(df_emissions.emissions.sum(),3))
kpi_gl2.image(img_co2, width=60)
#kpi_gl2.plotly_chart(fig_emissions)

kpi_gl3.metric(label="Total Training Energy Consumed (kWh)", value=np.round(df_emissions.energy_consumed.sum(),3))
kpi_gl3.image(img_energy, width=60)
#kpi_gl3.plotly_chart(fig_energy)

st.markdown("""---""")

kpi1,kpi2,kpi3,kpi4,kpi5,kpi6 = st.columns(6)

kpi1.metric(label="Car Miles Drive", value=np.round(green_data[0],3)) # Car miles drive
kpi1.image(img_car,width=40)
kpi1.write("Miles driven by an average gasoline-powered passenger vehicle.")

kpi2.metric(label="Homes' electricity use for one year", value=np.round(green_data[1],3)) # homes' electricity use for one year 
kpi2.image(img_home)
kpi2.write("Annual home electricity consumption was multiplied by the carbon dioxide emission rate \n"
            "(per unit of electricity delivered) to determine annual carbon dioxide emissions per home.")

kpi3.metric(label="Number of smartphones charged", value=np.round(green_data[2],3))  #smartphones charged
kpi3.image(img_smartphone, width=40)
kpi3.write("Carbon dioxide emissions per smartphone charged were determined by multiplying the energy use per smartphone \n"
            "charged by the national weighted average carbon dioxide marginal emission rate for delivered electricity.")

kpi4.metric(label="Gallons of diesel consumed", value=np.round(green_data[3],3)) #gallons of diesel consumed
kpi4.image(img_diesel, width = 40)
kpi4.write("For reference, to obtain the number of grams of CO2 emitted per gallon of diesel combusted, the heat content \n"
            "of the fuel per gallon can be multiplied by the kg CO2 per heat content of the fuel.")

kpi5.metric(label="Pounds of coal burned", value=np.round(green_data[4],3)) #Pounds of coal burned
kpi5.image(img_coal, width = 40)
kpi5.write("Carbon dioxide emissions per pound of coal were determined by multiplying heat content times the carbon \n"
            "coefficient times the fraction oxidized times the ratio of the molecular weight of carbon dioxide to that of carbon (44/12)..")

kpi6.metric(label="Tree seedlings grown for 10 years", value=np.round(green_data[5],3)) # trees seedlings grown
kpi6.image(img_tree, width=40)
kpi6.write("A medium growth coniferous or deciduous tree, planted in an urban setting and allowed to grow for 10 years, \n"
            "sequesters 23.2 and 38.0 lbs of carbon, respectively.")


##PLOTS 

st.subheader("Geo Emissions")
col_geo1, col_geo2 = st.columns([2,1])
col_geo1.plotly_chart(fig_geo)
col_geo2.plotly_chart(fig_country_emissions)


st.markdown("""---""")

col1, col2 = st.columns(2)
col1.plotly_chart(fig_pie_emissions_project)
col2.plotly_chart(fig_hardware)

st.subheader("Emissions by date")

col3, col4 = st.columns(2)

col3.plotly_chart(fig_daily_emissions)
col3.plotly_chart(fig_emissions)

col4.plotly_chart(fig_daily_duration)
col4.plotly_chart(fig_duration)

st.markdown("""---""")
st.subheader("Raw Data")

#print all rows data
st.dataframe(df_emissions.iloc[:,1:].sort_values(by='datetime',ascending=True))

#DOWNLOADS
st.markdown("""---""")

now = datetime.now().strftime("%Y%m%d-%H%M")


@st.cache
def convert_df(df):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return df.to_csv().encode('utf-8')
st.subheader("Downloads")

st.write("Download dataset in csv format")
st.download_button(label="Download", 
                    data = convert_df(df_emissions),
                    file_name=now+'-data_co2_ml.csv',
                    mime='text/csv'
                )