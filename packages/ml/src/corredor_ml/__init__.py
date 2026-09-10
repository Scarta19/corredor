"""Modelling library for the Corredor platform.

Kept deliberately free of FastAPI, SQLAlchemy and any database import: models
take feature objects and return prediction objects, which is what makes them
testable offline, trainable in a notebook and callable from a worker without
dragging a web application along.
"""

__version__ = "0.1.0"
