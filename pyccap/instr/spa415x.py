"""
.. module spa415x.py
.. moduleauthor:: Vikram Sekar <vikram.mail@gmail.com>

"""

import pyvisa
import sys
import numpy as np
from . import instrIO as io

class spa415x():
    """
    Device driver for Agilent 4155/4156

    Provides the necessary methods to configure and collect measurement
    data using the Agilent 4155/4156 Semiconductor Parameter Analyzer (SPA).

    """
    def __init__(self, visa_name):
        """
        Initialization method for analyzer.

        Device object requires pyvisa and NI backend installed.

        Parameters
        ----------
            visa_name : str
                Visa resource ID. Ex: GPIB0::25::INSTR

        >>> dc = pyccap.instr.spa415x('GPIB0::25::INSTR')
        """
        io.initialize(self, visa_name)

    @property
    def mode(self):
        """
        Operating Mode Property

        Queries the analyzer to check sweep or sampling state.

        Returns
        -------
        str
            SWE - for sweep mode
            SAMP - for sampling mode

        >>> dc.mode
        'SWE'
        """
        return io.query(self, ':PAGE:CHANnels:MODE?')

    @mode.setter
    def mode(self, mode):
        """
        Set Operating Mode

        Sets the operating mode of the analyzer as sweep or sampling

        Parameters
        ----------
        mode : str
            Allowed inputs are 'sweep' or 'sampling'

        >>> dc.mode = 'sweep'
        """
        modedict = {'sweep':'SWEep', 'sampling':'SAMPling'}
        try:
            op_mode = modedict[mode]
        except KeyError:
            print('Invalid mode. Use sweep or sampling.')
        else:
            io.write(self, ':PAGE:CHANnels:MODE '+op_mode)

    @property
    def data_variables(self):
        """
        List of Data Variables

        Gets a string list of data variables for whom measured data
        is available.

        >>> dc.data_variables
        ['V1', 'I1', 'V2', 'I2', 'V3', 'I3', 'V4', 'I4']
        """
        dlist = io.query(self, ':PAGE:DISP:LIST?').split(',')
        dvar = io.query(self, ':PAGE:DISP:DVAR?').split(',')
        return dlist + dvar

    def __get_meas_data(self, var):
        """
        Get measurement data for variable

        Private Method:
        The string identifying voltage or current on channel is passed in as
        arguement, and the data for that quantity is obtained from instrumentself.

        Parameters
        ----------
        var : str
            String identifying voltage or current quantity on channel

        Returns
        -------
        float
            List of voltage or current values for each independent sweep var
        """
        io.write(self, ':FORM:DATA ASC')
        return io.query_asc(self, ':DATA? '+var)

    def __get_meas_data_matrix(self):
        """
        Arrange all measured data into a matrix

        Private Method:
        Uses column_stack from numpy to arrange all measured quantities as
        columns on a numpy array.

        Parameters
        ----------
        None

        Returns
        -------
        numpy array
            Contains all measured quantities from analyzer
        """
        for i, listvar in enumerate(self.data_variables):
            data = np.array(self.__get_meas_data(listvar))
            if i == 0:
                lastdata = data
            else:
                data = np.column_stack((lastdata, data))
                lastdata = data
        return data

    def __get_error(self):
        """
        Check for system error

        Private Method:
        Retrives the error code and error message from instrument.

        Parameters
        ----------
        None

        Returns
        -------
        int, str
            error code, error message
        """
        err = io.query(self, ':SYSTem:ERRor?')
        err = err.split(',')

        err_num = int(err[0])

        err_mess = err[1].replace('\"', '')
        return err_num, err_mess

    def report_any_errors(self):
        err_num, err_mess  = self.__get_error()
        print(str(err_num) + ': ' + err_mess)

    def config(self, ch, func, vname, iname='I', outmode='V'):
        """
        Configures operating properties of the SMU channel

        Parameters
        ----------
        ch : str
            String identifying channel on Analyzer
            Allowed inputs : smu1 | smu2 | smu3 | smu4 | vsu1 | vsu2 | vmu1 | vmu2
        func : str
            Sets the function of the SMU
            Allowed inputs : var1 | var2 | vard | constant
        vname : str
            Voltage name on specified channel; must be unique to each channel.
        iname : str
            Current name on specified channel; must be unique to each channel.
        outmode : str
            Output operating mode of the channel
            Allowed inputs : v | i | vpulse | ipulse | common

        Returns
        -------
        None

        Raises
        ------
        KeyError, Exception
        """

        ch = ch.upper()
        funcdict = {'var1':'VAR1', 'var2':'VAR2', 'vard':'VARD','constant':'CONStant'}
        modedict = {'v':'V', 'i':'I', 'vpulse':'VPULse', 'ipulse':'IPULse', 'common':'COMMon'}
        func = func.lower()
        outmode = outmode.lower()

        try:
            outmode = modedict[outmode]
        except KeyError:
            print('Invalid channel mode. Use v, i, vpulse, ipulse or common.')
        else:
            io.write(self, ':PAGE:CHANnels:'+ch+':MODE '+outmode)

        if(outmode.lower() is 'common'):
            pass
        else:
            try:
                func = funcdict[func]
            except KeyError:
                print('Invalid channel function. Use var1, var2, vard or constant.')
            else:
                try:
                    'VMU' not in ch
                except ValueError:
                    print('Cannot set channel function for VMU.')
                else:
                    io.write(self, ':PAGE:CHAN:'+ch+':FUNC '+func)
        # self.io.write channel names and save it for list display
        io.write(self, ':PAGE:DISP:MODE LIST')
        io.write(self, ':PAGE:CHANnels:'+ch+':VNAMe '+"'"+vname+"'")
        io.write(self, ':PAGE:DISP:LIST '+"'"+vname+"'")

        if ('VMU' in ch):
            io.write(self, 'PAGE:DISP:DVAR '+"'"+vname+"'")
        else:
            io.write(self, ':PAGE:CHANnels:'+ch+':INAMe '+"'"+iname+"'")
            io.write(self, ':PAGE:DISP:LIST '+"'"+iname+"'")

    def setup(self,ch='smu1',start=0,stop=1,step=0.1,spacing='linear',constval=0,ratio=1,offset=0,compl=0):
        """
        Configures operating properties of the channel

        Parameters
        ----------
        ch : str
            String identifying channel on Analyzer
            Allowed inputs : smu1 | smu2 | smu3 | smu4 | vsu1 | vsu2 | vmu1 | vmu2
        start : float
            Sweep start value
        stop : float
            Sweep end value
        step : float
            Sweep step value
        spacing : str
            Spacing of step values for VAR1 only.
            Allowed inputs : linear | log10 | log20 | log50
        constval : float
            Constant value. Can be used for constant value in sweep or
            sampling mode.
        ratio : float
            Ratio of current quantity to that of VAR1 when in VARD mode
        offset : float
            Offset of current quantity to that of VAR1 when in VARD mode
        compl : float
            Compliance of current or voltage on analyzer channel

        Returns
        -------
        None

        Raises
        ------
        KeyError, Exception

        >>> dc.setup(ch='smu1', start=0, stop=1, step=0.1, spacing='linear', compl=100e-3)
        >>> dc.setup(ch='smu2', start=0, stop=1, step=0.1, compl=100e-3)
        >>> dc.setup(ch='smu3', constval=1, compl=100e-3)
        >>> dc.setup(ch='smu4', constval=0, compl=100e-3)

        """
        # Define set of methods that create the right SCPI command to set channel sweep based on channel function
        def __setswp_const(val,cmp):
            cmd = ':PAGE:MEASure:CONStant:'+ch +':SOURce '+str(val)+';COMPliance '+str(cmp)
            return cmd
        def __setswp_var1(srt,end,stp,spc,cmp):
            cmd = ':PAGE:MEASure:VAR1:STARt '+str(srt)+';STOP '+str(end)+';STEP '+str(stp)+';SPACing '+spc+';COMPliance '+str(cmp)
            return cmd
        def __setswp_var2(srt,end,stp,cmp):
            pts = int((end-srt)/stp + 1)
            cmd = ':PAGE:MEASure:VAR2:STARt '+str(srt)+';POINts '+str(pts)+';STEP '+str(stp)+';COMPliance '+str(cmp)
            return cmd
        def __setswp_vard(rto,ofs,cmp):
            cmd = ':PAGE:MEASure:VARD:RATio '+str(rto)+';OFFSet '+str(ofs)+';COMPliance '+str(cmp)
            return cmd

        spacing_dict = {'linear':'LIN', 'log10':'L10', 'log20':'L20', 'log50':'L50'}
        try:
            spacing = spacing_dict[spacing]
        except KeyError:
            print('Invalid VAR1 spacing. Use linear | log10 | log20 | log50.')

        if self.mode == 'SWE':
            # Get channel mode from instrument and check if it is COMMON
            opmode = io.query(self, ':PAGE:CHANnels:'+ch+':MODE?')
            if(opmode.rstrip() != 'COMM'):
                # Get the channel function from the instrument
                getfunc = io.query(self, ':PAGE:CHANnels:'+ch+':FUNCtion?')
                # Set sweep parameter by calling functions that define the SCPI command to be sent
                getcmd = {    'CONS' : __setswp_const(constval,compl),
                              'VAR1' : __setswp_var1(start,stop,step,spacing,compl),
                              'VAR2' : __setswp_var2(start,stop,step,compl),
                              'VARD' : __setswp_vard(ratio,offset,compl)
                         }
                cmdout = getcmd[getfunc.rstrip()]    # rstrip() removes the newline character
                io.write(self, cmdout)
            else:
                print('Channel '+ch+' is set to COMMON mode. Skipping sweep setup...')
        elif self.mode == 'SAMP':
            io.write(self, ':PAGE:MEASure:SAMPling:CONStant:'+ch+':SOURce '+str(constval))
            io.write(self, ':PAGE:MEASure:SAMPling:CONStant:'+ch+':COMPliance '+str(compl))
        else:
            raise Exception('SMU operating mode cannot be found.')

    def meas(self, mtime=60):
        """
        Performs a measurement

        Measurement time is only used in sampling mode to keep the outputs on
        for the specified amount of time. This is useful when the analyzer is
        used with other instruments such as VNAs to hold the output on till the
        VNA measurement is complete. This quantity is ignored in a sweep
        measurement.

        Parameters
        ----------
        mtime : float
            Measurement time in seconds (default - 60s)

        Returns
        -------
        numpy data array
            Dataset containing all the measured data variables

        Raises
        ------
        Exception

        >>> data = dc.meas() # for sweep mode
        >>> data = dc.meas(mtime=100)) # for sampling mode

        """
        if self.mode == 'SAMP':
            io.write(self, ':PAGE:MEASure:SAMPling:PERiod ' + str(mtime))
            io.write(self, ':PAGE:MEASure:SAMPling:POINts 1')
            io.write(self, ':PAGE:SCON:MEAS:SING')
            io.write(self, '*WAI')
            return self.__get_meas_data_matrix()
        elif self.mode == 'SWE':
            io.write(self, 'PAGE:SCON:MEAS:SING')
            io.write(self, '*WAI')
            return self.__get_meas_data_matrix()
        else:
            raise Exception('SMU operating mode cannot be found.')

    def disable(self, ch):
        """
        Disables an analyzer channel

        Parameters
        ----------
        ch : str
            String identifying channel on Analyzer
            Allowed inputs : smu1 | smu2 | smu3 | smu4 | vsu1 | vsu2 | vmu1 | vmu2

        """
        io.write(self, ':PAGE:CHANnels:'+ch+':DISable')

    def time(delay=0, hold=0, integ='short'):
        """
        Specifies delay, hold and integration times of analyzer

        Parameters
        ----------
        delay : float
            Measurement delay time in sec
            (min = 0.03s, max = 65s, resolution=100us)
        hold : float
            Measurement hold time in sec
            (min = 0.03s, max = 655.35s, resolution=10ms)
        integ : str
            Integration time used in measurement.
            Allowed values - short | medium | long

        """
        # Set delay time
        try:
            0 <= delay <= 65.535
        except ValueError:
            print('Delay time must be between 0 and 65 sec with a 100us resolution.')
        else:
            io.write(self, ':PAGE:MEAS:DEL {}'.format(delay))
        # Set hold time
        try:
            0 <= Hold <= 655.35
        except ValueError:
            print('Hold time must be between 0 and 655 sec with a 10ms resolution.')
        else:
            if hold==0: hold=0.03
            io.write(self, ':PAGE:MEAS:HTIME {}'.format(hold))
        # Set integration time
        itimedict = {'short':'SHOR', 'medium':'MED', 'long':'LONG'}
        integ = integ.lower()
        try:
            integ = itimedict[integ]
        except KeyError:
            print('Invalid SMU integration time. Use short, medium or long.')
        else:
            io.write(self, ':PAGE:MEAS:MSET:ITIM '+integ)

    def init(self):
        """
        Initialize instrument by setting all channels in constant and setting proper naming
        """
        self.config(ch='smu1', func='constant', vname='X1', iname='Y1', outmode='V')
        self.config(ch='smu2', func='constant', vname='X2', iname='Y2', outmode='V')
        self.config(ch='smu3', func='constant', vname='X3', iname='Y3', outmode='V')
        self.config(ch='smu1', func='var1', vname='X1', iname='Y1', outmode='V')
        self.config(ch='smu4', func='constant', vname='X4', iname='Y4', outmode='V')
        self.config(ch='vsu1', func='constant', vname='ZA')
        self.config(ch='vsu2', func='constant', vname='ZB')
        self.config(ch='vmu1', func='constant', vname='ZC')
        self.config(ch='vmu2', func='constant', vname='ZD')
'''-------------------------------------------------------------------------'''
