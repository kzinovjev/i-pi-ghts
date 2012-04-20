"""Deals with creating the ensembles class.

Classes:
   RestartEnsemble: Deals with creating the Ensemble object from a file, and 
      writing the checkpoints.
"""

import numpy as np
from engine.ensembles import *
import engine.thermostats
import engine.barostats
from utils.inputvalue import *
from inputs.barostats import *
from inputs.thermostats import *
from utils.units import *

__all__ = ['RestartEnsemble']

class RestartEnsemble(Input):
   """Ensemble input class.

   Handles generating the appropriate ensemble class from the xml input file,
   and generating the xml checkpoint tags and data from an instance of the 
   object.

   Attributes:
      type: An optional string giving the type of ensemble to be simulated.
         Defaults to 'unknown'.
      thermostat: The thermostat to be used for constant temperature dynamics.
      barostat: The barostat to be used for constant pressure or stress
         dynamics.
      timestep: An optional float giving the size of the timestep in atomic
         units. Defaults to 1.0.
      temperature: An optional float giving the temperature in Kelvin. Defaults
         to 1.0.
      pressure: An optional float giving the external pressure in atomic units.
         Defaults to 1.0.
      stress: An optional array giving the external stress tensor in atomic
         units. Defaults to an identity array.
      fixcom: An optional boolean which decides whether the centre of mass 
         motion will be constrained or not. Defaults to False.
   """

   attribs={"type"  : (InputValue, {"dtype"   : str,
                                    "default" : "nve",
                                    "help"    : "The ensemble that will be sampled during the simulation.",
                                    "options" : ['nve', 'nvt', 'npt', 'nst']}) }
   fields={"thermostat" : (RestartThermo, {"default"   : engine.thermostats.Thermostat(),
                                           "help"      : "The thermostat for the atoms, keeps the atom velocity distribution at the correct temperature."} ),
           "barostat" : (RestartBaro, {"default"       : engine.barostats.Barostat(),
                                       "help"          : "The barostat for the simulation."} ), 
           "timestep": (InputValue, {"dtype"         : float,
                                     "default"       : "1.0",
                                     "help"          : "The time step.",
                                     "dimension"     : "time"}),
           "temperature" : (InputValue, {"dtype"     : float, 
                                         "default"   : 1.0,
                                         "help"      : "The temperature of the system.",
                                         "dimension" : "temperature"}),
           "pressure" : (InputValue, {"dtype"        : float,
                                      "default"      : "1.0",
                                      "help"         : "The external pressure.",
                                      "dimension"    : "pressure"}),
           "stress" : (InputArray, {"dtype"          : float, 
                                    "default"        : np.identity(3),
                                    "help"           : "The external stress.",
                                    "dimension"      : "pressure"}), 
           "fixcom": (InputValue, {"dtype"           : bool, 
                                   "default"         : False,
                                   "help"            : "This describes whether the centre of mass of the particles is fixed."}) }
   
   def store(self, ens):
      """Takes an ensemble instance and stores a minimal representation of it.

      Args:
         ens: An ensemble object.
      """

      super(RestartEnsemble,self).store(ens)
      if type(ens) is NVEEnsemble:    
         self.type.store("nve"); tens=0
      elif type(ens) is NVTEnsemble:  
         self.type.store("nvt"); tens=1
      elif type(ens) is NPTEnsemble:  
         self.type.store("npt"); tens=2
      elif type(ens) is NSTEnsemble:  
         self.type.store("nst"); tens=3
      
      self.timestep.store(ens.dt)
      self.temperature.store(ens.temp)
      
      if tens > 0: 
         self.thermostat.store(ens.thermostat)
         self.fixcom.store(ens.fixcom)
      if tens > 1:
         self.barostat.store(ens.barostat)
      if tens == 2:
         self.pressure.store(ens.pext)
      if tens == 3:
         self.stress.store(ens.pext)

   def fetch(self):
      """Creates an ensemble object.

      Returns:
         An ensemble object of the appropriate type and with the appropriate
         objects given the attributes of the RestartEnsemble object.
      """

      super(RestartEnsemble,self).fetch()
      if self.type.fetch().upper() == "NVE" :
         ens = NVEEnsemble(dt=self.timestep.fetch(), temp=self.temperature.fetch(), fixcom=self.fixcom.fetch())
      elif self.type.fetch().upper() == "NVT" : 
         ens = NVTEnsemble(dt=self.timestep.fetch(), temp=self.temperature.fetch(), thermostat=self.thermostat.fetch(),
                        fixcom=self.fixcom.fetch())
      elif self.type.fetch().upper() == "NPT" : 
         ens = NPTEnsemble(dt=self.timestep.fetch(), temp=self.temperature.fetch(), thermostat=self.thermostat.fetch(),
                        fixcom=self.fixcom.fetch(), pext=self.pressure.fetch(), barostat=self.barostat.fetch() )
      elif self.type.fetch().upper() == "NST" : 
         ens = NSTEnsemble(dt=self.timestep.fetch(), temp=self.temperature.fetch(), thermostat=self.thermostat.fetch(),
                        fixcom=self.fixcom.fetch(), sext=self.stress.fetch(), barostat=self.barostat.fetch() )
                        
      print "thermostat energy", ens.thermostat.ethermo
      return ens
      
   def check(self):
      """Function that deals with optional arguments.

      Makes sure that if the ensemble requires a thermostat or barostat that 
      they have been defined by the user and not given the default values.
      """

      super(RestartEnsemble,self).check()
      if self.type.fetch().upper() == "NVT":
         if self.thermostat._explicit == False:
            raise ValueError("No thermostat tag supplied for NVT simulation")
      if self.type.fetch().upper() == "NPT":
         if self.thermostat._explicit == False:
            raise ValueError("No thermostat tag supplied for NPT simulation")
         if self.barostat._explicit == False:
            raise ValueError("No barostat tag supplied for NPT simulation")
         if self.barostat.thermostat._explicit == False:
            raise ValueError("No thermostat tag supplied in barostat for NPT simulation")
      if self.type.fetch().upper() == "NST":
         if self.thermostat._explicit == False:
            raise ValueError("No thermostat tag supplied for NST simulation")
         if self.barostat._explicit == False:
            raise ValueError("No barostat tag supplied for NST simulation")
         if self.barostat.thermostat._explicit == False:
            raise ValueError("No thermostat tag supplied in barostat for NST simulation")
         if self.barostat.kind.fetch() == "rigid":
            raise ValueError("You must use a flexible barostat to do constant stress simulations.")
