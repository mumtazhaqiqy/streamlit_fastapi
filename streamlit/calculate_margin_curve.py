import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import t

# Function to calculate MarginCurve parameters and average price elasticity for each category
def calculate_margin_curve(dataframe, confidence=0.95):
    # Sort the data by item_code, category, and date
    dataframe.sort_values(by=['item_code', 'Category', 'date'], inplace=True)
    
    # Calculate the percentage changes within each item and category
    dataframe['PctChange_Qty'] = dataframe.groupby(['item_code', 'Category'])['qty'].pct_change()
    dataframe['PctChange_SellPrice'] = dataframe.groupby(['item_code', 'Category'])['Sell price/unit'].pct_change()
    
    # Calculate elasticity: (percentage change in quantity / percentage change in price)
    dataframe['Elasticity'] = dataframe['PctChange_Qty'] / dataframe['PctChange_SellPrice']
    
    # Handle infinity and NaN values
    dataframe.replace([np.inf, -np.inf], np.nan, inplace=True)
    dataframe.dropna(subset=['Elasticity'], inplace=True)
    
    # Define a power-law function for fitting the margin curve
    def power_law(x, a, b):
        return a * np.power(x, b)

    category_results_list = []
    for category in dataframe['Category'].unique():
        category_data = dataframe[dataframe['Category'] == category]
        
        # Ensure there are enough data points for curve fitting
        if len(category_data) < 3:
            # Streamlit uses st.error to display error messages in the app
            RuntimeError(f"Not enough data for curve fitting in category: {category}")
            continue
        
        # Fit the power-law function to the COGS and Sell Price data to find the parameters
        try:
            # Assuming initial guesses for A and B
            initial_guess = [1, 1]
            params, cov = curve_fit(
                power_law, 
                category_data['Cogs/unit'], 
                category_data['Sell price/unit'],
                p0=initial_guess,
                maxfev=10000  # Increase the number of function evaluations
            )
            MarginCurveA, MarginCurveB = params

            # Calculate confidence intervals
            perr = np.sqrt(np.diag(cov))
            tval = t.ppf(1.0 - (1 - confidence) / 2, len(category_data) - len(params))
            ci_a = (params[0] - perr[0] * tval, params[0] + perr[0] * tval)
            ci_b = (params[1] - perr[1] * tval, params[1] + perr[1] * tval)

        except Exception as e:
            RuntimeError(f"Curve fitting failed for {category} due to {e}")
            continue
        
        # Calculate average elasticity for the category
        mean_elasticity = category_data['Elasticity'].mean()
        
        # Store the results in the list as a dictionary
        category_results_list.append({
            'Category': category,
            'MarginCurveA': MarginCurveA,
            'MarginCurveB': MarginCurveB,
            'CI_A': ci_a,
            'CI_B': ci_b,
            'AverageElasticity': mean_elasticity
        })
    
    # Convert the list of dictionaries to a DataFrame
    category_results = pd.DataFrame(category_results_list)
    return category_results
