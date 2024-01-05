import os
from dotenv import load_dotenv
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import requests
from sqlmodel import SQLModel, Session, create_engine, select, Field
import calculate_margin_curve

load_dotenv()

backend_url = os.getenv("BACKEND_URL") or os.environ["BACKEND_URL"]
connectionString = os.getenv("CONNECTION_STRING") or os.environ["CONNECTION_STRING"]

# Create an engine instance
engine = create_engine(os.getenv("CONNECTION_STRING"))

# set encoding to latin1
engine.connect().connection.setencoding('latin1')

# Function to create all tables if they do not exist
def create_tables():
    SQLModel.metadata.create_all(engine)
    with get_session() as session:
        session.commit()

# Database connection context manager
def get_session():
    return Session(engine)

# Retrieve data from database
def clear_session():
    SQLModel.metadata.clear()

@st.cache_data()
def fetch_price_data():
    with get_session() as session:
        statement = select(PriceData)
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])


def fetch_calculation_data():
    with get_session() as session:
        statement = select(CalculationData)
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])
    

# Fetch margin configuration from database
def fetch_margin_configuration():
    with get_session() as session:
        statement = select(MarginConfiguration)
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])

# Fetch data from database
def fetch_data(table_name):
    with get_session() as session:
        statement = select(eval(table_name))
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])


# Update or insert calculation results
def update_calculation_results(category, margin_curve_a, margin_curve_b, avg_elasticity):    
    data = CalculationData(
        category=category,
        margin_curveA=margin_curve_a,
        margin_curveB=margin_curve_b,
        average_elasticity=avg_elasticity
    )
    return data

# Update margin configuration
def update_margin_configuration(min_margin, max_margin):
    with get_session() as session:
        data = MarginConfiguration(
            id=1,
            key="margin",
            value=min_margin
        )
        session.add(data)
        session.commit()
        data = MarginConfiguration(
            id=2,
            key="max_margin",
            value=max_margin
        )
        session.add(data)
        session.commit()


# clear all stremlit cache
st.cache(allow_output_mutation=True)

# Define SQLModel classes for your tables
class CalculationData(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(primary_key=True)
    category: str  = Field(nullable=True)
    margin_curveA: float = Field(nullable=True)
    margin_curveB: float = Field(nullable=True)
    ci_a_lower: float = Field(nullable=True)
    ci_a_upper: float = Field(nullable=True)
    ci_b_lower: float = Field(nullable=True)
    ci_b_upper: float = Field(nullable=True)
    average_elasticity: float = Field(nullable=True)

class MarginConfiguration(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(primary_key=True)
    key: str
    value: float

class PriceData(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(primary_key=True)
    country_code: str
    category: str
    item_code: str
    date: str
    qty: int
    cogs: float
    sell_price: float

# Create an engine instance
engine = create_engine("mssql+pyodbc://skruvat:^z4jj$w5JudEE19%@cloudservicedb.database.windows.net:1433/cloud2?driver=ODBC+Driver+17+for+SQL+Server")

# set encoding to latin1
engine.connect().connection.setencoding('latin1')

# Function to create all tables if they do not exist
def create_tables():
    SQLModel.metadata.create_all(engine)
    with get_session() as session:
        session.commit()

# Database connection context manager
def get_session():
    return Session(engine)

# Retrieve data from database
def clear_session():
    SQLModel.metadata.clear()

@st.cache_data()
def fetch_price_data():
    with get_session() as session:
        statement = select(PriceData)
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])


def fetch_calculation_data():
    with get_session() as session:
        statement = select(CalculationData)
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])
    

# Fetch margin configuration from database
def fetch_margin_configuration():
    with get_session() as session:
        statement = select(MarginConfiguration)
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])

# Fetch data from database
def fetch_data(table_name):
    with get_session() as session:
        statement = select(eval(table_name))
        results = session.exec(statement).all()
        return pd.DataFrame([result.model_dump() for result in results])


# Update or insert calculation results
def update_calculation_results(category, margin_curve_a, margin_curve_b, avg_elasticity):    
    data = CalculationData(
        category=category,
        margin_curveA=margin_curve_a,
        margin_curveB=margin_curve_b,
        average_elasticity=avg_elasticity
    )
    return data

# Update margin configuration
def update_margin_configuration(min_margin, max_margin):
    with get_session() as session:
        data = MarginConfiguration(
            id=1,
            key='min_margin',
            value=min_margin
        )
        session.merge(data)
        data = MarginConfiguration(
            id=2,
            key='max_margin',
            value=max_margin
        )
        session.merge(data)
        session.commit()
        st.success('Data successfully updated in the database!')

# Clear existing data and insert new data
def replace_data(df):
    with get_session() as session:
        statement = select(PriceData).where(PriceData.id > 0)
        results = session.exec(statement)
        price_data = results.first()
        
        if price_data:
            session.delete(price_data)
            session.commit()
        
        for idx, row in df.iterrows():
            data = PriceData(
                country_code=row['country_code'],
                category=row['category'],
                item_code=row['item_code'],
                date=row['date'],
                qty=row['qty'],
                cogs=row['cogs'],
                sell_price=row['sell_price']
            )
            session.add(data)
        session.commit()        
        st.success('Data successfully updated in the database!')

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# clear_session()
# create_tables()

st.set_page_config(layout="wide")
st.sidebar.title('Navigation')
page = st.sidebar.selectbox('Choose a page:', ['View Margin Curve Data', 'View Price Data', 'Upload Base Data', 'Price Tools Upload XLS'])

if page == 'Upload Base Data':
    st.title('Upload Base Data')
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type="csv")
    
    if st.button('create_tables'):
        create_tables()
        st.success('Tables successfully created in the database!')
    
    if st.button('clear_session'):
        clear_session()
        st.success('Session successfully cleared!')
    
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file, sep=';')
        st.success(f'Successfully Uploaded {len(data)} rows')
        st.write(data.head(5))
        
        # before click upload and calculate I want user to be able to map the csv with the correct column in the database
        st.write('Map the csv with the correct column in the database')
        
        col1,col2,col3,col4 = st.columns([1,1,1,1])
        country_code = col1.selectbox('Country Code', data.columns)
        category = col2.selectbox('Category', data.columns)
        item_code = col3.selectbox('Item Code', data.columns)
        date = col4.selectbox('Date', data.columns)
        qty = col1.selectbox('Qty', data.columns)
        cogs = col2.selectbox('Cogs/unit', data.columns)
        sell_price = col3.selectbox('Sell price/unit', data.columns)
        
        if st.button('Upload and calculate'):
            # remap dataframe according to column mapping
            df = data[[country_code, category, item_code, date, qty, cogs, sell_price]]
            df.columns = ['country_code', 'category', 'item_code', 'date', 'qty', 'cogs', 'sell_price']
            # replace data in price_data table
            # replace_data(df)
            # calculate margin curve
            df_calculation_data = calculate_margin_curve(df)
            st.dataframe(df_calculation_data, use_container_width=True)
            
            # clean data remove nan value
            clean_df = df_calculation_data.dropna()
            st.dataframe(df_calculation_data, use_container_width=True)
            # update calculation results in database
            with get_session() as session:
                for idx, row in clean_df.iterrows():
                    data = update_calculation_results(
                        category=row['category'],
                        margin_curve_a=row['margin_curve_a'],
                        margin_curve_b=row['margin_curve_b'],
                        avg_elasticity=row['avg_elasticity']
                    )
                    session.merge(data)
                session.commit()
                st.success('Data successfully updated in the database!')

elif page == 'View Price Data':
    st.title('View Price Data')
    # Get the data from the database
    df_price_data = fetch_price_data()
    
    st.text('Price Data')
    df_price_data = df_price_data[['country_code', 'category', 'item_code', 'date', 'qty', 'cogs', 'sell_price']]
    st.dataframe(df_price_data, use_container_width=True)

    @st.cache_data()
    def display_sell_qty_over_time(df_price_data):
        # get sell qty group by date from dataframe df_price_data
        df_sell_qty = df_price_data[['date', 'qty']]

        # group dataframe df_sell_qty by week
        df_sell_qty['date'] = pd.to_datetime(df_sell_qty['date'])
        df_sell_qty['date'] = df_sell_qty['date'].dt.strftime('%Y-%U')
        df_sell_qty = df_sell_qty.groupby('date').sum().reset_index()

        # Display the data    
        st.text('Sell Qty by overtime')
        st.bar_chart(df_sell_qty, x='date', y='qty')

    # Call the function
    display_sell_qty_over_time(df_price_data)

    # #  compare the time series of Sell price/unit and Cogs/unit over time to analyze margin changes
    @st.cache_data()
    def display_sell_price_and_cogs_by_week(df_price_data):
        margin_data = df_price_data[['date', 'sell_price', 'cogs']]

        margin_data['date'] = pd.to_datetime(margin_data['date'])
        margin_data['date'] = margin_data['date'].dt.strftime('%Y-%U')
        margin_data = margin_data.groupby('date').mean().reset_index()

        st.text('Sell price/unit and Cogs/unit by week')
        st.line_chart(margin_data, x='date', y=['sell_price', 'cogs'])

    # Call the function
    display_sell_price_and_cogs_by_week(df_price_data)

    @st.cache_data()
    def display_top_category_by_year(df_price_data):
        # get top 5 category by qty sales by year
        df_top_category = df_price_data[['category', 'qty', 'date']]

        df_top_category['date'] = pd.to_datetime(df_top_category['date'])
        df_top_category['date'] = df_top_category['date'].dt.strftime('%Y')
        df_top_category = df_top_category.groupby(['category', 'date']).sum().reset_index()
        df_top_category = df_top_category.sort_values(by=['qty', 'date'], ascending=False)
        df_top_category = df_top_category.groupby('date').head(10).reset_index()
        df_top_category = df_top_category.sort_values(by=['qty'], ascending=False)

        # change label 'date' to 'year'
        chart_data = df_top_category.rename(columns={'date': 'year'})

        # Display the data
        st.text('Top 10 Category by Qty Sales by Year')
        st.area_chart(chart_data, x='category', y='qty', color='year')

    # Call the function
    display_top_category_by_year(df_price_data)

elif page == 'View Margin Curve Data':
    # st.title('View Margin Curve Data')
    col1, col2 = st.columns([2,4])
    col3, col4 = st.columns([2,4])
    
    @st.cache_data()
    def get_calculation_data():
        calculation_data = fetch_calculation_data()
        return calculation_data
    
    df_calculation_data = get_calculation_data()
    
    col4.text('Margin Curve Calculation Data')
    col4.dataframe(df_calculation_data[['category', 'margin_curveA', 'margin_curveB', 'average_elasticity']], use_container_width=True)
    
    st.sidebar.title('Margin Configuration')
    min_margin = st.sidebar.slider('Margin Bruto Min', 0.0, 1.0, 0.06)
    max_margin = st.sidebar.slider('Margin Bruto Max', 0.0, 1.0, 0.20)
    
    categories = df_calculation_data['category'].unique()
    selected_category = st.sidebar.selectbox('category', categories)
    
    item_code_input = st.sidebar.text_input('Item Code', '')
    cogs_input = st.sidebar.number_input('Cogs', format='%f')
    
    inputs = [{"category": selected_category, "item_code": item_code_input, "cogs": cogs_input}]

    if cogs_input:
        #convertion the input into json format
        res = requests.post(url = backend_url + "price_suggestion?confident=default", data = json.dumps(inputs))
        # st.write(res.text)
        # get suggested price from res
        suggested_price = json.loads(res.text)[0]['suggested_price']
        
        st.sidebar.subheader(f"Response from API = {suggested_price}")
            
    
    if selected_category:
        category_data = df_calculation_data[df_calculation_data['category'] == selected_category]
        # add value of Margin bruto in dataframe
        category_data['MarginB Min'] = min_margin
        category_data['MarginB Max'] = max_margin
        
        category_data['margin_curveA'] = category_data['margin_curveA'].round(4)
        category_data['margin_curveB'] = category_data['margin_curveB'].round(4)
        category_data['average_elasticity'] = category_data['average_elasticity'].round(4)
        
        category_data = category_data[['category', 'margin_curveA', 'margin_curveB', 'average_elasticity', 'MarginB Min', 'MarginB Max']]
        
        col3.text_input('category', selected_category, disabled=True)
        col3.dataframe(category_data.T, use_container_width=True)
        
        df_price_data = fetch_price_data()
        
        df_price_data = df_price_data[df_price_data['category'] == selected_category]
        df_price_data['cogs'].round(2)
        df_price_data = df_price_data[['cogs', 'sell_price', 'country_code']]        
        
        # group dataframe by cogs and get count of cogs and sell_price
        df_price_data = df_price_data.groupby(['cogs', 'sell_price']).count().reset_index()
        df_price_data = df_price_data.rename(columns={'country_code': 'count'})
                
        margin_curve_a = category_data['margin_curveA'].iloc[0]
        margin_curve_b = category_data['margin_curveB'].iloc[0]
        
        df_price_data['price_suggestion'] = round(margin_curve_a * (df_price_data['cogs'] ** margin_curve_b), 2)
        df_price_data['Margin Bruto'] = round((df_price_data['price_suggestion'] - df_price_data['cogs']) / df_price_data['price_suggestion'], 2)
        df_price_data['price_from_mb_min'] = round(df_price_data['cogs'] / (1 - min_margin), 2)
        df_price_data['price_from_mb_max'] = round(df_price_data['cogs'] / (1 - max_margin), 2)
        df_price_data['price_suggestion'] = df_price_data.apply(
            lambda x: x['price_from_mb_min'] if x['price_suggestion'] < x['price_from_mb_min'] 
            else x['price_from_mb_max'] if x['price_suggestion'] > x['price_from_mb_max'] 
            else x['price_suggestion'], axis=1)
        
        col2.text('Price Suggestion Data')
        col2.dataframe(df_price_data, use_container_width=True)

        plt.rcParams["figure.figsize"] = (8, 6)
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(df_price_data['cogs'], df_price_data['Margin Bruto'], 'r-')
        ax1.set_ylim(0, 1)  # Set the y-axis limits to 0 and 1
        ax2.plot(df_price_data['cogs'], df_price_data['price_suggestion'], 'b-')
        ax2.set_ylim(0, 5000)
        ax1.set_xlabel('cogs')
        ax1.set_ylabel('Margin Bruto')
        ax2.set_ylabel('Price Suggestion')
        
        col1.text('Margin Bruto and Price Suggestion Chart')
        col1.pyplot(fig)

elif page == 'Price Tools Upload XLS':
    st.title('Price Tools Upload XLS')
    price_uploaded_file = st.sidebar.file_uploader("Upload File", type=["xls", "csv"])
    
    if price_uploaded_file is not None:
        if price_uploaded_file.name.endswith('.xls'):
            data = pd.read_excel(price_uploaded_file)
        elif price_uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(price_uploaded_file)
        else:
            st.error("Invalid file format. Please upload a valid XLS or CSV file.")
        
        st.success(f'Successfully Uploaded {len(data)} rows')
        
        # Map the data to the correct column name (category, item_code, cogs)
        category = st.sidebar.selectbox('Category', data.columns)
        item_code = st.sidebar.selectbox('Item Code', data.columns)
        cogs = st.sidebar.selectbox('Cogs', data.columns)
        
        # Remap data according to column mapping
        data = data[[category, item_code, cogs]]
        data[item_code] = data[item_code].astype(str)
        
        # change column header to category, item_code, cogs
        data.columns = ['category', 'item_code', 'cogs']
        
        # Create a request to the API and get the response
        inputs = data.to_dict('records')
        # st.write(inputs)
        create_request = st.sidebar.button('Create Request')

        if create_request:
            res = requests.post(url=backend_url + "price_suggestion?confident=default", data=json.dumps(inputs))
            suggested_price = json.loads(res.text)
            
            suggested_price = pd.DataFrame(suggested_price).get('suggested_price')
            
            data['suggested_price'] = suggested_price
            st.write(data)
            
            df_xlsx = to_excel(pd.DataFrame(data))
            st.download_button(label='📥 Download Current Result', data=df_xlsx, file_name='pricelist_with_suggestion.xlsx')
