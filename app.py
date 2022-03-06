import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
import pandas as pd

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# relect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

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
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/[start]<br/>"
        f"/api/v1.0/[start]/[end]"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    #Create a session (link) from Python to the DB
    session = Session(engine)

    """Return a list of precipitation data including the date and measurement"""
    
    # query for 1 year date
    recent = session.query(Measurement.date).order_by((Measurement.date).desc()).first()[0]
    startDate = dt.datetime.strptime(recent,"%Y-%m-%d").date()
    endDate = startDate - dt.timedelta(days=365)

    # query precipitation
    results = session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date > endDate).\
    order_by((Measurement.date).desc()).all()

    session.close()

    # Create a dictionary
    precipitation = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["Precipitation"] = prcp
        precipitation.append(prcp_dict)

    return jsonify(precipitation)

@app.route("/api/v1.0/stations")
def stations():
    #Create a session (link) from Python to the DB
    session = Session(engine)
    
    # query stations and include count of measurements
    results = session.query(
        Measurement.station,
        Station.name,
        Station.elevation,
        Station.latitude,
        Station.longitude,
        func.count(Measurement.station)
        ).\
        group_by(Measurement.station).\
        order_by((func.count(Measurement.station)).desc()).all()

    session.close()

    """Return a list of stations"""
    # Create a dictionary
    stations = []
    for station, name, elevation, latitude, longitude, measurementCount in results:
        stations_dict = {}
        stations_dict["station"] = station
        stations_dict["name"] = name
        stations_dict["elevation"] = elevation
        stations_dict["latitude"] = latitude
        stations_dict["longitude"] = longitude
        stations_dict["measurementCount"] = measurementCount
        stations.append(stations_dict)

    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    #Create Session
    session = Session(engine)

    # query dates and temps for most active station lasy year of data
    #get most active station
    station_mostActive = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).\
    order_by((func.count(Measurement.station)).desc()).first()[0]

    # query for 1 year
    recent = session.query(Measurement.date).order_by((Measurement.date).desc()).first()[0]
    startDate = dt.datetime.strptime(recent,"%Y-%m-%d").date()
    endDate = startDate - dt.timedelta(days=365)

    #get results for most active station
    results = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.date > endDate).\
    filter(Measurement.station == station_mostActive).all()

    session.close()

    # Create a dictionary
    all_tobs = []
    for date, tobs in results:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["temperature"] = tobs
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)

@app.route("/api/v1.0/<start>")
def start(start):
    # Create session
    session = Session(engine)

    #get most active station
    station_mostActive = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).\
    order_by((func.count(Measurement.station)).desc()).first()[0]

    #query for only start date
    start_df = pd.DataFrame(session.query(Measurement.tobs).\
    filter(Measurement.date >= start).\
    filter(Measurement.station == station_mostActive).all(), columns=['tobs'])

    summary_dict = {}
    summary_dict["Min Temp"] = start_df.min()[0]
    summary_dict["Max Temp"] = start_df.max()[0]
    summary_dict["Avg Temp"] = start_df.mean()[0]

    return jsonify(summary_dict)

@app.route("/api/v1.0/<start>/<end>")
def startend(start,end):
    # Create session
    session = Session(engine)

    #get most active station
    station_mostActive = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).\
    order_by((func.count(Measurement.station)).desc()).first()[0]

    #query for only start date
    start_df = pd.DataFrame(session.query(Measurement.tobs).\
    filter(Measurement.date >= start).\
    filter(Measurement.date < end).\
    filter(Measurement.station == station_mostActive).all(), columns=['tobs'])

    summary_dict = {}
    summary_dict["Min Temp"] = start_df.min()[0]
    summary_dict["Max Temp"] = start_df.max()[0]
    summary_dict["Avg Temp"] = start_df.mean()[0]

    return jsonify(summary_dict)

if __name__ == '__main__':
    app.run(debug=True)
