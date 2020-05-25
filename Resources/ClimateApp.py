import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# For queries with no station assume the most active station as default
session = Session(engine)
default_station = session \
    .query(Measurement.station, func.count(Measurement.station)) \
    .group_by(Measurement.station) \
    .order_by(func.count(Measurement.station).desc()) \
    .first()[0]
session.close()

# Date format for date manipulations
d_format = '%Y-%m-%d'

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
"""
<ul>
<li>/ Home [this] page.</li>
<li><a href="/api/v1.0/precipitation">/api/v1.0/precipitation</a></li>
<li><a href="/api/v1.0/stations">/api/v1.0/stations</a></li>
<li><a href="/api/v1.0/tobs">/api/v1.0/tobs</a></li>
<li><a href="/api/v1.0/2017-02-23">/api/v1.0/&lt;start&gt;</a></li>
<li><a href="/api/v1.0/2017-02-23/2017-03-23">/api/v1.0/&lt;start&gt;/&lt;end&gt;</a></li>
</ul>
"""
    )


#Convert the query results to a dictionary using date as the key and prcp as the value.
#Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # No date requirements in the assignment? OK. Otherwise could be done like tobs()
    results = session.query(Measurement.date, Measurement.prcp) \
        .filter(Measurement.station == default_station) \
        .order_by(Measurement.date) \
        .all()

    session.close()

    # Convert list of tuples into normal list
    all_names = dict(results)

    return jsonify(all_names)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all stations
    results = session.query(Station.station, Station.name).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_stations
    all_stations = []
    for station, name in results:
        station_dict = {}
        station_dict["name"] = name
        station_dict["station"] = station
        all_stations.append(station_dict)

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query the last 12 months of temperature observation data for this station and plot the results as a histogram
    first_month = session.query(
        func.strftime(d_format,
        func.date(func.max(Measurement.date), '-1 year')
    )).filter(Measurement.station == default_station).first()[0]
    last_month = session.query(
        func.strftime(d_format,
        func.max(Measurement.date)
    )).filter(Measurement.station == default_station).first()[0]

    # Perform a query to retrieve the data and precipitation scores
    # We take the max(date) so the last month can be incomplete month, let's exclude it
    sel = [func.strftime(d_format, Measurement.date), func.avg(Measurement.tobs)]
    results = session.query(*sel).\
        filter(func.strftime(d_format, Measurement.date) >= first_month).\
        filter(func.strftime(d_format, Measurement.date) <  last_month).\
        filter(Measurement.station == default_station). \
        group_by(func.strftime(d_format, Measurement.date)).\
        order_by(func.strftime(d_format, Measurement.date)).\
        all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_stations
    all_tobs = []
    for date, temperature in results:
        one_dict = {}
        one_dict["date"] = date
        one_dict["temperature"] = temperature
        all_tobs.append(one_dict)

    return jsonify(all_tobs)

# This function called `calc_temps` will accept start date and end date in the format '%Y-%m-%d' 
# and return the minimum, average, and maximum temperatures for that range of dates
def calc_temps(session, start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).\
        filter(Measurement.date <= end_date).\
        filter(Measurement.station == default_station).\
        first()

@app.route("/api/v1.0/<start_date>/<end_date>")
def temp_stats(start_date, end_date):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    ret_list = calc_temps(session, start_date, end_date)
    session.close()
    ret_object = {
        "min_temp": ret_list[0],
        "avg_temp": ret_list[1],
        "max_temp": ret_list[2]
    }
    return jsonify(ret_object)

@app.route("/api/v1.0/<start_date>")
def temp_stats_opendate(start_date):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    end_date = session.query(
        func.strftime(d_format, func.max(Measurement.date))
    ).filter(Measurement.station == default_station).first()[0]
    session.close()
    return temp_stats(start_date, end_date)


if __name__ == '__main__':
    app.run(debug=True)
