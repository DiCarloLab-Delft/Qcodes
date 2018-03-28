from qcodes.instrument import visa as visa_mod

class OxfordInstruments_ITC503(visa_mod.VisaInstrument):
  def __init__(self, name, address):
    super().__init__(name, address, terminator='\r')

    def parse_response(s):
      "chop off the first letter, as instrument answers 'Rx.xxx'"
      return float(s[1:])

    self.add_parameter(name='sorb',
                           label='Sorb temperature',
                           unit='K',
                           get_cmd="R1",
                           get_parser=parse_response)
    self.add_parameter(name='ROX',
                       label='ROX temperature',
                       unit='K',
                       get_cmd="R2",
                       get_parser=parse_response)
    self.add_parameter(name='CERNOX',
                       label='CERNOX temperature',
                       unit='K',
                       get_cmd="R3",
                       get_parser=parse_response)

  def get_idn(self):

      #the ITC does not have an IDN command implemented, but it has a "V" (for version) command,
      #so we fake it

      s = self.ask("V")

      import parse

      idn = parse.parse("{model} Version {firmware} (c) {vendor} {}", s).named

      idn["serial"] = None

      return idn
