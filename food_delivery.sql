-- Server Name: online_delivery
-- DB name: food_delivery_db
-- Table Name:food_del_data (Imported file:food_del_clean_data_fea.csv )
CREATE TABLE food_del_data(
				Order_ID VARCHAR(20) PRIMARY KEY, 
				Customer_ID VARCHAR(20) NOT NULL,  
				Customer_Age INTEGER NOT NULL, 
				Customer_Gender VARCHAR(10) NOT NULL, 
				City VARCHAR(15) NOT NULL,
                Area VARCHAR(10) NOT NULL, 
				Restaurant_ID VARCHAR(20) NOT NULL, 
				Restaurant_Name VARCHAR(25) NOT NULL, 
				Cuisine_Type VARCHAR(15) NOT NULL,
                Order_Date DATE NOT NULL, 
	            Delivery_Time_Min INTERVAL, 
				Distance_km DECIMAL(6,2) NOT NULL, 
				Order_Value DECIMAL(6,2) NOT NULL,
                Discount_Applied DECIMAL(5,2) NOT NULL, 
				Final_Amount DECIMAL(6,2) NOT NULL, 
				Payment_Mode VARCHAR(10) NOT NULL, 
				Order_Status VARCHAR(15) NOT NULL,
                Cancellation_Reason VARCHAR(25) NOT NULL, 
				Delivery_Partner_ID VARCHAR(20) NOT NULL,
				Delivery_Rating DECIMAL(2,1) NOT NULL,
                Restaurant_Rating DECIMAL(2,1) NOT NULL,
				Order_Day VARCHAR(10) NOT NULL, 
				Peak_Hour BOOLEAN, 
				Profit_Margin DECIMAL(4,2) NOT NULL,
                Delivery_Time TIMESTAMP NOT NULL,
				Discount_Match BOOLEAN,
				Delivery_Minutes INTEGER NOT NULL, 
				Distance_Range VARCHAR(15) NOT NULL,
				Pro_Mar_Per DECIMAL(5,2) NOT NULL,
                Del_Perf VARCHAR(15) NOT NULL,
				Cust_Age_Group VARCHAR(15) NOT NULL			
);

SELECT * FROM food_del_data;

-- To DROP the Table:
DROP TABLE food_del_data;

-- To Check table get inserted or not:

SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_name = 'food_del_data';

--To check rows get inserted:
SELECT COUNT(*)
FROM public.food_del_data;

-- SQL QUERIES---
--1.CUSTOMER & ORDER ANALYSIS:
--1.1 Top Spending Customer:
WITH top_spend AS(
				SELECT Customer_ID,City,SUM(Order_Value) AS ORDER_RATE FROM food_del_data 
				GROUP BY Customer_ID,City
				ORDER BY ORDER_RATE 
				)
SELECT DENSE_RANK() OVER(ORDER BY ORDER_RATE DESC) AS RANK,Customer_ID,City,ORDER_RATE
FROM top_spend
ORDER BY RANK;


--1.2 Analyze age group vs order value :

SELECT Customer_Age, SUM(Order_Value) AS ORDER_RATE FROM food_del_data
GROUP BY Customer_Age
ORDER BY Customer_Age;

--1.3 Weekend vs weekday order patterns:

SELECT City,Order_Day,Cuisine_Type,SUM(Final_Amount) AS Total_Amt,SUM(Pro_Mar_Per) AS Total_Profit 
FROM food_del_data 
WHERE Order_Status='Delivered'
GROUP BY Order_Day,City,Cuisine_Type
ORDER BY City DESC,
         Cuisine_Type DESC,
		 Order_Day;

--2.REVENUE & PROFIT:
--2.1  Monthly revenue trends 
SELECT
    TO_CHAR(Order_Date, 'Month') AS Month_Name,
    TO_CHAR(SUM(Final_Amount),'FM99,99,99,999') AS Monthly_Revenue
FROM food_del_data
WHERE Order_Status='Delivered'
GROUP BY
    DATE_TRUNC('month', Order_Date),
    TO_CHAR(Order_Date, 'Month')
ORDER BY DATE_TRUNC('month', Order_Date);

--2.2 Impact of discounts on profit:
SELECT
    Discount_Applied,
    COUNT(*) AS Total_Orders,
    SUM(Order_Value) AS Revenue_Before_Discount,
    SUM(Final_Amount) AS Revenue_After_Discount,
    SUM(Order_Value) - SUM(Final_Amount) AS Total_Discount,
    ROUND(AVG(Profit_Margin) * 100, 2) AS Avg_Profit_Margin_Percentage
FROM food_del_data
WHERE Order_Status = 'Delivered'
GROUP BY Discount_Applied
ORDER BY Discount_Applied;

--2.3 High-revenue cities and cuisines:

WITH Revenue AS
      (SELECT City,Cuisine_Type,
       	SUM (Final_Amount) AS revenue
		FROM food_del_data
		WHERE Order_Status='Delivered'
		GROUP BY City,Cuisine_Type
		ORDER BY City)
SELECT DENSE_RANK() OVER(ORDER BY Revenue.revenue DESC) AS RANK,City,Cuisine_Type,Revenue.revenue
FROM Revenue
ORDER BY RANK;

--3.Delivery Performance :
--3.1 Average delivery time by city:

SELECT City, DATE_TRUNC('seconds',AVG(Delivery_Time_Min)) AS avg_del_time FROM food_del_data
WHERE Order_Status='Delivered'
GROUP BY City
ORDER BY avg_del_time DESC;

--3.2 Distance vs delivery delay analysis 

SELECT City,Distance_Range,COUNT(*) AS Total_Orders,
    ROUND(
        AVG(EXTRACT(EPOCH FROM Delivery_Time_Min) / 60.0),
        2
    ) AS Avg_Delivery_Minutes
FROM food_del_data
WHERE Order_Status = 'Delivered'
GROUP BY City,Distance_Range
ORDER BY Distance_Range ASC;

--3.3 Delivery rating vs delivery time:
SELECT Delivery_Rating,
    ROUND(
        AVG(EXTRACT(EPOCH FROM Delivery_Time_Min) / 60.0),
        2
    ) AS Avg_Delivery_Minutes
FROM food_del_data
WHERE Order_Status = 'Delivered'
GROUP BY Delivery_Rating;

--4.Restaurant Performance 
--4.1 Top Rated Restaurant:

WITH Res_Rat AS(
            SELECT Restaurant_Name , ROUND(AVG(Restaurant_Rating),2) AS avg_res_rat
			FROM food_del_data
			WHERE Order_Status = 'Delivered'
			GROUP BY Restaurant_Name
			)
SELECT DENSE_RANK() OVER(ORDER BY avg_res_rat DESC) AS RANK,Restaurant_Name,avg_res_rat
FROM Res_Rat
ORDER BY RANK;

--4.2 Cancellation rate by restaurant:

WITH tot_order AS (
    SELECT
        Restaurant_Name,
        COUNT(*) AS Total_Orders,
        COUNT(*) FILTER (
            WHERE Order_Status = 'Cancelled'
        ) AS Cancelled_Orders
    FROM food_del_data
    GROUP BY Restaurant_Name
)
SELECT
    Restaurant_Name,
    Total_Orders,
    Cancelled_Orders,
    ROUND(
        Cancelled_Orders * 100.0 / NULLIF(Total_Orders, 0),
        2
    ) AS Cancellation_Rate
FROM tot_order
ORDER BY Cancellation_Rate DESC;

--4.3 12. Cuisine-wise performance:

SELECT City,Cuisine_Type,ROUND(AVG(Discount_Applied),2) AS avg_disc,ROUND(AVG(Final_Amount),2) AS avg_amt
FROM food_del_data
WHERE Order_Status = 'Delivered'
GROUP BY City,Cuisine_Type
ORDER BY City,Cuisine_Type;


--5. Operational Insights 
--5.1 Peak hour demand analysis 
SELECT City,Restaurant_Name,Order_Day, COUNT(*) AS Tot_Ord
FROM food_del_data
WHERE Order_Status = 'Delivered' AND Peak_Hour IS True
GROUP BY City,Restaurant_Name,Order_Day
ORDER BY City,Order_Day;

--5.2 Payment mode preferences ,Cust_Age_Group

SELECT
    Payment_Mode,
    COUNT(*) AS Tot_Order,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS Payment_Rate
FROM food_del_data
WHERE Order_Status = 'Delivered'
GROUP BY Payment_Mode
ORDER BY Payment_Rate DESC;

--5.3 Cancellation reason analysis :

SELECT Cancellation_Reason,COUNT(Cancellation_Reason) AS Total FROM food_del_data
WHERE Order_Status = 'Cancelled'
GROUP BY Cancellation_Reason
ORDER BY Cancellation_Reason;
--Exttra
--Peak hour demand analysis based on city:
SELECT
    City,
    COUNT(*) AS Peak_Hour_Orders
FROM food_del_data
WHERE Peak_Hour = TRUE
GROUP BY City
ORDER BY Peak_Hour_Orders DESC;

-- PERF: Cancellation Rate:

SELECT Cancellation_Reason,
	COUNT(*) AS Total_Order,
	ROUND(
		COUNT(*) *100/SUM(COUNT(*)) OVER (),
        2) AS Cancellation_Rate
FROM food_del_data
WHERE Order_Status = 'Cancelled'
GROUP BY Cancellation_Reason
ORDER BY Cancellation_Reason;

-- PERF: PROFIT MARGIN
