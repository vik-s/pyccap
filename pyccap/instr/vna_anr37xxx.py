"""
.. module vna_anr37xxx.py
.. moduleauthor:: Vikram Sekar <vikram.mail@gmail.com>

"""

import pyvisa
import sys
import numpy as np
from . import instrIO as io
import time
import skrf as rf

class vna_anr37xxx():
    """
    Device driver for Anritsu 37XXX Vector Network Analyzer

    Provides the necessary methods to configure and collect measurement
    data using the Anritsu 37XXX VNA.

    """
    def __init__(self,visa_name):
        """
        Initialization method for analyzer.

        Device object requires pyvisa and NI backend installed.

        Parameters
        ----------
            visa_name : str
                Visa resource ID. Ex: GPIB0::6::INSTR

        >>> dc = pyccap.instr.vna_anr37xxx('GPIB0::6::INSTR')
        """
        io.initialize(self, visa_name)
        print('WARNING: VNA must have a valid calibration')

    @property
    def frequency(self):
        """
        Get frequency settings from instrument

        Returns start frequency, stop frequency and number of steps

        Returns
        ----------
        start : float
            Start Frequency
        stop : float
            Stop Frequency
        npoints : int
            number of points

        >>> vna.frequency
        """
        qry = io.query(self, 'SRT?; STP?; ONDF')
        qry = qry.split(';')
        start = float(qry[0]); stop = float(qry[1]); npoints = int(qry[2])
        return start, stop, npoints

    @frequency.setter
    def frequency(self, frq):
        """
        Set Frequency Sweep

        Set the frequency start and stop range using discrete values

        Parameters
        ----------
        frq : numpy array
            Array of frequency points

        >>> vna.frequency = numpy.linspace(1,40,40)
        """
        # Check to see if frq is of type np.ndarray and then configure freq
        try:
            frq = str(frq.tolist())
        except TypeError:
            print('Frequency vector must be of type numpy.ndarray')
        else:
            frq = frq.replace("[","").replace("]","")
            io.write(self, 'IFV #0 '+frq)

    @property
    def power(self):
        """
        Get port power level

        Returns
        ----------
        power : float
            Port power value

        >>> vna.power
        """
        qry = self.pyvisa.query('PWR?')
        return float(qry)

    @power.setter
    def power(self, pwr):
        """
        Set port power level

        Set the input port power level to be between -30 dBm and 0 dBm.

        Parameters
        ----------
        pwr : float
            Port power value

        >>> vna.power = -10
        """
        # Input power level is expected to be between -30dBm and 0dBm
        try:
            if -30 <= pwr <= 0:
               pass
            else:
               print('Source power level must be between -30 dBm and 0 dBm.')
        except TypeError:
            print('Power input must be a numeric value in dBm.')
        else:
            io.write(self, 'PWR '+str(pwr)+' DB')

    @property
    def attenuation(self):
        """
        Get attenuation levels of each Port

        Returns
        ----------
        att1 : int
            Port 1 Attenuation
        att2 : int
            Port 2 Attenuation

        >>> vna.attenuation
        """
        qry = io.query(self, 'SA1?; TA2?')
        qry = qry.split(';')
        att1 = int(qry[0]); att2 = int(qry[1])
        return att1, att2

    @attenuation.setter
    def attenuation(self, att1 = 0, att2 = 0):
        """
        Set attenuation levels

        Set port 1 and port 2 attenuatiomn levels. Default = 0 dB.
        Should be between 0 dB and 70 dB in steps of 10 dB.

        Parameters
        ----------
        att1 : int
            Port 1 Attenuation
        att2 : int
            Port 2 Attenuation

        >>> vna.attenuation(att1 = 10, att2 = 0)
        """
        # Attenuation level should be between 0dB and 70dB in steps of 10dB
        try:
            ValChk = (0 <= att1 <= 70, 0 <= att2 <= 40)
            MulChk = (att1 % 10, att2 % 10)
            if (all(x == True for x in ValChk) & all(x == 0 for x in MulChk)):
                pass
            else:
                print('Attenuation must be between 0 dB and 70/40 dB (P1/P2) in multiples of 10 dB.')
        except TypeError:
            print('Attenuation must be a positive number in dB.')
        else:
            io.write(self, 'SA1 '+str(att1)+';'+'TA2 '+str(att2))

    @property
    def ifbandwidth(self):
        """
        Get IF Bandwidth

        Returns
        ----------
        ifbw : string
            Returns IF Bandwidth as string value.
            10Hz, 100Hz, 1kHz, or 10kHz.

        >>> vna.ifbandwidth
        """
        ifdict2 = {1.0:'10Hz', 2.0:'100Hz', 3.0:'1kHz', 4.0:'10kHz'}
        ifbw = float(io.query(self, 'IFX?'))
        ifbw = ifdict2[ifbw]
        return ifbw

    @ifbandwidth.setter
    def ifbandwidth(self, ifbw):
        """
        Set IF Bandwidth

        Sets the IF Bandwidth of the measurement

        Parameters
        ----------
        ifbw : str
            IF Bandwidth string value.
            Use 10Hz, 100Hz, 1kHz, or 10kHz.

        >>> vna.ifbandwidth(ifbw = '10Hz')
        """
        ifdict = {'10Hz':'IF1', '100Hz':'IF2', '1kHz':'IF3', '10kHz':'IF4'}
        try:
            ifcode = ifdict[ifbw]
        except KeyError:
            print('IF Bandwidth code is invalid. Use 10Hz, 100Hz, 1kHz, or 10kHz.')
        else:
            io.write(self, ifcode)

    def summary(self):
        """
        Provides a summary of the VNA settings

        Parameters
        ----------
        None

        Returns
        -------
        summary
            Summary of all current VNA configuration

        >>> vna.summary()
        """
        # Get current time
        time_qry = str(datetime.datetime.now())
        # Get frequency information
        start, stop, npoints = self.frequency
        frq_qry = 'Frequency range is from {} GHz to {} GHz in {} steps'.format(start/1e9, stop/1e9, npoints)
        # Get source power information
        pwr_qry = 'Source power level is {} dBm'.format(self.power)
        # Get IF bandwidth
        if_qry = 'IF Bandwidth is {}'.format(self.ifbandwidth)
        # Get attenuation levels
        att1, att2 = self.attenuation
        att_qry1 = 'Source attenuation level is {} dB'.format(att1)
        att_qry2 = 'Receiver attenuation level is {} dB'.format(att2)
        # Create summary
        summary = '! ' + time_qry + '\n' + '! ' + frq_qry + '\n' + '! ' + pwr_qry + '\n' + '! ' + if_qry + '\n' + '! ' + att_qry1 + '\n' + '! ' + att_qry2 + '\n'
        return summary

    def meas(self, name = 'vna-meas'):
        '''
        Performs an s-parameter measurement

        Parameters
        ----------
            name : str
                name of rf.Network object created from measurement
        '''
        # Set measurement and displays
        io.write(self, 'CH1;S11;SMI;CH2;S12;PLR;CH3;S21;PLR;CH4;S22;SMI')
        # Set RF off and Bias off while in hold
        io.write(self, 'BH0; RH0')
        # Take measurement
        io.write(self, 'HLD;TRS;WFS;TRS;WFS')
        # Get freq, sparameter data
        npoints = io.query(self, 'ONP')
        frq = io.query_binary_values(self, 'FMC;OFV')
        frq = np.array(frq)*1e-9

        io.write(self, 'CH1')
        s11 = io.query_binary_values(self, 'FMC;OCD')
        s11 = np.array(s11)
        s11 = s11[::2] + 1j * s11[1::2]
        io.write(self, 'CH2')
        s12 = io.query_binary_values(self, 'FMC;OCD')
        s12 = np.array(s12)
        s12 = s12[::2] + 1j * s12[1::2]
        io.write(self, 'CH3')
        s21 = np.array(s21)
        s21 = s21[::2] + 1j * s21[1::2]
        io.write(self, 'CH4')
        s22 = io.query_binary_values(self, 'FMC;OCD')
        s22 = np.array(s22)
        s22 = s22[::2] + 1j * s22[1::2]

        # Reshape sparameters
        xx = np.dstack((s11,s12))
        yy = np.dstack((s21,s22))
        zz = np.dstack((xx,yy))
        sp = np.reshape(zz,(int(npoints),2,2))

        # Create z0 matrix
        z0 = np.array([50, 50])
        # Create network object and return it
        ntwk = rf.Network(frequency=frq, s=sp, z0=z0, name=name)
        return ntwk

'''-------------------------------------------------------------------------'''
