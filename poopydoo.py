from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, session
from flask_session import Session
import os
import pandas as pd
from forms import RegistrationForm, LoginForm
from wrangle_functions import custom_sort, adjust_decreasing_values, format_data
import logging
app = Flask(__name__)

app.config['SECRET_KEY'] = '82697c2f22bccd4acc7b62e31f05b743'
app.config['SESSION_TYPE'] = 'filesystem'

# Set the directory for session files relative to the current script
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'session_data')

Session(app)

# Ensure the directory for session files exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

df_raw=pd.read_csv(rf'/Users/danielchung/Downloads/TIP PARAM - Sheet1.csv')

df_param = format_data(df_raw)

print(df_param)

posts = [
    {
        'author': 'Daniel Chung',
        'title':'The d',
        'content': 'The d!!!',
        'Date': 'Today'
    },
    {
        'author': 'BA',
        'title':'The d',
        'content': 'The d!!!',
        'Date': 'Today'
    }
]

@app.route("/")
def home():
    return render_template('home.html', posts=posts)

@app.route('/set_dataframe')
def set_dataframe():
    # Example DataFrame
    df = pd.read_csv(rf'/Users/danielchung/Downloads/TIP PARAM - Sheet1.csv') #replace with sql query
    df_format = format_data(df)

    session['base_data'] = df_format.to_json()
    # Convert DataFrame to JSON and store in session
    session['dataframe'] = df_format.to_json()

    return "DataFrame stored in session!"

@app.route('/get_dataframe')
def get_dataframe():
    # Retrieve the DataFrame from the session
    json_data = session.get('dataframe')
    if json_data:
        df = pd.read_json(json_data)
        return df.to_html()  # Displaying DataFrame as HTML table
    else:
        return "No DataFrame in session"

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))

    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():


    form = LoginForm()

    if form.validate_on_submit():
        flash("Form validated", "info")
        if form.username.data == 'tipp' and form.password.data =='password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    else:
        print("Form validation failed")

    return render_template('login.html', title='Login', form=form)


@app.route('/tipp_club')
def t_club():
    json_data = session.get('dataframe')
    if json_data:
        df = pd.read_json(json_data)
        unique_aln_values = df['INVENTORY_CARRIER_CD'].unique().tolist()
        data = df.to_dict(orient='records')
        return render_template('t_club.html', data=data, enumerate=enumerate, unique_aln_values=unique_aln_values)
    else:
        return "No DataFrame in session"

@app.route('/update', methods=['POST'])
def update_data():
    selected_carrier = request.form.get('carrier')
    json_data = session.get('dataframe')
    if not json_data:
        flash("No DataFrame in session", "error")
        return redirect(url_for('t_club'))

    df = pd.read_json(json_data)
    print(selected_carrier, df['INVENTORY_CARRIER_CD'].unique())
    df= df[df['INVENTORY_CARRIER_CD'] == selected_carrier]

    # Update DataFrame with the submitted data
    for i in range(len(df)):
        # Check and update each field, avoiding overwriting disabled fields (value = 9)
        for column in ['180_P1', '180_P2', '120_P1', '120_P2', '100_P1', '100_P2']:
            form_value = request.form.get(f'{column}_{i}')
            if form_value is not None:
                df.at[i, column] = round(float(form_value), 2)
            elif df.at[i, column] != 9:
                df.at[i, column] = None  # Handle case where the field was not disabled but no value was submitted


    columns_to_adjust = ['180_P1', '180_P2', '120_P1', '120_P2', '100_P1', '100_P2']
    df, changes_made = adjust_decreasing_values(df, columns_to_adjust)

    if changes_made:
        flash("Adjustments Made. Ensure Parameters Always Decreasing", "danger")

    session['dataframe'] = df.to_json()  # Store updated DataFrame back in the session
    return redirect(url_for('t_club'))


if __name__ == '__main__':
    app.run(debug=True)