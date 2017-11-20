from qcodes import VisaInstrument
from qcodes.utils.validators import Strings, Enum
from qcodes import VisaInstrument, validators as vals


class Keithley_2200(VisaInstrument):
    """
    QCoDeS driver for the Keithley 2200 current source.
    """
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        self.add_parameter('trigger',
                           get_cmd='*TRG',
                           label='Trigger list/fixed measurement')

        self.add_parameter('status',
                           get_cmd=':OUTP:STAT?',
                           set_cmd=self.set_status,
                           get_parser=self.parse_on_off,
                           vals=vals.Strings())

        self.add_parameter('fetchi',
                           get_cmd='FETC:CURR?',
                           get_parser=float,
                           label='Current',
                           unit='A')

        self.add_parameter('fetchv',
                           get_cmd='FETC:VOLT?',
                           get_parser=float,
                           label='Voltage',
                           unit='V')

        self.add_parameter('fetchp',
                           get_cmd='FETC:POW?',
                           get_parser=float,
                           label='Power',
                           unit='W')

        self.add_parameter('measurei',
                           get_cmd='MEAS:CURR?',
                           get_parser=float,
                           label='Execute current measurement',
                           unit='A')

        self.add_parameter('measurev',
                           get_cmd='MEAS:VOLT?',
                           get_parser=float,
                           label='Execute voltage measurement',
                           unit='V')

        self.add_parameter('resistance',
                           get_cmd=self.measureR,
                           get_parser=float,
                           label='Execute resistance measurement',
                           unit='Ohm')

        self.add_parameter('seti',
                           get_cmd='CURR?',
                           get_parser=float,
                           set_cmd='CURR {:f}A', # {<current>|MIN|MAX|DEF} (one element required)
                           label='Set current',
                           unit='A')

        self.add_parameter('setv',
                           get_cmd='VOLT?',
                           get_parser=float,
                           set_cmd='VOLT {:f}V', # {<current>|MIN|MAX|DEF} (one element required)
                           label='Set voltage',
                           unit='V')

        self.add_parameter('rangev',
                           get_cmd='VOLTage:RANGe?',
                           get_parser=float,
                           set_cmd='VOLTage:RANGe {:f}',
                           unit='V')

        self.add_parameter('command_mode',
                           get_cmd='FUNCtion:MODE?',
                           get_parser= str,
                           set_cmd='FUNCtion:MODE "{:s}"', # {FIXed|LIST}
                           set_parser = str,
                           label='Set mode to FIXed or LIST')

        self.add_parameter('list_repeats',
                           get_cmd='LIST:COUNt?',
                           get_parser=float,
                           set_cmd='LIST:COUNt {}', # {<NR1>|ONCE|REPeat}
                           set_parser = int or str,
                           label='Set repeats to amount or ONCE or REPeat (continuously)')

        self.add_parameter('step_duration',
                           get_cmd='LIST:WIDth? {:f}',
                           # get_parser=float,
                           set_cmd='LIST:WIDth {:f}, {:f}', # <NR1>,{<duration>|MIN|MAX}
                           label='Set step duration')

        self.add_parameter('no_of_steps',
                           get_cmd='LIST:STEP?',
                           get_parser=float,
                           set_cmd='LIST:STEP {:f}', # {<NR1>|MIN|MAX}
                           label='Set # of steps') # max is 80

        self.add_parameter('liststepi',
                           get_cmd='LIST:CURR?',
                           get_parser=float,
                           set_cmd='LIST:CURR {:f}', # <NR1>,<current> = step no., value
                           label='Set current for a list step',
                           unit='A')

        self.add_parameter('liststepv',
                           get_cmd='LIST:VOLT?',
                           get_parser=float,
                           set_cmd='LIST:VOLT {:f}', # <NR1>,<voltage> = step no., value
                           label='Set voltage for a list step',
                           unit='V')


    def parse_on_off(self, stat):
        if stat.startswith('0'):
            stat = 'Off'
        elif stat.startswith('1'):
            stat = 'On'
        return stat

    def set_status(self, stat):
        if stat.upper() in ('ON', 'OFF'):
            self.write(':OUTP:STAT %s' % stat)
        else:
            raise ValueError('Unable to set status to %s, ' % stat +
                             'expected "ON" or "OFF"')

    def measureR(self):
        if self.seti() == 0:
            return 0
        if self.measurei() == 0:
            return 1e9
        R = self.measurev()/self.measurei()
        return R