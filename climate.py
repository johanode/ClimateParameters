# -*- coding: utf-8 -*-
"""
Created on Sun May 22 15:10:49 2022

@author: Johan Odelius
"""
import smhi
from helpers import get_types, validatestring
    
# sub functions
climate_weather_parameters = {
    'temperature' : [
        'TemperatureMeanPastMonth',    
        'TemperatureMaxPast24h',
        'TemperatureMinPast24h',
        'TemperaturePast24h'
        ],
    'precipitation' : [
        'PrecipPast24hAt06',
        'PrecipTypePast24h'
        ],
    'wind' : [
        'WindSpeed',
        'WindGust'
        ]
    }
climate_weather_parameters['combination'] = climate_weather_parameters['temperature'] + climate_weather_parameters['precipitation']

def list_stations(parameter_type='all'):
    if parameter_type.lower() == 'all':
        # list all climate paramters
        parameters = []
        for ty in climate_weather_parameters:
            parameters += climate_weather_parameters[ty]
    else:
        # validate that type is valid ['temperature','precipitation','wind','combination']
        ty = validatestring(parameter_type, climate_weather_parameters.keys())
        parameters = climate_weather_parameters[ty]
    
    # Make variable a set, i.e. remove dublicates
    paramsset = set(parameters)
    
    # Find stations for first parameter
    df_stations = smhi.list_stations(paramsset.pop())
    # Make stations id a set
    stations = set(df_stations['id'])
    # Loop the rest of parameters and update stations list with intersection
    for param in paramsset:
        stations = stations.intersection(smhi.list_stations(param, col='id'))
    
    # Output columns of dataframe
    cols = ['name','latitude','longitude','active','from','to']
    # Filter out valid stations
    df_output = df_stations.set_index('id').loc[stations,cols].reset_index()
    
    return df_output
    
def isin_station(station, parameter_type='all'):
    df_stations = list_stations(parameter_type)
    return station in df_stations['id'].to_list()

# %% Temperature

# Medeltemperatur
def TAS(station, ts, time_period='y'):
    # Medeltemperatur (TAS)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y','s'), default 'y'
    
    weather_parameter = 'TemperatureMeanPastMonth'
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Mean of TemperatureMeanPastMonth
    value = parameter_values.mean()

    return value

# Dygnsmaxtemperatur
def TX(station, ts, time_period='y'):
    # Dygnsmaxtemperatur (TX)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y','s','m'), default 'y'
    
    weather_parameter = 'TemperatureMaxPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Max of TemperatureMaxPast24h
    value = parameter_values.max()

    return value


# Dygnsminimitemperatur
def TN(station, ts, time_period='y'):
    # Dygnsminimitemperatur (TN)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y','s','m'), default 'y'
    
    weather_parameter = 'TemperatureMinPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Min of TemperatureMinPast24h
    value = parameter_values.min()

    return value


# Dygnsamplitud (varmast minus kallast)
def DTR(station, ts, time_period='m'):
    # Dygnsamplitud (varmast minus kallast) (DTR)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('m'), default 'm'

    weather_parameter = 'TemperatureMinPast24h'
    # Filter based on failure time and time period
    temperature_min = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'TemperatureMaxPast24h'
    # Filter based on failure time and time period
    temperature_max = smhi.get_values(weather_parameter, station, ts, time_period)
   
    # Amplitude: max temperature - min temperature
    amplitude = temperature_max-temperature_min

    # Max of daily amplitude values
    value = amplitude.max()

    return value


# Varma dagar/h??gsommardagar (Maxtemperatur >20 ??C)
def WarmDays(station, ts, time_period='y'):
    # Varma dagar (WarmDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y','s'), default 'y'
    
    weather_parameter = 'TemperatureMaxPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Number of days over 20 deg
    value = (parameter_values > 20).sum()

    return value


# V??rmeb??lja (dagar i f??ljd med maxtemperatur > 20??C)
def ConWarmDays(station, ts, time_period='y'):
    # V??rmeb??lja (ConWarmDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'TemperatureMaxPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Days in a row with temperature more than 20 deg
    number_of_days = 0
    max_number_of_days = 0
    temperature_threshold = 20
    for value in parameter_values:
        if value > temperature_threshold:
            number_of_days += 1
            max_number_of_days = max(max_number_of_days, number_of_days)
        else:
            number_of_days = 0

    return max_number_of_days

# Nollgenomg??ngar (Antal dagar med h??gsta temp > 0??C och l??gsta temp < 0??C)
def ZeroCrossingDays(station, ts, time_period='s'):
    # Nollgenomg??ngar (ZeroCrossingDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('s'), default 's'

    weather_parameter = 'TemperatureMinPast24h'
    # Filter based on failure time and time period
    temperature_min = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'TemperatureMaxPast24h'
    # Filter based on failure time and time period
    temperature_max = smhi.get_values(weather_parameter, station, ts, time_period)

    # Min temperature less than 0 and max temperature more than 0
    if temperature_min.size>0:
        value = ((temperature_min < 0) & (temperature_max > 0)).sum()
    else:
        value = float('NaN')

    return value

# Vegetationsperioden
def VegSeason(ser, temperature=5, days=4):
    # 4 days in a row with temperature more than 5 deg

    # Initialize variables
    number_of_days_above = 0
    veg_start = ser.iloc[-1]
    
    for idx, value in ser.iteritems():
        if value > temperature:
            number_of_days_above += 1
            if number_of_days_above >= days:
                veg_start = idx  # Vegperiod start
                break
        else:
            number_of_days_above = 0
    
    # Initialize variables
    number_of_days_below = 0
    previous = ser.loc[[veg_start]].index
    for idx, value in ser.loc[veg_start:].iteritems():
        # if start of vegperiod set and after 1 July 
        if idx.month >= 7 and value <= temperature:
            number_of_days_below += 1
            if number_of_days_below >= days:
                veg_end = previous  # Vegperiod slut
                break
        else:
            number_of_days_below = 0
            previous = idx
    
    return veg_start, veg_end

# Vegetationsperiodens slut (sista dag i sammanh??ngande 4-dags period med medeltemp > 5??C
def VegSeasonDayEnd(station, ts, time_period='y'):
    # Vegetationsperiodens slut (VegSeasonDayEnd-5)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Vegperiod
    _,veg_end = VegSeason(parameter_values)

    # Returning last date of vegperiod
    return veg_end


# Vegetationsperiodens b??rjan (sista dag i sammanh??ngande 4-dags period med medeltemp > 5 ??C)
def VegSeasonDayStart(station, ts, time_period='y'):
    # Vegetationsperiodens b??rjan (VegSeasonDayStart-5)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Vegperiod
    veg_start,_ = VegSeason(parameter_values)

    # Returning first date of vegperiod
    return veg_start


# Vegetationsperiodens l??ngd (medeltemp > 2/5??C)
def VegSeasonLentgh(station, ts, time_period='y', temperature=5):
    # Vegetationsperiodens l??ngd (VegSeasonLentgh-2/VegSeasonLentgh-5)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    #   temperature     : temperature definition of vegseason (2,5), default is 5

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Vegperiod
    veg_start,veg_end = VegSeason(parameter_values)

    # Returning length in days of vegperiod
    return (veg_end-veg_start).days


# Frostdagar (minimitemperatur < 0??C )
def FrostDays(station, ts, time_period='s'):
    # Frostdagar (FrostDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('s'), default 's'


    weather_parameter = 'TemperatureMinPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Count days where min temperature is less than 0
    value = (parameter_values < 0).sum()

    return value


# Kalla dagar (maxtemperatur < -7??C)
def ColdDays(station, ts, time_period='s'):
    # Kalla dagar (ColdDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('s'), default 's'

    weather_parameter = 'TemperatureMaxPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Days with max temperature less than -7
    value = (parameter_values < -7).sum()

    return value

# %% Nederb??rd

# Summa nederb??rd
def PR(station, ts, time_period='y'):
    # Summa nederb??rd (PR)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('m','y','s'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Sum of PrecipPast24hAt06
    value = parameter_values.sum()

    return value


# Summa regn
def PRRN(station, ts, time_period='y'):
    # Summa nederb??rd (PRRN)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period (y','s'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    # Join precipitation values with type of precipitation
    precip_data = precip_values.to_frame().join(precip_types.rename('Type'))
    
    # Data for days with rain
    valid_types = get_types('Rain')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types),'Value'].groupby(level=0).first()
    
    # Sum up all during time period
    value = precip_valid.sum()
                        
    return value


# Summa sn??
def PRSN(station, ts, time_period='y'):
    # Summa sn?? (PRSN)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period (y','s'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    # Join precipitation values with type of precipitation
    precip_data = precip_values.to_frame().join(precip_types.rename('Type'))
     
    # Data for days with valid precipitation
    valid_types = get_types('Snow')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types),'Value'].groupby(level=0).first()
    
    # Sum up all during time period
    value = precip_valid.sum()  
    
    return value


# Summa underkylt regn
def SuperCooledPR(station, ts, time_period='y'):
    # Underkylt regn (SuperCooledPR)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    # Join precipitation values with type of precipitation
    precip_data = precip_values.to_frame().join(precip_types.rename('Type'))
     
    # Cooled rain types
    valid_types = get_types('SuperCooledRain')
    
    # Data for days with valid precipitation
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types),'Value'].groupby(level=0).first()
    
    # Sum up all during time period
    value = precip_valid.sum()

    return value


# H??gsta nederb??rd under 7 dagar
def PR7Dmax(station, ts, time_period='y'):
    # H??gsta nederb??rd  (PR7Dmax)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Sum of PrecipPast24hAt06 for rolling window of 7 days (sum or max??)
    values = parameter_values.rolling(7).sum()

    # Max of sum of precipitation
    return values.max()


# Maximal nederb??rdsintensitet
def PRmax(station, ts, time_period='y'):
    # Maximal nederb??rd  (PRmax)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Max of PrecipPast24hAt06
    value = parameter_values.max()

    return value


# Maximal sn??fallsintensitet
def PRSNmax(station, ts, time_period='y'):
    # Maximal sn??fall  (PRSNmax)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    # Join precipitation values with type of precipitation
    precip_data = precip_values.to_frame().join(precip_types.rename('Type'))
  
    # Snow types
    valid_types = get_types('Snow') 
    
    # precip_data.loc[precip_data['Type'].isin(valid_types)].groupby('Type').max()
    
    # Data for days with valid precipitation
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types),'Value'].groupby(level=0).first()
    
    # Max during time period
    value = precip_valid.max()

    return value


# Kraftig nederb??rd > 10 mm/dygn
def PRgt10Days(station, ts, time_period='y'):
    # Kraftig nederb??rd  (PRgt10Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('s','y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Days of more than 10 mm precip
    value = (parameter_values > 10).sum()

    return value

# Extrem nederb??rd > 25 mm/dygn
def PRgt25Days(station, ts, time_period='y'):
    # Extrem nederb??rd  (PRgt25Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('s','y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Days of more than 25 mm precip
    value = (parameter_values > 25).sum()

    return value


# Torra dagar (med nederb??rd < 1 mm)
def DryDays(station, ts, time_period='m'):
    # Torra dagar  (DryDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('m'), default 'm'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Days of less than 1 mm precip
    if parameter_values.size>0:
        value = (parameter_values < 1).sum()
    else:
        value = float('NaN')

    return value

# %% Sn?? p?? marken
# Sn??t??cke
def SncDays(station, ts, time_period='y'):
    # Sn??t??cke  (SncDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'SnowDepthPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Number of days with snow
    if parameter_values.size>0:
        value = (parameter_values > 0).sum()
    else:
        value = float('NaN')
        
    return value

# Maximalt sn??djup (r??knat som vatteninneh??ll)
def SNWmax(station, ts, time_period='y'):
    # Maximalt sn??djup  (SNWmax)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'SnowDepthPast24h'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, station, ts, time_period)

    # Maximum snow depth
    value = parameter_values.max()

    return value

# %% Vind och densitet

# Medelvindhastighet i 10m-niv??
def SfcWind(station, ts, time_period='y'):
    # Medelvindhastighet  (SfcWind)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('s','y'), default 'y'

    weather_parameter = 'WindSpeed'
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, ts, time_period, idx='Date (UTC)')
    
    # Daily max of mean windspeed observations
    values = parameter_values.resample('1D').max()

    # Max of daily max during time period
    return values.max()

# Maximal byvind (10m-niv??)


def WindGustMax(station, ts, time_period='y'):
    # Maximal byvind  (WindGustMax)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'WindGust'  # Wind Gust
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, ts, time_period, idx='Date (UTC)')
    
    # Daily max of wind gust (byvind) observations
    values = parameter_values.resample('1D').max()

    # Max of daily max during time period
    return values.max()


# Antal dagar med byvind >21 m/s (10m-niv??)
def WindyDays(station, ts, time_period='y'):
    # Antal dagar med h??rd byvind  (WindyDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'WindGust'  # Wind Gust
    # Filter based on failure time and time period
    parameter_values = smhi.get_values(weather_parameter, ts, time_period, idx='Date (UTC)')
    
    # Number of days with daily max of wind gust (byvind) above 21
    if parameter_values.size>0:
        value = (parameter_values.resample('1D').max() > 21).sum()
    else:
        value = float('NaN')

    return value

#%% Kombinationsindex

# Nederb??rd n??r temperaturen ligger mellan 0.58 och 2 grader
def ColdRainDays(station, ts, time_period='y'):
    # Dagar kall nederb??rd  (ColdRainDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # weather_parameter = 'PrecipTypePast24h'
    # # Filter based on failure time and time period
    # precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # precip_data = precip_data.join(precip_types.rename('Type'))
    # valid_types = get_types('Rain')
    # precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)]
    
    # Days with precip given temperature interval
    if precip_values.size>0:
        temperature_threshold = [.58, 2]
        i_temperature = (precip_data['Temperature']>temperature_threshold[0]) & (precip_data['Temperature']<temperature_threshold[1])
        value = (precip_data.loc[i_temperature,'Value']>0).sum()
    else:
        value = float('NaN')

    return value


# Nederb??rd ( > 10 mm/dygn) n??r temperaturen ligger mellan 0.58 och 2 grader
def ColdRainGT10Days(station, ts, time_period='y'):
    # Dagar mkt kall nederb??rd  (ColdRainGT10Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # weather_parameter = 'PrecipTypePast24h'
    # # Filter based on failure time and time period
    # precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # precip_data = precip_data.join(precip_types.rename('Type'))
    # valid_types = get_types('Rain')
    # precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)]
    
    # Number of days of precip > 10 given temperature interval
    if precip_values.size>0:
        temperature_threshold = [.58, 2]
        i_temperature = (precip_data['Temperature']>temperature_threshold[0]) & (precip_data['Temperature']<temperature_threshold[1])
        precip_threshold = 10
        value = (precip_data.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value


# Nederb??rd ( > 20 mm/dygn) n??r temperaturen ligger mellan 0.58 och 2 grader
def ColdRainGT20Days(station, ts, time_period='y'):
    # Dagar kraftig kall nederb??rd  (ColdRainGT20Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
   # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # weather_parameter = 'PrecipTypePast24h'
    # # Filter based on failure time and time period
    # precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # precip_data = precip_data.join(precip_types.rename('Type'))
    # valid_types = get_types('Rain')
    # precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)]
    
    # Number of days of precip > 20 given temperature interval
    if precip_values.size>0:
        temperature_threshold = [.58, 2]
        i_temperature = (precip_data['Temperature']>temperature_threshold[0]) & (precip_data['Temperature']<temperature_threshold[1])
        precip_threshold = 20
        value = (precip_data.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value

# Nederb??rd n??r temperaturen ligger mellan -2 och 0.58 grader
def WarmSnowDays(station, ts, time_period='y'):
    # Dagar varm sn??  (WarmSnowDays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # weather_parameter = 'PrecipTypePast24h'
    # # Filter based on failure time and time period
    # precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # precip_data = precip_data.join(precip_types.rename('Type'))
    # valid_types = get_types('Snow')
    # precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)]
    
    # Days with precip given temperature interval
    if precip_values.size>0:
        temperature_threshold = [-2, .58]
        i_temperature = (precip_data['Temperature']>temperature_threshold[0]) & (precip_data['Temperature']<temperature_threshold[1])
        value = (precip_data.loc[i_temperature,'Value']>0).sum()
    else:
        value = float('NaN')

    return value


# Nederb??rd (> 10 mm/dygn) n??r temperaturen ligger mellan -2 och 0.58 grader
def WarmSnowGT10Days(station, ts, time_period='y'):
    # Dagar mkt varm sn??  (WarmSnowGT10Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # weather_parameter = 'PrecipTypePast24h'
    # # Filter based on failure time and time period
    # precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # precip_data = precip_data.join(precip_types.rename('Type'))
    # valid_types = get_types('Snow')
    # precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)]
    
    # Number of days of precip > 10 given temperature interval
    if precip_values.size>0:
        temperature_threshold = [-2, .58]
        i_temperature = (precip_data['Temperature']>temperature_threshold[0]) & (precip_data['Temperature']<temperature_threshold[1])
        precip_threshold = 10
        value = (precip_data.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value


# Nederb??rd (> 20 mm/dygn) n??r temperaturen ligger mellan -2 och 0.58 grader
def WarmSnowGT20Days(station, ts, time_period='y'):
    # Dagar kraft varm sn??  (WarmSnowGT20Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # weather_parameter = 'PrecipTypePast24h'
    # # Filter based on failure time and time period
    # precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # precip_data = precip_data.join(precip_types.rename('Type'))
    # valid_types = get_types('Snow')
    # precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)]
    
    # Number of days of precip > 20 given temperature interval
    if precip_values.size>0:
        temperature_threshold = [-2, .58]
        i_temperature = (precip_data['Temperature']>temperature_threshold[0]) & (precip_data['Temperature']<temperature_threshold[1])
        precip_threshold = 20
        value = (precip_data.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value


# Regn n??r temperaturen ??r under 2 grader
def ColdPRRNdays(station, ts, time_period='y'):
    # Regn under 2 grader  (ColdPRRNdays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # Add precipitaion type
    precip_data = precip_data.join(precip_types.rename('Type'))
    # Filter out days with rain
    valid_types = get_types('Rain')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)].groupby(level=0).first()
    
    # Number of days of rain given temperature interval
    if precip_valid.size>0:
        temperature_threshold = 2
        i_temperature = precip_data['Temperature']<temperature_threshold
        value = (precip_valid.loc[i_temperature,'Value']>0).sum()
    else:
        value = float('NaN')

    return value


# Regn ( > 10 mm/dygn) n??r temperaturen ??r under 2 grader
def ColdPRRNgt10Days(station, ts, time_period='y'):
    # Regn under 2 grader  (ColdPRRNgt10Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # Add precipitaion type
    precip_data = precip_data.join(precip_types.rename('Type'))
    # Filter out days with rain
    valid_types = get_types('Rain')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)].groupby(level=0).first()
    
    # Number of days of rain more than 10 mm given temperature interval
    if precip_valid.size>0:
        temperature_threshold = 2
        i_temperature = precip_valid['Temperature']<temperature_threshold
        precip_threshold = 10
        value = (precip_valid.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value

# Regn ( > 20 mm/dygn) n??r temperaturen ??r under 2 grader
def ColdPRRNgt20Days(station, ts, time_period='y'):
    # Regn under 2 grader  (ColdPRRNgt20Days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
   
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # Add precipitaion type
    precip_data = precip_data.join(precip_types.rename('Type'))
    # Filter out days with rain
    valid_types = get_types('Rain')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)].groupby(level=0).first()
    
    # Number of days of rain more than 20 mm given temperature threshold
    if precip_valid.size>0:
        temperature_threshold = 2
        i_temperature = precip_valid['Temperature']<temperature_threshold
        precip_threshold = 20
        value = (precip_valid.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value


# Sn?? n??r temperaturen ??r ??ver -2 grader
def WarmPRSNdays(station, ts, time_period='y'):
    # Sn?? ??ver -2 grader  (WarmPRSNdays)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # Add precipitaion type
    precip_data = precip_data.join(precip_types.rename('Type'))
    # Filter out days with snow
    valid_types = get_types('Snow')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)].groupby(level=0).first()
    
    # Number of days of rain given temperature interval
    if precip_valid.size>0:
        temperature_threshold = -2
        i_temperature = precip_valid['Temperature']>temperature_threshold
        value = (precip_valid.loc[i_temperature,'Value']>0).sum()
    else:
        value = float('NaN')

    return value


# Sn?? ( > 10 mm/dygn) n??r temperaturen ??r ??ver -2 grader
def WarmPRSNgt10days(station, ts, time_period='y'):
    # Sn?? ??ver -2 grader  (WarmPRSNgt10days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'
    
    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # Add precipitaion type
    precip_data = precip_data.join(precip_types.rename('Type'))
    # Filter out days with snow
    valid_types = get_types('Snow')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)].groupby(level=0).first()
    
    # Number of days of rain given temperature threshold
    if precip_valid.size>0:
        temperature_threshold = -2
        i_temperature = precip_valid['Temperature']>temperature_threshold
        precip_threshold = 10
        value = (precip_valid.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value

# Sn?? ( > 20 mm/dygn) n??r temperaturen ??r ??ver -2 grader
def WarmPRSNgt20days(station, ts, time_period='y'):
    # Sn?? ??ver -2 grader  (WarmPRSNgt20days)
    # Input
    #   station         : station id [int]
    #   ts              : timestamp
    #   time_period     : time period ('y'), default 'y'

    weather_parameter = 'PrecipPast24hAt06'
    # Filter based on failure time and time period
    precip_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    weather_parameter = 'PrecipTypePast24h'
    # Filter based on failure time and time period
    precip_types = smhi.get_values(weather_parameter, station, ts, time_period)

    weather_parameter = 'TemperaturePast24h'
    # Filter based on failure time and time period
    temperature_values = smhi.get_values(weather_parameter, station, ts, time_period)
    
    # Add temperture values to the precipitaion values
    precip_data = precip_values.to_frame().join(temperature_values.rename('Temperature'))
    # Add precipitaion type
    precip_data = precip_data.join(precip_types.rename('Type'))
    # Filter out days with snow
    valid_types = get_types('Snow')
    precip_valid = precip_data.loc[precip_data['Type'].isin(valid_types)].groupby(level=0).first()
    
    # Number of days of rain given temperature interval
    if precip_valid.size>0:
        temperature_threshold = -2
        i_temperature = precip_valid['Temperature']>temperature_threshold
        precip_threshold = 20
        value = (precip_valid.loc[i_temperature,'Value']>precip_threshold).sum()
    else:
        value = float('NaN')

    return value