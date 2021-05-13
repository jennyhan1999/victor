from __future__ import division

from pykalman import KalmanFilter
import numpy as np
import matplotlib.pyplot as plt
import time
import json,os 
from pprint import pprint


FOLDER_PATH = "./walk_away_then_towards/"
list_keypoint_json = []
c = 0
prev_body_keypoints = {}
known_keypoints = {}

def kalman_filter_using_module(arr):
	#measurements = np.asarray([(20,20),(40,40),(45,45),(37,40),(25,25),(10,10)])
	measurements = np.asarray(arr)
	initial_state_mean = [measurements[0, 0],
	                      0,
	                      measurements[0, 1],
	                      0]

	transition_matrix = [[1, 1, 0, 0],
	                     [0, 1, 0, 0],
	                     [0, 0, 1, 1],
	                     [0, 0, 0, 1]]

	observation_matrix = [[1, 0, 0, 0],
	                      [0, 0, 1, 0]]

	kf1 = KalmanFilter(transition_matrices = transition_matrix,
	                  observation_matrices = observation_matrix,
	                  initial_state_mean = initial_state_mean)

	kf1 = kf1.em(measurements, n_iter=5)
	(smoothed_state_means, smoothed_state_covariances) = kf1.smooth(measurements)

	plt.figure(1)
	times = range(measurements.shape[0])
	plt.plot(1280- measurements[:, 0],720-measurements[:,1],'bo',)
	'''
	plt.plot(times, measurements[:, 0], 'bo',
         times, measurements[:, 1], 'ro',
         times, smoothed_state_means[:, 0], 'b--',
         times, smoothed_state_means[:, 2], 'r--',)
    '''
	plt.show()

def kalman_filter_using_math(x_val,x_difference):
	# gaussian function
	def f(mu, sigma2, x):
	    ''' f takes in a mean and squared variance, and an input x
	       and returns the gaussian value.'''
	    coefficient = 1.0 / sqrt(2.0 * pi *sigma2)
	    exponential = exp(-0.5 * (x-mu) ** 2 / sigma2)
	    return coefficient * exponential

	# the update function
	def update(mean1, var1, mean2, var2):
	    ''' This function takes in two means and two squared variance terms,
	        and returns updated gaussian parameters.'''
	    # Calculate the new parameters
	    new_mean = (var2*mean1 + var1*mean2)/(var2+var1)
	    new_var = 1/(1/var2 + 1/var1)
	    
	    return [new_mean, new_var]
	# the motion update/predict function
	def predict(mean1, var1, mean2, var2):
	    ''' This function takes in two means and two squared variance terms,
	        and returns updated gaussian parameters, after motion.'''
	    # Calculate the new parameters
	    new_mean = mean1 + mean2
	    new_var = var1 + var2
	    
	    return [new_mean, new_var]
	#print(update(20,9,30,3))
	measurements = x_val#[5., 6., 7., 9., 10.]
	motions = x_difference#[1., 1., 2., 1., 1.]

	# initial parameters
	measurement_sig = 1.
	motion_sig = 2.
	mu = 0.
	sig = 100.#10000.


	## TODO: Loop through all measurements/motions
	# this code assumes measurements and motions have the same length
	# so their updates can be performed in pairs
	for n in range(len(measurements)):
	    # measurement update, with uncertainty
	    mu, sig = update(mu, sig, measurements[n], measurement_sig)
	    #print('Update: [{}, {}, {}]'.format(mu, sig,measurements[n]))
	    # motion update, with uncertainty
	    mu, sig = predict(mu, sig, motions[n], motion_sig)
	    #print('Predict: [{}, {}]'.format(mu, sig))

	    
	# print the final, resultant mu, sig
	#print('Final result: [{}, {}]'.format(mu, sig))
	#print('\n')
	return mu,sig





def order_directory():
	for file in os.listdir(FOLDER_PATH):
	  #print("file found is:",file)
	  #i (file[0]=='0'):
	  list_keypoint_json.append(file)

	#list of json file in order
	list_keypoint_json.sort()

def main():
	order_directory()
	c = 0

	for keypoint in list_keypoint_json:
	  #print("number of files is ",number_of_files)
	  c += 1
	  path = FOLDER_PATH+keypoint
	  #open each file in order
	  #try:
	  with open(path) as f:
	      for line in f:
	        try:
	          json_line = json.loads(line)
	          #pprint(json_line)
	          # Access data
	          for x in json_line['people']:
	              keypoint_list = x['pose_keypoints_2d']
	                
	              for j in range (len(keypoint_list)):
	                #tmp.append(keypoint_list[i*3+j]
	                if j%3 == 2 :
	                  tmp = (keypoint_list[j-2],keypoint_list[j-1],keypoint_list[j])
	                  #print(j//3,tmp)
	                  #add the 3 datapoints (x,y,c) into the dict
	                  if j//3 not in prev_body_keypoints: 
	                    prev_body_keypoints[j//3] = [tmp]
	                  else:
	                    prev_body_keypoints[j//3].append(tmp) 

	        except (ValueError, KeyError, TypeError):
	            print ("JSON format error")
	#print(prev_body_keypoints)
	#print("keypoint list is ", keypoint_list)
	'''
	if (len(prev_body_keypoints[0]) == 8): #ADD ONE BECAUSE CHECK STATE CHANGE REMOVES A VALUE
	#print(c)
	c += 1
	state_change = check_state_change()
	print(state_change)
	#map_state_change_to_motion(state_change)
	#check_keypoints()
	print("..")
	#print(PERSON_STATE)
	    #break
	#except:
		#print("something went wrong")
	  '''

   

def get_y_val(arr):
    y_val, y_difference = [], []
    y_prev = 0
    for tpl in arr:
        y_val.append(tpl[1])
        #print(tpl[0]-x_prev)
        #x_difference.append(tpl[0]-x_prev)
        #x_prev = tpl[0]

    y_val_npy = np.array(y_val)
    mean = np.mean(y_val_npy, axis=0)
    sd = np.std(y_val_npy, axis=0)

    final_list = [y for y in y_val_npy  if (y > mean - 2 * sd)]
    final_list = [y for y in final_list if (y < mean + 2 * sd)]

    for val in final_list:
        y_difference.append(val - y_prev)
        y_prev = val

    return final_list,y_difference

def get_x_val(arr):
    x_val, x_difference = [], []
    x_prev = 0
    for tpl in arr:
        x_val.append(tpl[0])
	#print(tpl[0]-x_prev)
        #x_difference.append(tpl[0]-x_prev)
    	#x_prev = tpl[0]

    x_val_npy = np.array(x_val)
    mean = np.mean(x_val_npy, axis=0)
    sd = np.std(x_val_npy, axis=0)
    
    final_list = [x for x in x_val_npy  if (x > mean - 2 * sd)]
    final_list = [x for x in final_list if (x < mean + 2 * sd)]
    
    for val in final_list:
        x_difference.append(val - x_prev)
        x_prev = val
        
    return final_list,x_difference

def kalman_array(keypoint_list,keypoint):
	ret = []
	for tpl in keypoint_list[keypoint]:
		new_tpl = (tpl[0],tpl[1])
		ret.append(new_tpl)
	return ret

if __name__ == "__main__":
	main()
	arr = kalman_array(keypoint_list,keypoint)
	x_val, x_difference = get_x_val(arr)
	print("new list is ", arr)
	print(x_val,x_difference)
	#kalman_filter_using_module(arr)
	kalman_filter_using_math(x_val,x_difference)
