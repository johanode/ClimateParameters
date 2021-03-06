import datetime
# import sys
# import logging
import json
import requests


# functions
def api_return_data(adr):
    # initiate the call
    req_obj = requests.get(adr)
    # try to get the json data (exceptions will be catched later)
    json_data = req_obj.json()
    return json_data

def validatestring(inputStr, validStrings, only_forward=False):
    # matchedStr = validatestring(inputStr,validStrings) 
    # checks the validity of inputStr against validStrings. 
    # The text is valid if it is an unambiguous, 
    # case-insensitive match to any element in validStrings.
    
    outputStrings = set()
    checkStr = inputStr.lower()
    validStrings = set(validStrings)
    compareStrings = [x.lower() for x in validStrings]
    for compareStr, validStr in zip(compareStrings, validStrings):
        if checkStr == compareStr:
            outputStrings = {validStr}
            break
        elif only_forward:
            if compareStr.startswith(checkStr) or checkStr.startswith(compareStr):
                outputStrings.update({validStr})               
        # elif compareStr.startswith(checkStr) or compareStr.endswith(checkStr): 
            # outputStrings.update({validStr})
        elif checkStr in compareStr or compareStr in checkStr:
            outputStrings.update({validStr})
            
    
    if len(outputStrings)==0:
        raise ValueError('The input did not match any of the valid values.')
    elif len(outputStrings)>1:
        raise ValueError('The input matched more than one valid value.')
     
    return outputStrings.pop()

def get_season(ts):
    # Define month for the seasons
    s1 = [12, 1, 2]
    s2 = [3, 4, 5]
    s3 = [6, 7, 8]
    s4 = [9, 10, 11]

    m = []
    for s in [s1, s2, s3, s4]:
        if ts.month in s:
            m = s
            break
    return m


def get_filter(ts, time_period='day'):
    #Validate input time_period
    time_period = validatestring(time_period, ['day','week','month','season','year'], only_forward=True)
    
    if time_period == 'day':
        if isinstance(ts,datetime.date):
            time_filter = [str(ts)]
        else:
            time_filter = [str(ts.date())]
    
    elif time_period == 'week':
        # w = ts.isocalendar().week
        d = ts.isocalendar().weekday
        dt = datetime.timedelta(1)
        ts1 = ts-(d-1)*dt
        ts2 = ts+(7-d)*dt
        time_filter = [
            '%d-%02d-%02d' % (ts1.year, ts1.month, ts1.day),
            '%d-%02d-%02d' % (ts2.year, ts2.month, ts2.day)
            ]
    
    elif time_period == 'month':
        time_filter = ['%d-%02d' % (ts.year, ts.month)]
    
    elif time_period == 'season':
        m = get_season(ts)
        if 12 in m:
            m1 = '%d-%02d' % (ts.year-1, 12)
        else:
            m1 = '%d-%02d' % (ts.year, m[0])
        m2 = '%d-%02d' % (ts.year, m[-1])
        time_filter = [m1, m2]
    
    elif time_period == 'year':
        time_filter = [str(ts.year)]
    
    else:
        raise ValueError('The input time period did not match any of ''day'', ''week'', ''month'', ''season'', ''year''')

        
    return time_filter

def get_types(cat):
    PrecitipationTypes = ['snowfall',
                'regn',
                'duggregn',
                'regnskurar',
                'kornsn??',
                'sn??blandat regn',
                'sn??byar',
                'Obest??md nederb??rdstyp',
                'isn??lar',
                'underkyld nederb??rd',
                'iskorn',
                'sm??hagel',
                'byar av sn??blandat regn',
                'sn??hagel',
                'ishagel']
    
    if cat.lower()=='rain':
        return ['regn', 'duggregn', 'regnskurar']
    elif cat.lower()=='snow':
        return ['snowfall', 'kornsn??', 'sn??byar', 'sn??hagel']
    elif cat.lower()=='snowslush':
        return ['sn??blandat regn', 'byar av sn??blandat regn']
    elif cat.lower()=='supercooledrain':
        return ['underkyld nederb??rd']
    else: 
        return []
    
def filter_time(df, ts, time_period, idx, col):
    if ts in df[idx].values or (df[idx]-ts).abs().min().days<df[idx].diff().mean().days:
        time_filter = get_filter(ts, time_period)
    
        if len(time_filter)>=2:
            df_filter = df.set_index(idx).loc[time_filter[0]:time_filter[-1]]
        else:
            df_filter = df.set_index(idx).loc[time_filter[0]]
        if col is not None:
            return df_filter[col]
        else:
            return df_filter
    else:
        return df.loc[[]]
        
    
def get_parameters():
    # See https://opendata.smhi.se/apidocs/metobs/parameter.html
    # Thanks also to https://github.com/LasseRegin/smhi-open-data
    
    # with open('parameters.json', encoding='utf-8') as fp:
    #     parameters = json.load(fp)
    
    parameters = [
        {'label' : 'TemperaturePast1h', 'key' : 1          , 'name' : 'Lufttemperatur'                        , 'Note' : 'Momentanv??rde, 1 g??ng/tim'},
        {'label' : 'TemperaturePast24h', 'key' : 2         , 'name' : 'Lufttemperatur'                        , 'Note' : 'Medelv??rde 1 dygn, 1 g??ng/dygn, kl 00'},
        {'label' : 'WindDirection', 'key' : 3              , 'name' : 'Vindriktning'                          , 'Note' : 'Medelv??rde 10 min, 1 g??ng/tim'},
        {'label' : 'WindSpeed', 'key' : 4                  , 'name' : 'Vindhastighet'	                      , 'Note' : '  Medelv??rde 10 min, 1 g??ng/tim'},
        {'label' : 'PrecipPast24hAt06', 'key' : 5          , 'name' : 'Nederb??rdsm??ngd'                       , 'Note' : 'Summa 1 dygn, 1 g??ng/dygn, kl 06'},
        {'label' : 'Humidity', 'key' : 6                   , 'name' : 'Relativ Luftfuktighet'	              , 'Note' : 'Momentanv??rde, 1 g??ng/tim'},
        {'label' : 'PrecipPast1h', 'key' : 7               , 'name' : 'Nederb??rdsm??ngd'                       , 'Note' : 'Summa 1 timme, 1 g??ng/tim'},
        {'label' : 'SnowDepthPast24h', 'key' : 8           , 'name' : 'Sn??djup'                               , 'Note' : 'Momentanv??rde, 1 g??ng/dygn, kl 06'},
        {'label' : 'Pressure', 'key' : 9                   , 'name' : 'Lufttryck reducerat havsytans niv??'    , 'Note' : 'Vid havsytans niv??, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'SunLast1h', 'key' : 10                 , 'name' : 'Solskenstid'                           , 'Note' : 'Summa 1 timme, 1 g??ng/tim'},
        {'label' : 'RadiaGlob', 'key' : 11                 , 'name' : 'Global Irradians (svenska stationer)'  , 'Note' : 'Medelv??rde 1 timme, 1 g??ng/tim'},
        {'label' : 'Visibility', 'key' : 12                , 'name' : 'Sikt'                                  , 'Note' : 'Momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CurrentWeather', 'key' : 13            , 'name' : 'R??dande v??der'                         , 'Note' : 'Momentanv??rde, 1 g??ng/tim resp 8 g??nger/dygn'},
        {'label' : 'PrecipPast15m', 'key' : 14             , 'name' : 'Nederb??rdsm??ngd'                       , 'Note' : 'Summa 15 min, 4 g??nger/tim'},
        {'label' : 'PrecipMaxPast15m', 'key' : 15          , 'name' : 'Nederb??rdsintensitet'                  , 'Note' : 'Max under 15 min, 4 g??nger/tim'},
        {'label' : 'CloudCover', 'key' : 16                , 'name' : 'Total molnm??ngd'                       , 'Note' : 'Momentanv??rde, 1 g??ng/tim'},
        {'label' : 'PrecipPast12h', 'key' : 17             , 'name' : 'Nederb??rd'                             , 'Note' : '2 g??nger/dygn, kl 06 och 18'},
        {'label' : 'PrecipTypePast24h', 'key' : 18         , 'name' : 'Typ av nederb??rd'                      , 'Note' : '4 g??ng/dygn'},
        {'label' : 'TemperatureMinPast24h', 'key' : 19     , 'name' : 'Lufttemperatur'                        , 'Note' : 'Min, 1 g??ng per dygn'},
        {'label' : 'TemperatureMaxPast24h', 'key' : 20     , 'name' : 'Lufttemperatur'                        , 'Note' : 'Max, 1 g??ng per dygn'},
        {'label' : 'WindGust', 'key' : 21             , 'name' : 'Byvind'                                , 'Note' : 'Max, 1 g??ng/tim'},
        {'label' : 'TemperatureMeanPastMonth', 'key' : 22  , 'name' : 'Lufttemperatur'                        , 'Note' : 'Medel, 1 g??ng per m??nad'},
        {'label' : 'PrecipPastMonth', 'key' : 23           , 'name' : 'Nederb??rdsm??ngd'                       , 'Note' : 'Summa, 1 g??ng per m??nad'},
        {'label' : 'LongwaveIrradians', 'key' : 24         , 'name' : 'L??ngv??gs-Irradians'                    , 'Note' : 'L??ngv??gsstr??lning, medel 1 timme, varje timme'},
        {'label' : 'WindSpeedMaxMeanPast3h', 'key' : 25    , 'name' : 'Max av MedelVindhastighet'             , 'Note' : 'Maximum av medelv??rde 10 min, under 3 timmar,...'},
        {'label' : 'TemperatureMinPast12h', 'key' : 26     , 'name' : 'Lufttemperatur'                        , 'Note' : 'Min, 2 g??nger per dygn, kl 06 och 18'},
        {'label' : 'TemperatureMaxPast12h', 'key' : 27	   , 'name' : 'Lufttemperatur'                        , 'Note' : 'Max, 2 g??nger per dygn, kl 06 och 18'},
        {'label' : 'CloudLayerLowest', 'key' : 28          , 'name' : 'Molnbas'                               , 'Note' : 'L??gsta molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudAmountLowest', 'key' : 29         , 'name' : 'Molnm??ngd'                             , 'Note' : 'L??gsta molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudLayerOther', 'key' : 30           , 'name' : 'Molnbas'                               , 'Note' : 'Andra molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudAmountOther', 'key' : 31          , 'name' : 'Molnm??ngd'                             , 'Note' : 'Andra molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudLayer3rd', 'key' : 32             , 'name' : 'Molnbas'                               , 'Note' : 'Tredje molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudAmount3rd', 'key' : 33            , 'name' : 'Molnm??ngd'                             , 'Note' : 'Tredje molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudLayer4th', 'key' : 34             , 'name' : 'Molnbas'                               , 'Note' : 'Fj??rde molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudAmount4th', 'key' : 35            , 'name' : 'Molnm??ngd'                             , 'Note' : 'Fj??rde molnlager, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudStorageLowest', 'key' : 36        , 'name' : 'Molnbas'                               , 'Note' : 'L??gsta molnbas, momentanv??rde, 1 g??ng/tim'},
        {'label' : 'CloudStorageLowestMin', 'key' : 37     , 'name' : 'Molnbas'                               , 'Note' : 'L??gsta molnbas, min under 15 min, 1 g??ng/tim'},
        {'label' : 'PrecipIntensityMaxMeanPast15m', 'key' : 38, 'name' : 'Nederb??rdsintensitet'               , 'Note' : 'Max av medel under 15 min, 4 g??nger/tim'},
        {'label' : 'TemperatureDew', 'key' : 39            , 'name' : 'Daggpunktstemperatur'                  , 'Note' : 'Momentanv??rde, 1 g??ng/tim'},
        {'label' : 'GroundCondition', 'key' : 40           , 'name' : 'Markens tillst??nd'                     , 'Note' : 'Momentanv??rde, 1 g??ng/dygn, kl 06'},
        ]
    return parameters

def get_indicators():
    with open('indicators.json', encoding='utf-8') as fp:
        indicators = json.load(fp)
    return indicators