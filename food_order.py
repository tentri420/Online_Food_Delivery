import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import seaborn as sns
import psycopg2
import streamlit as st

# DB connection
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="food_delivery_db",
        user="postgres",
        password="AJV06",
        port="5432"
    )

# run_querry cmd:
def run_query(sql):
    conn=get_connection() # get connect to DB
    cur=conn.cursor()  # to get query get variable

    cur.execute(sql)  # run the query given
    result= cur.fetchone()[0] # fetch a single single row
    
    cur.close()
    conn.close()
    return result

# Read CSV file as dataframe:
df = pd.read_csv("food_del_clean_data_fea.csv")

##### SQL QUERIES ####
# CUSTOMER & ORDER ANALYSIS:

# Weekend vs Weekday:
def week_end_day():
    conn=get_connection()
    query="""SELECT City,Order_Day,Cuisine_Type,COUNT(Cuisine_Type) AS cuisine ,SUM(Final_Amount) AS Total_Amt,SUM(Pro_Mar_Per) AS Total_Profit FROM food_del_data 
            WHERE Order_Status='Delivered' 
            GROUP BY Order_Day,City,Cuisine_Type
            ORDER BY City DESC, Order_Day;"""
    df_week=pd.read_sql_query(query,conn)
# Tree Map:
    fig4=px.treemap(
                    df_week,
                    path=["order_day","city"],
                    values="total_profit",
                    color="total_profit",
                    color_continuous_scale="Viridis",
                    title="Order Day over City",
                    )
    st.plotly_chart(fig4,use_container_width=True)

# Stacked Bar:
    fig5=px.bar(df_week,
                x="order_day",y="cuisine",color="cuisine_type",
                barmode="stack",
                title="Week-End/Day Cuisine Demand")
    st.plotly_chart(fig5,use_container_width=True)
    
def sqlq_cust_ors():
    conn=get_connection()
    queries={
        "1.Top Spending Customer":"""WITH top_spend AS(
				                                        SELECT Customer_ID,City,SUM(Order_Value) AS ORDER_RATE FROM food_del_data 
				                                        GROUP BY Customer_ID,City
				                                        ORDER BY ORDER_RATE 
				                                        )
                                    SELECT DENSE_RANK() OVER(ORDER BY ORDER_RATE DESC) AS RANK,Customer_ID,City,ORDER_RATE
                                    FROM top_spend
                                    ORDER BY RANK;""",
        "2.Age vs Order":"SELECT Customer_Age, SUM(Order_Value) AS ORDER_RATE FROM food_del_data GROUP BY Customer_Age ORDER BY Customer_Age;",
        "3.Weekend vs Weekday":None
    }
    st.title("📦Analysis on Customer & Order")
    select_qry=st.selectbox("Select",list(queries.keys()))
    
    if select_qry == "3.Weekend vs Weekday":
        week_end_day()
    else:
        df=pd.read_sql(queries[select_qry],conn)
        st.dataframe(df)

# REVENUE & PROFIT:
# Monthly Revenue:
def mon_rev():
    conn=get_connection()
    df_mon=pd.read_sql_query("""SELECT
                                TO_CHAR(Order_Date, 'Month') AS Month_Name,
                                TO_CHAR(SUM(Final_Amount),'FM99,99,99,999') AS Monthly_Revenue
                               FROM food_del_data
                               WHERE Order_Status='Delivered'
                               GROUP BY
                                 DATE_TRUNC('month', Order_Date),
                                 TO_CHAR(Order_Date, 'Month')
                                 ORDER BY DATE_TRUNC('month', Order_Date);""",conn)
    # Line Chart:
    fig6=px.line(df_mon,
                 x='month_name',y='monthly_revenue',
                 title='Monthly Revenue',
                 color_discrete_sequence=['teal'],
                 labels={'month_name':'Month',
                         'monthly_revenue':'Revenue'})
    st.plotly_chart(fig6,use_container_width=True)
def disc_pro():
    conn=get_connection()
    df_disc=pd.read_sql_query("""SELECT Restaurant_Name,SUM(Order_Value) AS Order_Rate,Discount_Applied,
		                                    SUM(Final_Amount) AS Tot_Amt,
		                                    ROUND(
                                                SUM(Profit_Margin) * 100.0
                                                / NULLIF(SUM(SUM(Profit_Margin)) OVER (), 0),2 ) AS Profit
                                            FROM food_del_data
                                            WHERE Order_Status='Delivered'
                                            GROUP BY Restaurant_Name,Discount_Applied
                                            ORDER BY Restaurant_Name asc,Discount_Applied;""",conn)
    #Filter:
    st.markdown("<p style='font-size:24px; font-weight:bold; color:blue;'>Restaurant Name</p>",unsafe_allow_html=True)

    res=st.multiselect("RES",["All"]+sorted(df_disc['restaurant_name'].dropna().unique().tolist()), label_visibility="collapsed")

    if res:
            df_disc = df_disc[df_disc['restaurant_name'].isin(res)]
            st.dataframe(df_disc)

def sqlq_rev_pro():
    conn=get_connection()
    queries={
        "1.Monthly Revenue":None,
        "2.Impact of Discount on Profit":None,
        "3.High Revenue City and Cuisine":"""WITH Revenue AS
                                                    (SELECT City,Cuisine_Type,
       	                                                SUM (Final_Amount) AS revenue
		                                                FROM food_del_data
		                                                WHERE Order_Status='Delivered'
		                                                GROUP BY City,Cuisine_Type
		                                                ORDER BY City
                                                      )
                                                    SELECT DENSE_RANK() OVER(ORDER BY Revenue.revenue DESC) AS RANK,City,Cuisine_Type,Revenue.revenue
                                                    FROM Revenue
                                                    ORDER BY RANK;"""
    }
    st.title("📊 Analysis on Revenue & Profit")
    select_qry=st.selectbox("Select",list(queries.keys()))
    if select_qry == "1.Monthly Revenue":
        mon_rev()
    elif select_qry == "2.Impact of Discount on Profit":
        disc_pro()
    else:
        df=pd.read_sql(queries[select_qry],conn)
        st.dataframe(df)

# DELIVERY PERFORMANCE:
#Distance vs Delivery Delay:
def dist_tdelay():
    conn=get_connection()
    df_delay=pd.read_sql_query("""SELECT City,Distance_Range,COUNT(*) AS Total_Orders,
                                                ROUND(AVG(EXTRACT(EPOCH FROM Delivery_Time_Min) / 60.0),2) AS Avg_Delivery_Minutes
                                            FROM food_del_data
                                            WHERE Order_Status = 'Delivered'
                                            GROUP BY City,Distance_Range
                                            ORDER BY Distance_Range ASC;""",conn)
# Scatter Chart:
    fig7=px.scatter(df_delay,
                    x='distance_range',y='avg_delivery_minutes', title='Distance vs Delivery Time',
                    color='distance_range')
    st.plotly_chart(fig7,use_container_width=True) 

# Delivery Rating vs Delivery Time:
def del_rate():
    conn=get_connection()
    df_rate=pd.read_sql_query("""SELECT Delivery_Rating,Distance_Range,
                                                ROUND(AVG(EXTRACT(EPOCH FROM Delivery_Time_Min) / 60.0),2) AS Avg_Delivery_Minutes
                                                FROM food_del_data
                                                WHERE Order_Status = 'Delivered'
                                                GROUP BY Delivery_Rating,Distance_Range;""",conn)
# Line Chart:
    fig8=px.line_3d(df_rate,
                    x='avg_delivery_minutes', y='delivery_rating', z='distance_range',
                    title=' Delivery - Rate vs Time',color='delivery_rating')
    st.plotly_chart(fig8,use_container_width=True) 

def sqlq_del_perf():
    conn=get_connection()
    queries={
        "1.Average Delivery Time by City":""" SELECT City, DATE_TRUNC('seconds',AVG(Delivery_Time_Min)) AS avg_del_time FROM food_del_data
                                                WHERE Order_Status='Delivered'
                                                GROUP BY City
                                                ORDER BY avg_del_time DESC;""",
        "2.Distance vs Delivery Delay":None,
        "3.Delivery Rating vs Delivery Time":None
    }
    st.title("⭐🛍️ Analysis on Delivery Performance")
    select_qry=st.selectbox("Select",list(queries.keys()))
    if select_qry == "2.Distance vs Delivery Delay":
        dist_tdelay()
    elif select_qry == "3.Delivery Rating vs Delivery Time":
        del_rate()
    else:
        df=pd.read_sql(queries[select_qry],conn)
        st.dataframe(df)

# RESTAURENT PERFORMANCE:
# Cuisine-wise Performance:
def cui_perf():
    conn=get_connection()
    df_perf=pd.read_sql_query("""SELECT City,Cuisine_Type,Discount_Applied,ROUND(AVG(Discount_Applied),2) AS avg_disc,
                                            ROUND(AVG(Final_Amount),2) AS avg_amt
                                            FROM food_del_data
                                            WHERE Order_Status = 'Delivered'
                                            GROUP BY City,Cuisine_Type,Discount_Applied
                                            ORDER BY City,Cuisine_Type;""",conn)
    # BAR CHART:
    fig9=px.bar(df_perf,
                x='cuisine_type',y='avg_amt',color='discount_applied',
                title='Cuisinewise Performance')
    st.plotly_chart(fig9,use_container_width=True)
def sqlq_res_perf():
    conn=get_connection()
    queries={
        "1.Top-related Restaurent":"""WITH Res_Rat AS(
                                                SELECT Restaurant_Name , ROUND(AVG(Restaurant_Rating),2) AS avg_res_rat
			                                    FROM food_del_data
			                                    WHERE Order_Status = 'Delivered'
			                                    GROUP BY Restaurant_Name
			                                    )
                                        SELECT DENSE_RANK() OVER(ORDER BY avg_res_rat DESC) AS RANK,Restaurant_Name,avg_res_rat
                                        FROM Res_Rat
                                        ORDER BY RANK;""",
        "2.Cancellation Rate by Restaurent":"""WITH tot_order AS (
                                                                SELECT Restaurant_Name, COUNT(*) AS Total_Orders,
                                                                COUNT(*) FILTER (WHERE Order_Status = 'Cancelled') AS Cancelled_Orders
                                                                FROM food_del_data
                                                                GROUP BY Restaurant_Name)
                                                SELECT Restaurant_Name, Total_Orders, Cancelled_Orders,
                                                ROUND(Cancelled_Orders * 100.0 / NULLIF(Total_Orders, 0),2) AS Cancellation_Rate
                                                FROM tot_order
                                                ORDER BY Cancellation_Rate DESC;""",
        "3.Cuisine-wise Performance":None
    }
    st.title("⭐🥡 Analysis on Restaurent Performance")
    select_qry=st.selectbox("Select",list(queries.keys()))
    if select_qry == "3.Cuisine-wise Performance":
        cui_perf()
    else:
        df=pd.read_sql(queries[select_qry],conn)
        st.dataframe(df)

# INSIGHTS:
# Payment Mode Pref:
def payment():
    conn=get_connection()
    df_payment=pd.read_sql_query("""SELECT Payment_Mode, COUNT(*) AS Tot_Order,
                                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),2) AS Payment_Rate
                                    FROM food_del_data
                                    WHERE Order_Status = 'Delivered'
                                    GROUP BY Payment_Mode
                                    ORDER BY Payment_Rate DESC;""",conn)
   # PIE CHART:
    fig10=px.pie(df_payment,
                 names='payment_mode', values='payment_rate',
                 title='Payment Mode Preference') 
    fig10.update_traces(textinfo="label+value+percent")
    st.plotly_chart(fig10,use_container_width=True)

#Peak Hour Demand Analysis:

def peak_ana():
    conn=get_connection()
    df_peak=pd.read_sql_query("""SELECT City,Restaurant_Name,Order_Day, COUNT(*) AS Tot_Ord
                                            FROM food_del_data
                                            WHERE Order_Status = 'Delivered' AND Peak_Hour IS True
                                            GROUP BY City,Restaurant_Name,Order_Day
                                            ORDER BY City,Order_Day;""",conn)

#Filter by CITY & RES-NAME:
    col1,col2 =st.columns(2)
    with col1:
        st.markdown("<p style='font-size:24px; font-weight:bold; color:red;'>City</p>",unsafe_allow_html=True)
    
        city=st.multiselect("RES",["All"]+sorted(df_peak['city'].dropna().unique().tolist()), label_visibility="collapsed")

    with col2:
        st.markdown("<p style='font-size:24px; font-weight:bold; color:blue;'>Restaurant Name</p>",unsafe_allow_html=True)
            
        res=st.multiselect("RES",["All"]+sorted(df_peak['restaurant_name'].dropna().unique().tolist()), label_visibility="collapsed")

    if city:
            df_peak = df_peak[df_peak['city'].isin(city)]    
    if res:
        df_peak = df_peak[df_peak['restaurant_name'].isin(res)]
        st.dataframe(df_peak)
        
def sqlq_insights():
    conn=get_connection()
    queries={
        "1.Peak Hour Demand Analysis":None,
        "2.Payment Mode Pref":None,
        "3.Cancellation Reason Analysis":"""SELECT Cancellation_Reason,COUNT(Cancellation_Reason) AS Total FROM food_del_data
                                            WHERE Order_Status = 'Cancelled'
                                            GROUP BY Cancellation_Reason
                                            ORDER BY Cancellation_Reason;"""
    }
    st.title("🚴‍♂️Insights on Food  Delivery System🛵🍔")
    select_qry=st.selectbox("Select",list(queries.keys()))
    if select_qry == "1.Peak Hour Demand Analysis":
        peak_ana()
    elif select_qry == "2.Payment Mode Pref":
        payment()
    else:
        df=pd.read_sql(queries[select_qry],conn)
        st.dataframe(df)

   
# SELECT ANALYSIS: (Content that to be displayed in the main DASHBOARD)
def sel_ana():
    conn=get_connection()
    df=pd.read_sql_query("SELECT * FROM food_del_data ORDER BY City;",conn)

# Filter:
    col1,col2,col3 =st.columns(3)
    with col1:
        k_city=st.selectbox("**City**",["All"]+sorted(df['city'].dropna().unique().tolist()))
    with col2:
        k_area=st.selectbox("Area",["All"]+sorted(df['area'].dropna().unique().tolist()))
    with col3:
        k_day=st.selectbox("Day Status",["All"]+sorted(df['order_day'].dropna().unique().tolist()))

    filtered_df=df.copy()

    if k_city != "All":
        filtered_df = filtered_df[filtered_df['city'] == k_city]
    if k_area != "All":
        filtered_df = filtered_df[filtered_df['area'] == k_area]
    if k_day != "All":
        filtered_df = filtered_df[filtered_df['order_day'] == k_day]
    #st.dataframe(filtered_df) 
    st.write("***********")

# Metrics update with the filters:
    col1,col2,col3 =st.columns(3)
    with col1:
        st.metric("Orders🍱", f"{len(filtered_df):,}")
    with col2:
        st.metric("Order Value🧾", f"{filtered_df['order_value'].mean():,.2f}")
    with col3:
        st.metric("Revenue💰",f"{filtered_df['final_amount'].sum():,.2f}")
    st.write("***********")

# Metric related with Delivery:
    col1,col2 = st.columns(2)
    with col1:
        st.metric("🕒 Delivery Time",f"{filtered_df['delivery_time'].mean().strftime("%I:%M:%S")}")
        #st.metric("🕒 Current Time", datetime.now().strftime("%I:%M:%S %p"))
    with col2:
        st.metric("Delivery Rating ⭐",f"{filtered_df['delivery_rating'].mean():,.2f}")

# Cancellation_Reason Chart Performance:(DONUT)
    df_group1=(filtered_df.groupby(['cancellation_reason']).size().reset_index(name='count'))
    df_group1["cancellation_rate"]=((df_group1['count']/df_group1['count'].sum())*100)
    df_group1["cancellation_rate"]=df_group1["cancellation_rate"].round(2)
    st.markdown("<h3 style='color:green; font-family:Georgia; text-align:center;'>Cancellation Rate</h3>",
                   unsafe_allow_html=True)
    
    fig1= px.pie(df_group1,
                        names="cancellation_reason",
                        values="cancellation_rate",
                        hole=0.5,
                        )
    fig1.update_traces(textinfo="label+value")
    st.plotly_chart(fig1,use_container_width=True)

# Profit MARGIN:(BUBBLE)
    df_group2=(filtered_df.groupby(['city','area'])['pro_mar_per'].sum().round(2).reset_index(name='profit'))
    st.markdown("<h3 style='color:red; font-family:Georgia; text-align:center;'>Profit Analysis</h3>",
                      unsafe_allow_html=True)
    fig2=px.scatter(df_group2,
                     x="city",y="profit",
                     size='profit',
                     color='area'
                    )
    st.plotly_chart(fig2,use_container_width=True)

#ORDER STATUS- PERF:
    df_group3 = (filtered_df.groupby(["city", "order_status"])["order_value"].sum().reset_index())
    st.markdown("<h3 style='color:orange; font-family:Georgia; text-align:center;'>Order Value by City and Order Status</h3>",
                          unsafe_allow_html=True)
    fig3 = px.bar(df_group3,
                    x="city", y="order_value", color="order_status",
                    barmode="group"
                )
    st.plotly_chart(fig3, use_container_width=True)


# DASHBOARD:
# DASH - TITLE:
st.markdown("<h2 style='color:blue; font-family:Georgia; text-align:left;'>🛵🍕Food Delivery Dashboard</h2>",
                   unsafe_allow_html=True )

# SIDE BAR DASHBOARD: To SELECT Anslysis

st.sidebar.markdown(
    "<h1 style='color:red; font-family:Arial; font-align:left; font-weight: bold; font-style: italic;'>""Welcome!""</h1>",
    unsafe_allow_html=True
)
st.sidebar.write("🍱 Food Order & Delivery Insights 📈")
report=["[SELECT ANALYSIS]","Customer and Order","Revenue & Profit","Delivery Performance","Restaurent Performance","Operational Insights"]
rep= st.sidebar.selectbox ("**Show Analysis Report for:**",report)

if rep == "[SELECT ANALYSIS]":
    sel_ana()
elif rep =="Customer and Order":
    sqlq_cust_ors()
elif rep == "Revenue & Profit":
    sqlq_rev_pro()
elif rep =="Delivery Performance":
    sqlq_del_perf()
elif rep == "Restaurent Performance":
    sqlq_res_perf()
else:
    sqlq_insights()
