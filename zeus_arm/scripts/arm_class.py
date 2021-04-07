#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Created on Thu May 28 14:40:02 2020
# @author: Santiago Moya		santiago.moya@usherbrooke.ca


"""
@package zeus_arm

------------------------------------

Rover's arm class

"""

import rospy
import numpy as np
from ddynamic_reconfigure_python.ddynamic_reconfigure import DDynamicReconfigure

class RoboticArm() : 
	"""
	RoboticArm class
	
	5 DOF robot arm
	
	"""
	def __init__(self):
		"""
		Constructor method

		"""
		# Robot geometry
		self.dof = 5
		self.l1 = 0.156175
		self.l2 = 0.265614
		self.l3 = 0.539307
		self.l4 = 0.457614
		self.l5 = 0.131542

		# DH parameters are in order from world to end-effector        
		self.r_dh = np.array([0.,      0.,       0.73375, 0.5866,  0.,      0.]) 
		self.d_dh = np.array([0.15255, 0.06405,  0.,      0.,      0.01349,      0.25664])
		self.t_dh = np.array([0.,      0.,       0.,      0.,      0.,      0.])
		self.a_dh = np.array([0.,      np.pi/2,  0.,      0.,      np.pi/2, 0.])

		# Robot state
		self.ref_cmd = np.zeros((6,1), dtype=np.float64)
		self.joint_angles = np.zeros(5, dtype=np.float64)
		#self.lambda_gain = 0.1
		# Initialize configurable params
		# Create a DynamicDynamicReconfigure Server
		self.ddr = DDynamicReconfigure("zeus_arm")

		# Add variables to ddr(name, description, default value, min, max, edit_method)        
		# Model Settings
		self.ddr.add_variable("lambda_gain", "float", 0.1, 0., 10.)
		#self.inputs = ['Joint', 'Cartesian']
		#self.input_enum = self.ddr.enum([ self.ddr.const("Cartesian", "int", 0, "Cartesian"),
		#								  self.ddr.const("Joint", "int", 1, "Joint")],
		#								 "Input enum for arm control mode")
		#self.ddr.add_variable("control_mode", "desired control mode", 0, 0, 3, edit_method=self.input_enum)


		# Start Server
		self.ddr.start(self.dynamic_reconfigure_callback)
		rospy.sleep(1)


	def dynamic_reconfigure_callback(self, config, level):

		'''
		Updates parameters value when changed by the user.
		----------
		Parameters
		----------
		config: dict
			Keys are param names and values are param values
		level: Unused
		-------
		Returns
		-------
		config: dict
			Keys are param names and values are param values
		'''
		# Update variables
		var_names = self.ddr.get_variable_names()
		for var_name in var_names:
			self.__dict__[var_name] = config[var_name]
		return config

	def dh2T(self, r , d , theta, alpha ):
		"""  
		Creates a transformtation matrix based on DH parameters
		
		INPUTS
		r     : DH parameter            (float 1x1)
		d     : DH parameter            (float 1x1)
		theta : DH parameter            (float 1x1)
		alpha : DH parameter            (float 1x1)
		
		OUTPUTS
		T     : Transformation matrix   (float 4x4 (numpy array))
				
		"""
		T = np.zeros((4,4), dtype=np.float64)

		c = lambda ang : np.cos(ang)
		s = lambda ang : np.sin(ang)
		
		T[0][0] = c(theta)
		T[0][1] = -s(theta)*c(alpha)
		T[0][2] = s(theta)*s(alpha)
		T[0][3] = r*c(theta)
		
		T[1][0] = s(theta)
		T[1][1] = c(theta)*c(alpha)
		T[1][2] = -c(theta)*s(alpha)
		T[1][3] = r*s(theta)
		
		T[2][0] = 0
		T[2][1] = s(alpha)
		T[2][2] = c(alpha)
		T[2][3] = d
		
		T[3][0] = 0
		T[3][1] = 0
		T[3][2] = 0
		T[3][3] = 1
		
		# Sets extremely small values to zero
		for i in range(0,4):
			for j in range(0,4):
				if -1e-10 < T[i][j] < 1e-10:
					T[i][j] = 0
		
		return T
			

	def dhs2T(self, r , d , theta, alpha ):
		"""
		Creates transformation matrix from end effector base to world base
	
		INPUTS
		r     : DH parameters                               (float nx1)
		d     : DH parameters                               (float nx1)
		theta : DH parameters                               (float nx1)
		alpha : DH parameters                               (float nx1)
	
		OUTPUTS
		WTT : Transformation matrix from tool to world      (float 4x4 (numpy array))
	
		"""
		WTT = np.zeros((4,4), dtype=np.float64)
		XTY = np.zeros((4,4), dtype=np.float64) 
		INT = np.array([XTY])
		
		# Count the number of T matrices to calculate
		parametersCount = len(r)
		
		# Create array for matrices
		for y in range(0,parametersCount):
			INT = np.append(INT,[XTY],0)
			
		# Calculate each T matrix
		for x in range(0, parametersCount):
			INT[x] = self.dh2T(r[x],d[x], theta[x], alpha[x])
		
		# First time must be done outside loop, if not WTT will remain a zeros matrix
		WTT = INT[0]
		for i in range(0,parametersCount-1):
			WTT = WTT.dot(INT[i+1])    
		
		return WTT
		
	def forward_kinematics(self):
		"""
		Calculates end effector position
		
		OUTPUTS
		r : current robot task coordinates                          (list 3x1)

		"""   

		# Extract transformation matrix
		WTG = self.dhs2T(self.r_dh,self.d_dh,self.t_dh,self.a_dh)

		theta_x = np.arctan2(WTG[2][1],WTG[2][2])
		theta_y = np.arctan2(-WTG[2][0],np.sqrt(WTG[2][1]**2 + WTG[2][2]**2))
		theta_z= np.arctan2(WTG[1][0],WTG[0][0]) 
		
		# Assemble the end effector position vector
		r = np.zeros((6,1), dtype=np.float64)
		r[0] = WTG[0][3]
		r[1] = WTG[1][3]
		r[2] = WTG[2][3]
		r[3] = theta_x
		r[4] = theta_y
		r[5] = theta_z

		return r


	def jacobian_matrix(self):
		"""
		Calculates jacobian matrix 
		
		INPUTS
		current_config : current robot joint space coordinates (list 5x1)
		
		OUTPUTS
		Jac : jacobian matrix (float 3x5)                                           
		"""

		J = np.zeros((6,self.dof), dtype=np.float64)

		c = lambda ang : np.cos(ang)
		s = lambda ang : np.sin(ang)

		l1 = self.l1
		l2 = self.l2
		l3 = self.l3
		l4 = self.l4
		l5 = self.l5

		q = self.joint_angles

		J[0][0] = -(l2 + l3 * c(q[1]) + l4 *c(q[1] + q[2] + np.pi) + l5 * c(q[1] + q[2] + q[3] + np.pi)) * s(q[0])
		J[0][1] = (l3 * c(q[1]) - l4 * s(q[1] + q[2] + np.pi) - l5 * s(q[1] + q[2] + q[3] + np.pi)) * c(q[0])
		J[0][2] = (-l4 * s(q[1] + q[2] + np.pi) - l5 * s(q[1] + q[2] + q[3] + np.pi)) * c(q[0])
		J[0][3] = (-l5 * s(q[1] + q[2] + q[3] + np.pi)) * c(q[0])
		J[0][4] = 0.

		J[1][0] = -(l2 + l3 * c(q[1]) + l4 *c(q[1] + q[2] + np.pi) + l5 * c(q[1] + q[2] + q[3] + np.pi)) * c(q[0])
		J[1][1] = -(l3 * c(q[1]) - l4 * s(q[1] + q[2] + np.pi) - l5 * s(q[1] + q[2] + q[3] + np.pi)) * s(q[0])
		J[1][2] = -(-l4 * s(q[1] + q[2] + np.pi) - l5 * s(q[1] + q[2] + q[3] + np.pi)) * s(q[0])
		J[1][3] = -(-l5 * s(q[1] + q[2] + q[3] + np.pi)) * s(q[0])
		J[1][4] = 0.

		J[2][0] = 0.
		J[2][1] = -l3 * s(q[1]) + l4 * c(q[1] + q[2] + np.pi) + l5 * c(q[1] + q[2] + q[3] + np.pi)
		J[2][2] = l4 * c(q[1] + q[2] + np.pi) + l5 * c(q[1] + q[2] + q[3] + np.pi)
		J[2][3] = l5 * c(q[1] + q[2] + q[3] + np.pi)
		J[2][4] = 0.

		J[3][0] = 0.
		J[3][1] = 0.
		J[3][2] = 0.
		J[3][3] = 0.
		J[3][4] = 1.

		J[4][0] = 0.
		J[4][1] = 1.
		J[4][2] = 1.
		J[4][3] = 1.
		J[4][4] = 0.

		J[5][0] = 1.
		J[5][1] = 0.
		J[5][2] = 0.
		J[5][3] = 0.
		J[5][4] = 0.

		return J 
			
	def move_to_home(self):
		"""
		Moves robot arm to rest position
		
		"""
		q = [0,0,0,0,0,0] # set defined angles for home position
		move_to(q)
				
	def move_to(self,q):
		"""
		Moves robot arm to deired joint space configuartion
		
		INPUTS
		q  : desired robot joint space coordinates     (list 5x1)

		"""
		# TODO : code that sends joint space coordinates to all motors
	
	
	def get_joint_config(self):
		"""
		Returns robot joint configuration
		
		OUTPUTS
		q  : current robot configuration                            (list 5x1)

		"""
		# TODO : Code that reads current robot configuration for all joint motors
		q = np.zeros((5,1), dtype=np.float64)
	
		return q
	

	def get_effector_pos(self):
		"""
		Returns current end effector position
		
		OUTPUTS
		end_effector  : current end effector coordinates     (list 3x1)

		"""
		q = get_joint_config()
		self.end_effector = forward_kinematics(q)
		
		return end_effector


	def speed_controller(self):
		"""	
		Returns speed command to send to actuator
		
		OUTPUTS
		cmd_to_motors  : position command for motors     (list 5x1)
		"""
		# J_inv = np.linalg.pinv(J) 
		# q_dot = np.dot(J_inv,self.ref_cmd)
   
		q_dot = np.zeros((5,1), dtype = np.float64)
		J = self.jacobian_matrix()
		Jt = J.T
		I = np.identity(5)
		lambda2I = np.power(self.lambda_gain, 2) * I
		q_dot = np.dot(np.dot(np.linalg.inv(np.dot(Jt,J) + lambda2I), Jt), self.ref_cmd)

		return q_dot.flatten().tolist()

		
