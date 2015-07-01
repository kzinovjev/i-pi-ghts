"""Contains the classes that deal with the different dynamics required in
different types of ensembles.

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


Holds the algorithms required for normal mode propagators, and the objects to
do the constant temperature and pressure algorithms. Also calculates the
appropriate conserved energy quantity for the ensemble of choice.

"""

__all__=['GeopMover']

import numpy as np
import time


from ipi.engine.mover import Mover
from ipi.utils.depend import *
from ipi.utils import units
from ipi.utils.softexit import softexit
from ipi.utils.io import read_file
from ipi.utils.io.inputs.io_xml import xml_parse_file
from ipi.utils.units import Constants, unit_to_internal
from ipi.utils.mintools import min_brent, min_approx, BFGS

class LineMover(object):
   """Creation of the one-dimensional function that will be minimized"""
   
   def __init__(self):
      self.x0 = self.d = None

   def bind(self, ens):
      self.dbeads = ens.beads.copy()
      self.dcell = ens.cell.copy()
      self.dforces = ens.forces.copy(self.dbeads, self.dcell)      
      
   def set_dir(self, x0, mdir):      
      self.x0 = x0.copy()
      self.d = mdir.copy()/np.sqrt(np.dot(mdir.flatten(),mdir.flatten()))
      if self.x0.shape != self.d.shape: raise ValueError("Incompatible shape of initial value and displacement direction")      
   
   def __call__(self, x):
            
      self.dbeads.q = self.x0 + self.d * x
      e = self.dforces.pot
      g = - np.dot(depstrip(self.dforces.f).flatten(),self.d.flatten())
      return e, g
   
class BFGSMover(object):
   """ Creation of the multi-dimensional function that will be minimized"""

   def __init__(self):
      self.x0 = self.d = None

   def bind(self, ens):
      self.dbeads = ens.beads.copy()
      self.dcell = ens.cell.copy()
      self.dforces = ens.forces.copy(self.dbeads, self.dcell)

   def __call__(self, x):
      self.dbeads.q = x
      e = self.dforces.pot
      g = - self.dforces.f
      return e, g        

class GeopMover(Mover):
   """Geometry optimization routine. Will start with a dumb steepest descent,
   and then see to include more and more features - getting at least to BFGS.

   Attributes:

   """

   def __init__(self, fixcom=False, fixatoms=None,
             mode="sd", 
             grad_tolerance=1.0e-6, maximum_step=100.0,
             cg_old_force=np.zeros(0, float),
             cg_old_direction=np.zeros(0, float),
             invhessian=np.eye(0), 
             ls_options={ "tolerance": 1e-5,  "iter": 100.0 , "step": 1e-3, "adaptive":1.0 } ,
             tolerances = {"energy" : 1e-5, "force": 1e-5, "position": 1e-5}
             ) :   
                 
      """Initialises GeopMover.

      Args:
         fixcom: An optional boolean which decides whether the centre of mass
            motion will be constrained or not. Defaults to False.         
      """

      super(GeopMover,self).__init__(fixcom=fixcom, fixatoms=fixatoms)
      
      # optimization options
      self.ls_options = ls_options
      self.tolerances = tolerances
      self.mode=mode
      self.grad_tol = grad_tolerance
      self.max_step = maximum_step
      self.cg_old_f = cg_old_force
      self.cg_old_d = cg_old_direction
      self.invhessian = invhessian
        
      self.lm = LineMover()
      self.bfgsm = BFGSMover()      
   
   def bind(self, beads, nm, cell, bforce, bbias, prng):
      
      super(GeopMover,self).bind(beads, nm, cell, bforce, bbias, prng)
      if self.cg_old_f.size != beads.q.size :
         if self.cg_old_f.size == 0: 
            self.cg_old_f = np.zeros(beads.q.size, float)
         else: 
            raise ValueError("Conjugate gradient force size does not match system size")
      if self.cg_old_d.size != beads.q.size :
         if self.cg_old_d.size == 0: 
            self.cg_old_d = np.zeros(beads.q.size, float)
         else: 
            raise ValueError("Conjugate gradient direction size does not match system size")
            
      self.lm.bind(self)
      self.bfgsm.bind(self)
      
   def step(self, step=None):
      """Does one simulation time step."""

      self.ptime = self.ttime = 0
      self.qtime = -time.time()

      print "\nMD STEP %d\n" % step

      if (self.mode == "bfgs"):

          # BFGS Minimization
          # Initialize approximate Hessian inverse and direction
          # to the steepest descent direction
          if step == 0:# or np.sqrt(np.dot(self.bfgsm.d, self.bfgsm.d)) == 0.0:
              self.bfgsm.d = depstrip(self.forces.f) / np.sqrt(np.dot(self.forces.f.flatten(), self.forces.f.flatten()))
              self.invhessian = np.eye(len(self.beads.q.flatten()))
              print "invhessian:", self.invhessian
              #invhessian = np.eye(n)

          # Current energy, forces, and function definitions
          # for use in BFGS algorithm

          u0, du0 = (self.forces.pot, - self.forces.f)
          print "u0:", u0
          print "du0:", du0
          
          # Do one iteration of BFGS, return new point, function value,
          # derivative value, and current Hessian to build upon
          # next iteration
          print "BEFORE"
          print "self.beads.q:", self.beads.q
          print "self.bfgsm.d:", self.bfgsm.d
          print "invhessian:", self.invhessian
          self.beads.q, fx, self.bfgsm.d, self.invhessian = BFGS(self.beads.q, self.bfgsm.d, self.bfgsm, fdf0=(u0, du0), 
              invhessian=self.invhessian, max_step=self.max_step, tol=self.ls_options["tolerance"], grad_tol=self.grad_tol, itmax=self.ls_options["iter"])  #TODO: make object for inverse hessian and direction if necessary
          print "AFTER"
          print "self.beads.q", self.beads.q
          print "self.bfgsm.d", self.bfgsm.d
          print "invhessian", self.invhessian

      # Routine for steepest descent and conjugate gradient
      else:
          if (self.mode == "sd" or step == 0): 
          
              # Steepest descent minimization
              # gradf1 = force at current atom position
              # dq1 = direction of steepest descent
              # dq1_unit = unit vector of dq1
              gradf1 = dq1 = depstrip(self.forces.f)

              # move direction for steepest descent and 1st conjugate gradient step
              dq1_unit = dq1 / np.sqrt(np.dot(gradf1.flatten(), gradf1.flatten())) 
      
          else:
          
              # Conjugate gradient, Polak-Ribiere
              # gradf1: force at current atom position
              # gradf0: force at previous atom position
              # dq1 = direction to move
              # dq0 = previous direction
              # dq1_unit = unit vector of dq1
              gradf0 = self.cg_old_f
              dq0 = self.cg_old_d
              gradf1 = depstrip(self.forces.f)
              beta = np.dot((gradf1.flatten() - gradf0.flatten()), gradf1.flatten()) / (np.dot(gradf0.flatten(), gradf0.flatten()))
              dq1 = gradf1 + max(0.0, beta) * dq0
              dq1_unit = dq1 / np.sqrt(np.dot(dq1.flatten(), dq1.flatten()))

          self.cg_old_d[:] = dq1    # store force and direction for next CG step
          self.cg_old_f[:] = gradf1
   
          if (len(self.fixatoms)>0):
              for dqb in dq1_unit:
                  dqb[self.fixatoms*3] = 0.0
                  dqb[self.fixatoms*3+1] = 0.0
                  dqb[self.fixatoms*3+2] = 0.0
      
          self.lm.set_dir(depstrip(self.beads.q), dq1_unit)

          # reuse initial value since we have energy and forces already
          u0, du0 = (self.forces.pot, np.dot(depstrip(self.forces.f.flatten()), dq1_unit.flatten()))

          (x, fx) = min_brent(self.lm, fdf0=(u0, du0), x0=0.0, tol=self.ls_options["tolerance"], itmax=self.ls_options["iter"], init_step=self.ls_options["step"]) 

          self.ls_options["step"] = x * self.ls_options["adaptive"] + (1-self.ls_options["adaptive"]) * self.ls_options["step"] # automatically adapt the search step for the next iteration
      
          self.beads.q += dq1_unit * x


      self.qtime += time.time()
