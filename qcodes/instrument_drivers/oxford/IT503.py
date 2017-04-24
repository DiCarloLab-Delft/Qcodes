from qcodes import Instrument, VisaInstrument, validators as vals
from qcodes.instrument import visa as visa_mod

class OxfordInstruments_IT503(Instrument):

    def __init__(self, name, address, **kw):
        super().__init__(name, **kw)
        self._instr_instance = visa_mod.VisaInstrument('IT503_sub',
        	                                           address=address,
        	                                           terminator='\r')
        self.add_parameter(name='sorb',
                           label='SORB',
                           unit='K',
                           get_cmd=lambda : self._get_temp(1),
                           get_parser=float,
                           vals=vals.Numbers(0., 1e3))
        self.add_parameter(name='ROX',
                           label='ROX',
                           unit='K',
                           get_cmd=lambda : self._get_temp(2),
                           get_parser=float,
                           vals=vals.Numbers(0., 1e3))
        self.add_parameter(name='CERNOX',
                           label='CERNOX',
                           unit='K',
                           get_cmd=lambda : self._get_temp(3),
                           get_parser=float,
                           vals=vals.Numbers(0., 1e3))

    def _get_temp(self, channel):
    	msg = self._instr_instance.ask('R%d'%channel)
    	return float(msg[1:])

