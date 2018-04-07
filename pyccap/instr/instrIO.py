"""
Module to handle GPIB IO commands
"""
import pyvisa

def write(self, message):
    """
    Write into instrument
    """
    self.pyvisa.write(message)
    #print(message)
    #self.report_any_errors()

def query_asc(self, message):
    """
    Query ASCII values
    """
    self.pyvisa.query_ascii_values(message)

def query_bin(self, message):
    """
    Query binary values
    """
    self.pyvisa.query_ascii_values(message)

def query(self, message):
    """
    Query values
    """
    self.pyvisa.query(message)

def read(self, message):
    """
    Read values
    """
    self.pyvisa.query(message)
