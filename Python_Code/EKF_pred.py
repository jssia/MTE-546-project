import numpy as np  
from var_store import var_store
import math as m
from math import tan,cos,sqrt

class EKF_pred(var_store):

	def __init__(self):
		super().__init__()

	def dt(self,val=0.4):
		return val

	#jacobian of f
	def Fk(self,Xk_pred_corr_k_m1,Uk_m1):
		#values
		T = Uk_m1[0,:][0]
		del_k_m1 = Uk_m1[1,:][0]
		#state constants
		dt = self.dt()
		b = self.b()		
		c1 = self.c1(T)
		L = self.L
		L_r = self.L_r
		#vars from input		
		del_dot_m1	= self.del_dot_m1(del_k_m1)	
		#print('del_dot_m1',del_dot_m1)
		row_1 = np.array([1 + (c1 - b)*dt,0,0])
		row_2 = np.array([tan(del_k_m1)*dt/sqrt(L**2 + L_r**2*tan(del_k_m1)**2),1,0])
		row_3 = np.array([L**2*del_dot_m1*(tan(del_k_m1)**2 + 1)*dt/(L**2 + L_r**2*tan(del_k_m1)**2)**1.5,0,1])
		ret_val =  np.stack([row_1,row_2,row_3])
		assert ret_val.shape == (3,3), 'weird jacobian size'
		return ret_val

	#State covariance
	def Pk(self,Pk_m1,Xk,Uk):
		Fk = self.Fk(Xk,Uk) 
		self.Pk_val = (Fk@Pk_m1)@np.transpose(Fk) + self.Q
		return self.Pk_val

	#Steering angle rate [rad/s]
	def del_dot_m1(self,del_k_m1):
		self.del_dot_m1_val = (del_k_m1 - self.del_k_m2)/self.dt()
		#print('self.del_k_m2 ',type(self.del_k_m2))
		return self.del_dot_m1_val 

	#Deceleration caused by drag [m/s2]
	def ad(self,v):
		self.ad_val = self.b()*v
		return self.ad_val

	#Acceleration caused by engine [m/s2]
	def af(self,T,v):
		self.af_val = self.c1(T)*v + self.c2(T)
		return self.af_val

	#Specific power model parameter 1 [m/s2]
	def c1(self,T):
		self.c1_val = -0.8304*(T**2)+1.6639*T
		return self.c1_val

	#Specific power model parameter 1 [m/s2]
	def c2(self,T):
		self.c2_val = -0.0323*(T**2)+0.4115*T
		return self.c2_val

	#direction of motion for COG
	def Bk_m1(self,del_k_m1): 
		self.Bk_m1_val = m.atan((self.L_r/self.L)*m.tan(del_k_m1))
		return self.Bk_m1_val

	#friction coefficient
	def b(self):
		self.b_val = 0.365056
		return self.b_val


	#State prediction
	def Xk_pred(self,Xk_pred_corr_k_m1,Uk_m1):
		#ceck if inut makes sense
		assert Xk_pred_corr_k_m1.shape == (3,1), 'incorr Xk_pred_corr_k_m1 shape'
		assert Uk_m1.shape == (2,1), 'incorr Uk_m1 shape'
		#get all values from rows
		vk_m1 = Xk_pred_corr_k_m1[0,:]
		thetha_k_m1 = Xk_pred_corr_k_m1[1,:]
		w_k_m1 = Xk_pred_corr_k_m1[2,:]
		T_k_m1 = Uk_m1[0,:]
		del_k_m1 = Uk_m1[1,:]
		#check if sterring ange makes sense
		assert del_k_m1 < m.pi/2 and del_k_m1 > -1 *m.pi/2, 'steering agle out of bounds'
		#calc_1
		vdot = self.af(T_k_m1,vk_m1) - self.ad(vk_m1)
		vk = vk_m1 + vdot*self.dt()
		#calc_2
		thetha_k = thetha_k_m1 + \
				tan(del_k_m1)*vk_m1*self.dt()/sqrt(self.L**2 + self.L_r**2*tan(del_k_m1)**2)

		#calc_3
		w_k = w_k_m1 + (vk_m1*self.del_dot_m1(del_k_m1)*self.L**2*(tan(del_k_m1)**2 + 1) + \
			vdot*tan(del_k_m1)*(self.L**2 + self.L_r**2*tan(del_k_m1)**2))*self.dt()/ \
			(self.L**2 + self.L_r**2*tan(del_k_m1)**2)**1.5
		
		#save value for next iteration
		self.del_k_m2 = del_k_m1[0]		
		#insert assertion on shape type
		ret_val = np.array([vk,thetha_k,w_k])		
		assert ret_val.shape == (3,1), 'incorr Xk_pred shape'
		return ret_val




if __name__ == '__main__':
	pass

