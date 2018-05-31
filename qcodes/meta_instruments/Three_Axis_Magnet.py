
import time
import logging
import numpy as np
from qcodes.utils import validators as vals
from pycqed.analysis import analysis_toolbox as atools

from pycqed.measurement import detector_functions as det

from pycqed.measurement import sweep_functions as swf
from pycqed.analysis import analysis_toolbox as a_tools
import logging
from copy import deepcopy,copy

import qcodes as qc
from qcodes.instrument.base import Instrument
from qcodes.utils import validators as vals
from qcodes.instrument.parameter import ManualParameter
from pycqed.instrument_drivers.pq_parameters import InstrumentParameter




class Three_Axis_Magnet(Instrument):


    def __init__(self, name,
                 Coil_X,
                 field_step_x,
                 Coil_Y,
                 field_step_y,
                 Coil_Z,
                 field_step_z,
                 Flux_instrument,
                 MC_inst,**kw):

        super().__init__(name, **kw)

        self.protection_state=False
        # Set instrumentss
        self.add_parameter('Coil_X', parameter_class=InstrumentParameter)
        self.coil_x = Coil_X
        self.add_parameter('Coil_Y', parameter_class=InstrumentParameter)
        self.coil_y = Coil_Y
        self.add_parameter('Coil_Z', parameter_class=InstrumentParameter)
        self.coil_z = Coil_Z
        self.add_parameter('Flux_instrument', parameter_class=InstrumentParameter)
        self.flux_instrument = Flux_instrument
        self.MC = MC_inst

        self.coil_list = [self.coil_x,self.coil_y,self.coil_z]

        self.add_parameter('field',
                           get_cmd=self.get_field,
                           set_cmd=self.set_field,
                           label='Persistent Field',
                           unit='T',
                           # vals=vals.Numbers(min_value=0.,max_value=max(self.max_field_y,self.max_field_z)),
                           docstring='Persistent absolute magnetic field')
        self.add_parameter('angle',
                           get_cmd=self.get_angle,
                           set_cmd=self.set_angle,
                           label='In-plane angle',
                           unit='deg',
                           vals=vals.Numbers(min_value=-180.,max_value=180.),
                           docstring='Angle of the field wrt. Z-axis')
        self.add_parameter('field_vector',
                           get_cmd=self.get_coordinates,
                           set_cmd=self._set_coordinates,
                           label='Field vector',
                           unit='T',
                           type=numpy.ndarray,
                           docstring='Field vector in coil frame')
        self.add_parameter('field_steps',
                           type=np.ndarray,
                           initial_value=np.array([field_step_x,field_step_y,field_step_z]),
                           label='Field steps',
                           type=npumpy.ndarray,
                           docstring='Maximum stepsize when changing field')
        self.add_parameter('v1',
                           get_cmd=self.get_polar_v1,
                           set_cmd=self.set_polar_v1,
                           label='In-plane vector 1',
                           type=npumpy.ndarray,
                           docstring='Vector that defines 0 angle in the sample plane')
        self.add_parameter('v2',
                           get_cmd=self.get_angle,
                           set_cmd=self.set_angle,
                           label='In-plane vector 2',
                           type=npumpy.ndarray,
                           docstring='Second vector in the sample plane')




    def set_polar_v1(self,v1):
        self.v1 = v1

    def get_polar_v1(self):
        return self.v1

    def set_current_pos_as_v1(self):
        current_field = self.get_field()
        self.set_polar_x(np.array(current_field))

    def set_polar_v2(self,v2):
        self.v2 = v2

    def get_polar_v2(self):
        return self.v2

    def set_current_pos_as_v2(self):
        current_field = self.get_field()
        self.set_polar_v2(np.array(current_field))

    def get_unit_normal(self):
        '''
        Returns the normal vector of the plane, where:
            v1: is used as the x-axis in the new polar coord system
            v2: defines the plane of the in-plane angle
        '''
        if self.v1 is None:
            raise ValueError('v1 is not defined')
        elif self.v2 is None:
            raise ValueError('v2 is not defined')
        else:
            v_normal = np.cross(self.v1, self.v2)
            self.unit_normal = v_normal/np.linalg.norm(v_normal)
            return self.unit_normal

    def rotation_matrix(self, theta):

        """
        Return matrix to rotate about axis defined by point and unit_vector.
        """
        angle = theta*np.pi/180.
        sina = np.sin(angle)
        cosa = np.cos(angle)
        unit_normal = self.get_unit_normal()
        ux, uy, uz = unit_normal
        # rotation matrix around unit vector
        R = np.diag([cosa, cosa, cosa])
        R += np.outer(unit_normal, unit_normal) * (1.0 - cosa)
        direction *= sina
        R += np.array([[0.0,-uz*sina,uy*sina],
                          [uz*sina, 0.0,-ux*sina],
                          [-uy*sina, ux*sina,  0.0]])
        return R

    def set_field(self,field):
        '''
        Changes the field magnitude
        '''
        current_angle = self.angle()
        target_coords = self.rotation_matrix(current_angle).dot(self.v1)*field
        self.step_field_coords(target_coords)
        return 0.

    def get_coordinates(self):
        x_coord = self.coil_x.field()
        y_coord = self.coil_y.field()
        z_coord = self.coil_z.field()
        return np.array([x_coord,y_coord,z_coord])

    def get_field(self):
        coords = self.get_coordinates()
        return np.linalg.norm(coords)

    def set_angle(self,angle):
        '''
        Changes the in-plane angle of the field
        '''
        current_field = self.field()
        target_coords = self.rotation_matrix(angle).dot(self.v1)*current_field
        self.step_field_coords(target_coords)
        return 0.

    def get_angle(self):
        coords = np.get_coordinates()
        phi = np.arccos(np.dot(coords,self.v1)/(np.linalg.norm(coords)*np.linalg.norm(self.v1)))
        return phi

    def _set_coordinates(self,target_coords):
        '''
        Gets the current coordinates, defines step sizes for all directions,
        steps in a straight line to the target coordinates.
        '''
        current_coords = self.get_coordinates()
        delta = target_coords - current_coords
        max_num_steps = int(max(np.ceil(np.abs(delta)/self.field_steps())))
        stepsizes = delta/max_num_steps
        for tt in range(max_num_steps):
            for ii, coil in enumerate(self.coil_list):
                current_coords[ii]+=stepsizes[ii]
                coil.field(current_coords[ii])
        for ii, coil in enumerate(self.coil_list):
            coil.field(target_coords[ii])


