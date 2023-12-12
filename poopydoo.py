from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, session
from flask_session import Session
import plotly.express as px
import plotly.io as pio
import os
import pandas as pd
from forms import RegistrationForm, LoginForm
from wrangle_functions import custom_sort, adjust_decreasing_values, format_data, filter_data, apply_buckets, update_base_data, update_base_metadata
from data_retreive import get_param_data, get_param_metadata
import logging
app = Flask(__name__)

app.config['SECRET_KEY'] = '82697c2f22bccd4acc7b62e31f05b743'
app.config['SESSION_TYPE'] = 'filesystem'

# Set the directory for session files relative to the current script
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'session_data')

Session(app)

# Ensure the directory for session files exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)


@app.route("/")
def home():
    return render_template('home.html')

@app.route('/set_dataframe')
def set_dataframe():
    # Example DataFrame
    df = get_param_data()
    df_format = format_data(df)

    df_meta = get_param_metadata()
    
    filter_template = {
        'INVENTORY_CARRIER_CD': 'BA',
        'ROUTE': 'LHRDEN'
    }

    session['base_param_data'] = df_format.to_dict()
    # Convert DataFrame to JSON and store in session
    session['param_data'] = df_format.to_dict()

    session['base_param_metadata'] = df_meta.to_dict()
    session['param_metadata'] = df_meta.to_dict()

    session['user_filters'] = filter_template

    carriers = df['INVENTORY_CARRIER_CD'].unique().tolist()
    routes = df['ROUTE'].unique().tolist()
    
    filters = {
        'INVENTORY_CARRIER_CD': carriers,
        'ROUTE': routes
    }

    session['available_filters'] = filters
    return "Dataframe Stored in Session!"

@app.route('/filter_data', methods = ['POST'])
def filter_dataframe():

    filters = {
        'INVENTORY_CARRIER_CD': request.form.get('carrier'),
        'ROUTE': request.form.get('selected_route')
    }


    session['user_filters'] = filters

    list_data = session.get('base_param_data')
    list_metadata = session.get('base_param_metadata')

    session['param_data'] = filter_data(list_data, filters)
    session['param_metadata'] = filter_data(list_metadata, filters)


    return redirect(url_for('t_club'))

@app.route('/get_dataframe')
def get_dataframe():

    # Retrieve the DataFrame from the session
    json_data = session.get('param_data')
    if json_data:
        df = pd.DataFrame(json_data)
        return df.to_html()  # Displaying DataFrame as HTML table
    else:
        return "No DataFrame in session"

@app.route('/get_dataframe2')
def get_dataframe2():

    # Retrieve the DataFrame from the session
    json_data = session.get('param_metadata')
    if json_data:
        df = pd.DataFrame(json_data)
        return df.to_html()  # Displaying DataFrame as HTML table
    else:
        return "No DataFrame in session"


@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route('/tipp_club')
def t_club():


    df_metadata = pd.DataFrame(session.get('base_param_metadata'))

    filters = session.get('available_filters')
    unique_aln_values = filters['INVENTORY_CARRIER_CD']
    unique_routes = df_metadata['ROUTE'].unique()


    data_list = session.get('base_param_data')
    filters = session.get('user_filters')

    selected_carrier = filters['INVENTORY_CARRIER_CD']
    selected_route = filters['ROUTE']

    #Filter metadata to retreive params for selected route


    session['param_data'] = filter_data(data_list, filters)
    df = pd.DataFrame(session.get('param_data'))

    P1_Start = df_metadata[(df_metadata['ROUTE'] == selected_route) &
                       (df_metadata['INVENTORY_CARRIER_CD'] == selected_carrier) &
                       (df_metadata['PARAMETER_NO'] == 'P1')]['PERCENTILE'].max()
    P2_Start = df_metadata[(df_metadata['ROUTE'] == selected_route) &
                       (df_metadata['INVENTORY_CARRIER_CD'] == selected_carrier) &
                       (df_metadata['PARAMETER_NO'] == 'P2')]['PERCENTILE'].max()
    
    AP180 = df_metadata[(df_metadata['ROUTE'] == selected_route) &
                       (df_metadata['INVENTORY_CARRIER_CD'] == selected_carrier) &
                       (df_metadata['AP'] == 180)]['START_INDEX_NUM'].max()
    
    AP120 = df_metadata[(df_metadata['ROUTE'] == selected_route) &
                       (df_metadata['INVENTORY_CARRIER_CD'] == selected_carrier) &
                       (df_metadata['AP'] == 120)]['START_INDEX_NUM'].max()
    
    AP100 = df_metadata[(df_metadata['ROUTE'] == selected_route) &
                       (df_metadata['INVENTORY_CARRIER_CD'] == selected_carrier) &
                       (df_metadata['AP'] == 100)]['START_INDEX_NUM'].max()
    
    # Create a Plotly graph
    fig = px.scatter(x=df['P_PCT_180_P1'], y=df['PRICE_INDEX_NUM'])
     # Convert the figure to HTML

    # Reverse the direction of x-axis
    fig.update_xaxes(autorange="reversed")

    fig.update_layout(
        xaxis_title="I Availability/Cabin Capacity",
        yaxis_title="Relative Price"
    )

    graph_html = pio.to_html(fig, full_html=False)
    
    data = session['param_data']

    return render_template('t_club.html',
                            data=data,
                            enumerate=enumerate,
                            unique_aln_values=unique_aln_values,
                            selected_carrier = selected_carrier,
                            unique_routes = unique_routes,
                            selected_route = selected_route,
                            P1_Start = P1_Start, P2_Start = P2_Start,
                            AP180 = AP180, AP120 = AP120, AP100 = AP100,
                            graph_html=graph_html
                            )

@app.route('/update', methods=['POST'])
def update_data():

    df = pd.DataFrame(session.get('param_data'))
    df_meta = pd.DataFrame(session.get('param_metadata'))

    p1_to_adjust = ['P_PCT_180_P1', 'P_PCT_120_P1', 'P_PCT_100_P1']
    p2_to_adjust = ['P_PCT_180_P2', 'P_PCT_120_P2', 'P_PCT_100_P2']
    buckets = ['BUCKETS_180', 'BUCKETS_120', 'BUCKETS_100']

    # Update DataFrame with the submitted data
    for i in range(len(df)):
        # Check and update each field, avoiding overwriting disabled fields (value = 9)
        for column in buckets:
            form_value = request.form.get(f'{column}_{i}')
            if form_value is not None:
                df.at[i, column] = round(float(form_value), 2)
            elif df.at[i, column] != 9:
                df.at[i, column] = None  # Handle case where the field was not disabled but no value was submitted

    initial_p1 = float(request.form.get('P1_Start'))
    initial_p2 = float(request.form.get('P2_Start'))

    df_meta.loc[df_meta['PARAMETER_NO'] == 'P1', 'PERCENTILE'] = initial_p1
    df_meta.loc[df_meta['PARAMETER_NO'] == 'P2', 'PERCENTILE'] = initial_p2
    
    AP180 = int(request.form.get('AP180', 0))
    AP120 = int(request.form.get('AP120', 0))
    AP100 = int(request.form.get('AP100', 0))

    AP_Index = [AP180, AP120, AP100]

    #Update metadata df with new start indexes
    df_meta.loc[df_meta['AP'] == 180, 'START_INDEX_NUM'] = AP180
    df_meta.loc[df_meta['AP'] == 120, 'START_INDEX_NUM'] = AP120
    df_meta.loc[df_meta['AP'] == 100, 'START_INDEX_NUM'] = AP100

    print('AP_INDEX ', AP_Index)

    print('initial_p1 : ', initial_p1, type(initial_p1))
    df, changes_made = apply_buckets(df, buckets, 
                                     p1_to_adjust, initial_p1, p2_to_adjust, initial_p2,
                                     AP_Index) 

    if changes_made:
        flash("Adjustments Made. Ensure buckets add up to 100% and there are no negative values.", "danger")
    # Store updated DataFrame back in the session

    print(df)
    session['param_data'] = df.to_dict()
    session['base_param_data'] = update_base_data(session['base_param_data'], session['param_data'])

    print(session['param_data'])
    #Update metadata JSON with new dataframe
    session['param_metadata'] = df_meta.to_dict()
    session['base_param_metadata'] = update_base_metadata(session['base_param_metadata'], session['param_metadata'])

    return redirect(url_for('t_club'))


if __name__ == '__main__':
    app.run(debug=True)