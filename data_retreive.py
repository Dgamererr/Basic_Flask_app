import pandas as pd

def get_param_data():
    df_raw = pd.read_csv(rf'/Users/danielchung/Downloads/TIP PARAM - Sheet1.csv')

    return df_raw

def get_param_metadata():
    df_raw = pd.read_csv(rf'/Users/danielchung/Downloads/TIPP_PARAM_MD.csv')

    return df_raw