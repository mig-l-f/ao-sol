"""
Copyright (c) 2013-2021, Sandia National Laboratories and pvlib python Development Team
All rights reserved.

Get, read, and parse data from `PVGIS <https://ec.europa.eu/jrc/en/pvgis>`_.

For more information, see the following links:
* `Non-interactive tools <https://joint-research-centre.ec.europa.eu/pvgis-photovoltaic-geographical-information-system/getting-started-pvgis/api-non-interactive-service_en>`_
* `Interactive Tools <https://re.jrc.ec.europa.eu/pvg_tools/en/tools.html>`_
* `Data downloads <https://ec.europa.eu/jrc/en/PVGIS/downloads/data>`_
* `User manual docs <https://ec.europa.eu/jrc/en/PVGIS/docs/usermanual>`_

More detailed information about the API for TMY and hourly radiation are here:
* `TMY <https://ec.europa.eu/jrc/en/PVGIS/tools/tmy>`_
* `hourly radiation
  <https://ec.europa.eu/jrc/en/PVGIS/tools/hourly-radiation>`_
* `daily radiation <https://ec.europa.eu/jrc/en/PVGIS/tools/daily-radiation>`_
* `monthly radiation
  <https://ec.europa.eu/jrc/en/PVGIS/tools/monthly-radiation>`_
"""
import io
import json
from pathlib import Path
import requests
import pandas as pd
import warnings

#URL = 'https://re.jrc.ec.europa.eu/api/'
URL = 'https://re.jrc.ec.europa.eu/api/v5_2/'

# Dictionary mapping PVGIS names to pvlib names
PVGIS_VARIABLE_MAP = {
    'G(h)': 'ghi',
    'Gb(n)': 'dni',
    'Gd(h)': 'dhi',
    'G(i)': 'poa_global',
    'Gb(i)': 'poa_direct',
    'Gd(i)': 'poa_sky_diffuse',
    'Gr(i)': 'poa_ground_diffuse',
    'H_sun': 'solar_elevation',
    'T2m': 'temp_air',
    'RH': 'relative_humidity',
    'SP': 'pressure',
    'WS10m': 'wind_speed',
    'WD10m': 'wind_direction',
}

def get_pvgis_hourly(latitude, longitude, start=None, end=None,
                     raddatabase='PVGIS-ERA5', components=False,
                     surface_tilt=0, surface_azimuth=0,
                     outputformat='json',
                     usehorizon=True, userhorizon=None,
                     pvcalculation=True,
                     peakpower=None, pvtechchoice='crystSi',
                     mountingplace='building', loss=14, trackingtype=0,
                     optimal_surface_tilt=False, optimalangles=False,
                     url=URL, map_variables=True, timeout=60):
    """Get hourly solar irradiation and modeled PV power output from PVGIS.

    PVGIS data is freely available at [1]_.

    Parameters
    ----------
    latitude: float
        In decimal degrees, between -90 and 90, north is positive (ISO 19115)
    longitude: float
        In decimal degrees, between -180 and 180, east is positive (ISO 19115)
    start: int or datetime like, default: None
        First year of the radiation time series. Defaults to first year
        available.
    end: int or datetime like, default: None
        Last year of the radiation time series. Defaults to last year
        available.
    raddatabase: str, default: 'PVGIS-ERA5'
        Name of radiation database. Options depend on location, see [3]_.
        "PVGIS-SARAH" for Europe, Africa and Asia or "PVGIS-NSRDB" for the Americas between 60°N and 20°S, 
        "PVGIS-ERA5" and "PVGIS-COSMO" for Europe (including high-latitudes), 
        and "PVGIS-CMSAF" for Europe and Africa (will be deprecated)
    components: bool, default: False
        Output solar radiation components (beam, diffuse, and reflected).
        Otherwise only global irradiance is returned.
    surface_tilt: float, default: 0
        Tilt angle from horizontal plane. Ignored for two-axis tracking.
    surface_azimuth: float, default: 0
        Orientation (azimuth angle) of the (fixed) plane. 0=south, 90=west,
        -90: east. Ignored for tracking systems.
    usehorizon: bool, default: True
        Include effects of horizon
    userhorizon: list of float, default: None
        Optional user specified elevation of horizon in degrees, at equally
        spaced azimuth clockwise from north, only valid if ``usehorizon`` is
        true, if ``usehorizon`` is true but ``userhorizon`` is ``None`` then
        PVGIS will calculate the horizon [4]_
    pvcalculation: bool, default: True
        Return estimate of hourly PV production.
    peakpower: float, default: None
        Nominal power of PV system in kW. Required if pvcalculation=True.
    pvtechchoice: {'crystSi', 'CIS', 'CdTe', 'Unknown'}, default: 'crystSi'
        PV technology.
    mountingplace: {'free', 'building'}, default: building
        Type of mounting for PV system. Options of 'free' for free-standing
        and 'building' for building-integrated.
    loss: float, default: 14
        Sum of PV system losses in percent. Required if pvcalculation=True
    trackingtype: {0, 1, 2, 3, 4, 5}, default: 0
        Type of suntracking. 0=fixed, 1=single horizontal axis aligned
        north-south, 2=two-axis tracking, 3=vertical axis tracking, 4=single
        horizontal axis aligned east-west, 5=single inclined axis aligned
        north-south.
    optimal_surface_tilt: bool, default: False
        Calculate the optimum tilt angle. Ignored for two-axis tracking
    optimalangles: bool, default: False
        Calculate the optimum tilt and azimuth angles. Ignored for two-axis
        tracking.
    outputformat: str, default: 'json'
        Must be in ``['json', 'csv']``. See PVGIS hourly data
        documentation [2]_ for more info.
    url: str, default: :const:`pvlib.iotools.pvgis.URL`
        Base url of PVGIS API. ``seriescalc`` is appended to get hourly data
        endpoint.
    map_variables: bool, default: True
        When true, renames columns of the Dataframe to pvlib variable names
        where applicable. See variable PVGIS_VARIABLE_MAP.
    timeout: int, default: 60
        Time in seconds to wait for server response before timeout

    Returns
    -------
    data : pandas.DataFrame
        Time-series of hourly data, see Notes for fields
    inputs : dict
        Dictionary of the request input parameters
    metadata : dict
        Dictionary containing metadata

    Raises
    ------
    requests.HTTPError
        If the request response status is ``HTTP/1.1 400 BAD REQUEST``, then
        the error message in the response will be raised as an exception,
        otherwise raise whatever ``HTTP/1.1`` error occurred

    Hint
    ----
    PVGIS provides access to a number of different solar radiation datasets,
    including satellite-based (SARAH, CMSAF, and NSRDB PSM3) and re-analysis
    products (ERA5 and COSMO). Each data source has a different geographical
    coverage and time stamp convention, e.g., SARAH and CMSAF provide
    instantaneous values, whereas values from ERA5 are averages for the hour.

    Notes
    -----
    data includes the following fields:

    ===========================  ======  ======================================
    raw, mapped                  Format  Description
    ===========================  ======  ======================================
    *Mapped field names are returned when the map_variables argument is True*
    ---------------------------------------------------------------------------
    P†                           float   PV system power (W)
    G(i), poa_global‡            float   Global irradiance on inclined plane (W/m^2)
    Gb(i), poa_direct‡           float   Beam (direct) irradiance on inclined plane (W/m^2)
    Gd(i), poa_sky_diffuse‡      float   Diffuse irradiance on inclined plane (W/m^2)
    Gr(i), poa_ground_diffuse‡   float   Reflected irradiance on inclined plane (W/m^2)
    H_sun, solar_elevation       float   Sun height/elevation (degrees)
    T2m, temp_air                float   Air temperature at 2 m (degrees Celsius)
    WS10m, wind_speed            float   Wind speed at 10 m (m/s)
    Int                          int     Solar radiation reconstructed (1/0)
    ===========================  ======  ======================================

    †P (PV system power) is only returned when pvcalculation=True.

    ‡Gb(i), Gd(i), and Gr(i) are returned when components=True, otherwise the
    sum of the three components, G(i), is returned.

    See Also
    --------
    pvlib.iotools.read_pvgis_hourly, pvlib.iotools.get_pvgis_tmy

    References
    ----------
    .. [1] `PVGIS <https://ec.europa.eu/jrc/en/pvgis>`_
    .. [2] `PVGIS Hourly Radiation
       <https://ec.europa.eu/jrc/en/PVGIS/tools/hourly-radiation>`_
    .. [3] `PVGIS Non-interactive service
       <https://ec.europa.eu/jrc/en/PVGIS/docs/noninteractive>`_
    .. [4] `PVGIS horizon profile tool
       <https://ec.europa.eu/jrc/en/PVGIS/tools/horizon>`_
    """  # noqa: E501
    # use requests to format the query string by passing params dictionary
    params = {'lat': latitude, 'lon': longitude, 'outputformat': outputformat,
              'angle': surface_tilt, 'aspect': surface_azimuth,
              'pvcalculation': int(pvcalculation),
              'pvtechchoice': pvtechchoice, 'mountingplace': mountingplace,
              'trackingtype': trackingtype, 'components': int(components),
              'usehorizon': int(usehorizon),
              'optimalangles': int(optimalangles),
              'optimalinclination': int(optimal_surface_tilt), 'loss': loss}
    # pvgis only takes 0 for False, and 1 for True, not strings
    if userhorizon is not None:
        params['userhorizon'] = ','.join(str(x) for x in userhorizon)
    if raddatabase is not None:
        params['raddatabase'] = raddatabase
    if start is not None:
        params['startyear'] = start if isinstance(start, int) else start.year
    if end is not None:
        params['endyear'] = end if isinstance(end, int) else end.year
    if peakpower is not None:
        params['peakpower'] = peakpower

    # The url endpoint for hourly radiation is 'seriescalc'
    res = requests.get(url + 'seriescalc', params=params, timeout=timeout)
    # PVGIS returns really well formatted error messages in JSON for HTTP/1.1
    # 400 BAD REQUEST so try to return that if possible, otherwise raise the
    # HTTP/1.1 error caught by requests
    if not res.ok:
        try:
            err_msg = res.json()
        except Exception:
            res.raise_for_status()
        else:
            raise requests.HTTPError(err_msg['message'])

    return read_pvgis_hourly(io.StringIO(res.text), pvgis_format=outputformat,
                             map_variables=map_variables)

def read_pvgis_hourly(filename, pvgis_format=None, map_variables=True):
    """Read a PVGIS hourly file.

    Parameters
    ----------
    filename : str, pathlib.Path, or file-like buffer
        Name, path, or buffer of hourly data file downloaded from PVGIS.
    pvgis_format : str, default None
        Format of PVGIS file or buffer. Equivalent to the ``outputformat``
        parameter in the PVGIS API. If ``filename`` is a file and
        ``pvgis_format`` is ``None`` then the file extension will be used to
        determine the PVGIS format to parse. If ``filename`` is a buffer, then
        ``pvgis_format`` is required and must be in ``['csv', 'json']``.
    map_variables: bool, default True
        When true, renames columns of the DataFrame to pvlib variable names
        where applicable. See variable PVGIS_VARIABLE_MAP.

    Returns
    -------
    data : pandas.DataFrame
        the time series data
    inputs : dict
        the inputs
    metadata : dict
        metadata

    Raises
    ------
    ValueError
        if ``pvgis_format`` is ``None`` and the file extension is neither
        ``.csv`` nor ``.json`` or if ``pvgis_format`` is provided as
        input but isn't in ``['csv', 'json']``
    TypeError
        if ``pvgis_format`` is ``None`` and ``filename`` is a buffer

    See Also
    --------
    get_pvgis_hourly, read_pvgis_tmy
    """
    # get the PVGIS outputformat
    if pvgis_format is None:
        # get the file extension from suffix, but remove the dot and make sure
        # it's lower case to compare with csv, or json
        # NOTE: basic format is not supported for PVGIS Hourly as the data
        # format does not include a header
        # NOTE: raises TypeError if filename is a buffer
        outputformat = Path(filename).suffix[1:].lower()
    else:
        outputformat = pvgis_format

    # parse the pvgis file based on the output format, either 'json' or 'csv'
    # NOTE: json and csv output formats have parsers defined as private
    # functions in this module

    # JSON: use Python built-in json module to convert file contents to a
    # Python dictionary, and pass the dictionary to the
    # _parse_pvgis_hourly_json() function from this module
    if outputformat == 'json':
        try:
            src = json.load(filename)
        except AttributeError:  # str/path has no .read() attribute
            with open(str(filename), 'r') as fbuf:
                src = json.load(fbuf)
        return _parse_pvgis_hourly_json(src, map_variables=map_variables)

    # CSV: use _parse_pvgis_hourly_csv()
    if outputformat == 'csv':
        try:
            pvgis_data = _parse_pvgis_hourly_csv(
                filename, map_variables=map_variables)
        except AttributeError:  # str/path has no .read() attribute
            with open(str(filename), 'r') as fbuf:
                pvgis_data = _parse_pvgis_hourly_csv(
                    fbuf, map_variables=map_variables)
        return pvgis_data

    

    # raise exception if pvgis format isn't in ['csv', 'json']
    err_msg = (
        "pvgis format '{:s}' was unknown, must be either 'json' or 'csv'")\
        .format(outputformat)
    raise ValueError(err_msg)

def _parse_pvgis_hourly_json(src, map_variables):
    inputs = src['inputs']
    metadata = src['meta']
    data = pd.DataFrame(src['outputs']['hourly'])
    data.index = pd.to_datetime(data['time'], format='%Y%m%d:%H%M') #, utc=True)
    data = data.drop('time', axis=1)
    data = data.astype(dtype={'Int': 'int'})  # The 'Int' column to be integer
    if map_variables:
        data = data.rename(columns=PVGIS_VARIABLE_MAP)
    return data, inputs, metadata

def _parse_pvgis_hourly_csv(src, map_variables):
    # The first 4 rows are latitude, longitude, elevation, radiation database
    inputs = {}
    # 'Latitude (decimal degrees): 45.000\r\n'
    inputs['latitude'] = float(src.readline().split(':')[1])
    # 'Longitude (decimal degrees): 8.000\r\n'
    inputs['longitude'] = float(src.readline().split(':')[1])
    # Elevation (m): 1389.0\r\n
    inputs['elevation'] = float(src.readline().split(':')[1])
    # 'Radiation database: \tPVGIS-SARAH\r\n'
    inputs['radiation_database'] = src.readline().split(':')[1].strip()
    # Parse through the remaining metadata section (the number of lines for
    # this section depends on the requested parameters)
    while True:
        line = src.readline()
        if line.startswith('time,'):  # The data header starts with 'time,'
            # The last line of the metadata section contains the column names
            names = line.strip().split(',')
            break
        # Only retrieve metadata from non-empty lines
        elif line.strip() != '':
            inputs[line.split(':')[0]] = line.split(':')[1].strip()
        elif line == '':  # If end of file is reached
            raise ValueError('No data section was detected. File has probably '
                             'been modified since being downloaded from PVGIS')
    # Save the entries from the data section to a list, until an empty line is
    # reached an empty line. The length of the section depends on the request
    data_lines = []
    while True:
        line = src.readline()
        if line.strip() == '':
            break
        else:
            data_lines.append(line.strip().split(','))
    data = pd.DataFrame(data_lines, columns=names)
    data.index = pd.to_datetime(data['time'], format='%Y%m%d:%H%M') #, utc=True)
    data = data.drop('time', axis=1)
    if map_variables:
        data = data.rename(columns=PVGIS_VARIABLE_MAP)
    # All columns should have the dtype=float, except 'Int' which should be
    # integer. It is necessary to convert to float, before converting to int
    data = data.astype(float).astype(dtype={'Int': 'int'})
    # Generate metadata dictionary containing description of parameters
    metadata = {}
    for line in src.readlines():
        if ':' in line:
            metadata[line.split(':')[0]] = line.split(':')[1].strip()
    return data, inputs, metadata