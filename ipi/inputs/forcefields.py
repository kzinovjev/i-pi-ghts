"""Deals with creating the forcefield class.

Copyright (C) 2013, Joshua More and Michele Ceriotti

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http.//www.gnu.org/licenses/>.


Classes:
   InputForces: Deals with creating all the forcefield objects.
   InputForceBeads: Base class to deal with one particular forcefield object.
   InputFBSocket: Deals with creating a forcefield using sockets.
"""

__all__ = ['InputForces', "InputFFSocket"]

from copy import copy
from ipi.engine.forcefields import *
from ipi.interfaces.sockets import InterfaceSocket
from ipi.utils.inputvalue import *

class InputForceField(Input):
   """ForceField input class.

   Handles generating one instance of a particular forcefield class from the xml
   input file, and generating the xml checkpoint tags and data from an
   instance of the object.

   Attributes:
      name: The number of beads that the forcefield will be evaluated on.
      latency: The number of seconds to sleep between looping over the requests.
   Fields:
      pars: A dictionary containing the forcefield parameters.
   """

   attribs = { "name" : ( InputAttribute, { "dtype"   : str,
                                         "help"    : "The name by which the forcefienld will be identified in the System forces section." } ),
               "pbc":  ( InputAttribute, { "dtype"   : bool,
                                         "default" : True,
                                         "help"    : "Applies periodic boundary conditions to the atoms coordinates before passing them on to the driver code." })
                                         
            }
   fields = {
            "latency" : ( InputValue, { "dtype"   : float,
                                         "default" : 0.01,
                                         "help"    : "The number of seconds the polling thread will wait between exhamining the list of requests." } ),
            "pars" : (InputValue, { "dtype" : dict,
                                     "default" : {},
                                     "help" : "The parameters of the force field"} )
   }

   default_help = "Base class that deals with the assigning of force calculation jobs and collecting the data."
   default_label = "FORCEFIELD"

   def store(self, ff):
      """Takes a ForceBeads instance and stores a minimal representation of it.

      Args:
         forceb: A ForceBeads object.
      """

      Input.store(self,ff)
      self.name.store(ff.name)
      self.latency.store(ff.latency)
      self.pars.store(ff.pars)
      self.pbc.store(ff.dopbc)

   def fetch(self):
      """Creates a ForceBeads object.

      Returns:
         A ForceBeads object.
      """

      super(InputForceField,self).fetch()

      return ForceField(pars = self.pars.fetch(), name = self.name.fetch(), latency = self.latency.fetch(), dopbc = self.pbc.fetch())
      

class InputFFSocket(InputForceField):
   """Creates a ForceField object with a socket interface.

   Handles generating one instance of a socket interface forcefield class.
   """
   fields = {"address": (InputValue, {"dtype"   : str,
                                      "default" : "localhost",
                                      "help"    : "This gives the server address that the socket will run on." } ),
             "port":    (InputValue, {"dtype"   : int,
                                      "default" : 65535,
                                      "help"    : "This gives the port number that defines the socket."} ),
             "slots":   (InputValue, {"dtype"   : int,
                                      "default" : 4,
                                      "help"    : "This gives the number of client codes that can queue at any one time."} ),            
             "timeout": (InputValue, {"dtype"   : float,
                                      "default" : 0.0,
                                      "help"    : "This gives the number of seconds before assuming a calculation has died. If 0 there is no timeout." } )}
   attribs = { 
               "mode": (InputAttribute, {"dtype"    : str,
                                     "options"  : [ "unix", "inet" ],
                                     "default"  : "inet",
                                     "help"     : "Specifies whether the driver interface will listen onto a internet socket [inet] or onto a unix socket [unix]." } ),
   
              }

   attribs.update(InputForceField.attribs)
   fields.update(InputForceField.fields)

   default_help = "Deals with the assigning of force calculation jobs to different driver codes, and collecting the data, using a socket for the data communication."
   default_label = "FFSOCKET"

   def store(self, ff):
      """Takes a ForceField instance and stores a minimal representation of it.

      Args:
         forceb: A ForceBeads object with a FFSocket forcemodel object.
      """

      if (not type(ff) is FFSocket):
         raise TypeError("The type " + type(ff).__name__ + " is not a valid socket forcefield")

      
      super(InputFFSocket,self).store(ff)
      
      self.address.store(ff.socket.address)
      self.port.store(ff.socket.port)
      self.timeout.store(ff.socket.timeout)
      self.slots.store(ff.socket.slots)
      self.mode.store(ff.socket.mode)

   def fetch(self):
      """Creates a ForceBeads object.

      Returns:
         A ForceBeads object with the correct socket parameters.
      """

      return FFSocket(pars = self.pars.fetch(), name = self.name.fetch(), latency = self.latency.fetch(), dopbc = self.pbc.fetch(),
              interface=InterfaceSocket(address=self.address.fetch(), port=self.port.fetch(),
            slots=self.slots.fetch(), mode=self.mode.fetch(), timeout=self.timeout.fetch() ) )


   def check(self):
      """Deals with optional parameters."""

      super(InputFFSocket,self).check()
      if self.port.fetch() < 1 or self.port.fetch() > 65535:
         raise ValueError("Port number " + str(self.port.fetch()) + " out of acceptable range.")
      elif self.port.fetch() < 1025:
         warning("Low port number being used, this may interrupt important system processes.", verbosity.low)

      if self.slots.fetch() < 1 or self.slots.fetch() > 5:
         raise ValueError("Slot number " + str(self.slots.fetch()) + " out of acceptable range.")
      if self.latency.fetch() < 0:
         raise ValueError("Negative latency parameter specified.")
      if self.timeout.fetch() < 0.0:
         raise ValueError("Negative timeout parameter specified.")
