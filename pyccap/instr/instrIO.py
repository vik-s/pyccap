"""
Module to handle GPIB IO commands
"""
import pyvisa

def initialize(self, visa_name):
    rm = pyvisa.ResourceManager()
    self.pyvisa = rm.open_resource(visa_name)
    self.pyvisa.timeout = None
    self.pyvisa.read_termination = '\n'

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
    return self.pyvisa.query_ascii_values(message)

def query_bin(self, message):
    """
    Query binary values
    """
    return self.pyvisa.query_ascii_values(message)

def query(self, message):
    """
    Query values
    """
    return self.pyvisa.query(message)

def read(self, message):
    """
    Read values
    """
    return self.pyvisa.query(message)
