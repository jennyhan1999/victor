#####################################################################
# changes   
#			- added person association based on predicted kalman value
#			- added leaving frame, doesnt work
#			- tested with other videos, doesnt work
# problems  
#			- removing people
#			- incorrectly catagorizing people
#			- check leaving frame
# add 		
#			- leaving frame check more robust
#			- more things to catagorize people with, double check if direction is working
#			- 
#			- 
#####################################################################

from __future__ import division
import json, os, math
from pprint import pprint
from PIL import Image,ImageDraw,ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import kalman_filter_test
import test_mult_people_helper,kalman_filter_test
import copy

PEOPLE_ENTERED = 0
PEOPLE_LEFT = 0

IMG_SIZE = (960,544) #(x,y)
#import test2_json_script
'''
me 4 ft
vicky 5 ft
at 20 ft away
'''
#FOLDER_PATH = "./2_ppl_walking_towards/" 
#FOLDER_PATH = "./jen_and_vicky_cross/"
#FOLDER_PATH = "./one_person_walking_towards/"
FOLDER_PATH = "./sitting_in_chair_turning_360_cw/"


list_keypoint_json = []

BODY_25_MAPPING = {
        0:  "Nose",
        1:  "Neck",
        2:  "RShoulder",
        3:  "RElbow",
        4:  "RWrist",
        5:  "LShoulder",
        6:  "LElbow",
        7:  "LWrist",
        8:  "MidHip",
        9:  "RHip",
        10: "RKnee",
        11: "RAnkle",
        12: "LHip",
        13: "LKnee",
        14: "LAnkle",
        15: "REye",
        16: "LEye",
        17: "REar",
        18: "LEar",
        19: "LBigToe",
        20: "LSmallToe",
        21: "LHeel",
        22: "RBigToe",
        23: "RSmallToe",
        24: "RHeel",
        25: "Background"
        }

PEOPLE_PREDICTION = {}
PEOPLE = {} #master list of all people, PEOPLE[person_id][keypoint] = keypoint previous list
PEOPLE_CHANGE = {} #list of keypoints that have changed
PEOPLE_DATA_LENGTH = {} #deals with edge case in remove people, 
                                                #keep track of how long person has been there with low data

POTENTIAL_PEOPLE_ENTER = {} #waiting to check if person data is accurate
POTENTIAL_PEOPLE_LEFT = {}

MAX_PREV_LENGTH = 10 #max number of prev length coordinates in PEOPLE
ANGLE_PIX = 0.0009275693057324841 #angle per pix
PERSPECTIVE = list()

def check_state_change():
    for person_id in PEOPLE:
        state_change = {"x":[],"y":[]}
        for prev_body_keypoint in PEOPLE[person_id]:
            try: 
                x_diff,y_diff = test_mult_people_helper.difference(PEOPLE[person_id][prev_body_keypoint])
                if x_diff > 100:
                    #print("significant x keypoint : ",prev_body_keypoint)
                    state_change["x"] = state_change["x"]+[prev_body_keypoint]

                if y_diff > 100:
                    #print("significant y keypoint : ",prev_body_keypoint)
                    state_change["y"] = state_change["y"]+[prev_body_keypoint]

                    PEOPLE_CHANGE[person_id] = state_change
            except:
                continue
    return PEOPLE_CHANGE

'''
removes oldest keypoint as long as original previous keypoints is equal to MAX_PREV_LENGTH
'''
def remove_from_PEOPLE():
    for person_id in PEOPLE:
        for prev_body_keypoint in PEOPLE[person_id]:
            length_keypoint = len(PEOPLE[person_id][prev_body_keypoint])
            if length_keypoint == MAX_PREV_LENGTH:
                PEOPLE[person_id][prev_body_keypoint] = PEOPLE[person_id][prev_body_keypoint][1:]
                assert length_keypoint <= MAX_PREV_LENGTH, " 0 length does not match "+ str(length_keypoint)
        #check_person_leaving()

'''
checks to make sure that there are no people in PEOPLE with no keypoint values,
also takes care of edge case where another person is incorrectly detected and
appended coordinates do ddnot exceed MAX_PREV_LENGTH, in which case the person_id 
is removed after a set number of iterations
'''

def check_person_leaving():
    global PEOPLE_LEFT
    remove = set()
    #print_people()
    for person_id in PEOPLE:
        empty_c = 0
        out_of_frame_x = 0
        for keypoint in PEOPLE[person_id]:
            #if empty, add to c
            if PEOPLE[person_id][keypoint] == []:
                #print("empty c is" ,empty_c)
                empty_c += 1	

            if (PEOPLE[person_id][keypoint][-1][0] > IMG_SIZE[0]) or (PEOPLE[person_id][keypoint][-1][0] < 0):
                out_of_frame_x += 1 

                #if all keypoints in person id are empty, then remove person
            if empty_c == 25:
                print(".....................................left because empty keypoints")
                remove.add(person_id)
            if out_of_frame_x > 20:
                remove.add(person_id)

            #case where not enough data points to remove personid 
            keypoint_len = len(PEOPLE[person_id][0])
            if keypoint_len < MAX_PREV_LENGTH-1:

                if (person_id in PEOPLE_DATA_LENGTH):# and 

                    PEOPLE_DATA_LENGTH[person_id] += 1
                else:
                    PEOPLE_DATA_LENGTH[person_id] = 1


    for person_id in remove: 
        '''
        if person_id not in POTENTIAL_PEOPLE_LEFT:
            POTENTIAL_PEOPLE_LEFT[person_id] = 1
        else:
            POTENTIAL_PEOPLE_LEFT[person_id] += 1
            if POTENTIAL_PEOPLE_LEFT[person_id] > 2:
            
            PEOPLE.pop(person_id)
            print("Person left, removed")
            PEOPLE_LEFT += 1
            POTENTIAL_PEOPLE_LEFT.pop(person_id)
        '''
        #print_people()
        PEOPLE.pop(person_id)
        print("Person left, removed.................................................")
        PEOPLE_LEFT += 1

    popped_people = set()
    for person_id in PEOPLE_DATA_LENGTH:

        if person_id in PEOPLE and PEOPLE_DATA_LENGTH[person_id] > 10 and person_id not in remove:
            PEOPLE.pop(person_id)
            PEOPLE_LEFT += 1
            print("Person left, outlier!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            popped_people.add(person_id)
            #print_people()

    for person_id in popped_people:
        PEOPLE_DATA_LENGTH.pop(person_id)


def order_directory():
    for file in os.listdir(FOLDER_PATH):
        #print("file found is:",file)
          #i (file[0]=='0'):
          list_keypoint_json.append(file)

    #list of json file in order
    list_keypoint_json.sort()

def get_person_set():
    temp = set()
    for person_id in PEOPLE:
        temp.add(person_id)
                #print("temp is ", temp)
    return temp

def person_association(people_set,keypoint_list):
    global PEOPLE_ENTERED
    threshold = 30

    keypoint_set = {0,1,8,9,12}
    if PEOPLE == {}:
        print("new person 0")
        return 0
    for person_id in people_set:
        keypoint_match = 0
        for keypoint in keypoint_set:

            arr = kalman_filter_test.kalman_array(PEOPLE[person_id],keypoint)
            x_val, x_difference = kalman_filter_test.get_x_val(arr)
            pred_x, pred_sig = kalman_filter_test.kalman_filter_using_math(x_val,x_difference)
            direction = test_mult_people_helper.check_direction(PEOPLE,person_id)
            average_x = test_mult_people_helper.average(0,PEOPLE[person_id][keypoint])
                
            if abs(pred_x-keypoint_list[keypoint*3]) < threshold:
                keypoint_match += 1
        #print("keypoint match number is ",keypoint_match)			
        if keypoint_match > len(keypoint_set) - 1:
            return person_id

    return len(PEOPLE)

def parse_keypoints(key,keypoint_list):
    for j in range(0,len(keypoint_list),3):
        tmp = (keypoint_list[j],keypoint_list[j+1],keypoint_list[j+2])
        #adding keypoint for new person id
        if j//3 not in PEOPLE[person_id]: 
            PEOPLE[person_id][j//3] = [tmp]

        else:
            PEOPLE[person_id][j//3].append(tmp)


def add_person_lag(person_id,keypoint_list):
    print("testing lag....")


    if person_id not in POTENTIAL_PEOPLE_ENTER:
        POTENTIAL_PEOPLE_ENTER[person_id] = {'frequency': 1, 
                                             'keypoints': {}}
    else:
        POTENTIAL_PEOPLE_ENTER[person_id]['frequency'] += 1
    #add keypoint
    for j in range(0,len(keypoint_list),3):
        tmp = (keypoint_list[j],keypoint_list[j+1],keypoint_list[j+2])
        #adding keypoint for new person id
        if j//3 not in POTENTIAL_PEOPLE_ENTER[person_id]['keypoints']: 
            POTENTIAL_PEOPLE_ENTER[person_id]['keypoints'][j//3] = [tmp]
        else:
            POTENTIAL_PEOPLE_ENTER[person_id]['keypoints'][j//3].append(tmp)


        if POTENTIAL_PEOPLE_ENTER[person_id]['frequency'] > 5:
            print("true")
            return True
        #print("person id is now ",POTENTIAL_PEOPLE_ENTER)
    return False

'''loop through single path to add values into PEOPLE dict, up to a specified
number of tuple inputs, also checks if there is a difference between the different
states'''
def decode_keypoints(path):

    '''
    add values to person dict
    '''

    #open file as f
    global PEOPLE_ENTERED
    global PEOPLE_LEFT
    b = 0
    #print_people()
    #print("length of ppl are ..........................................................", len(PEOPLE))
    with open(path) as f:
        #parse each line in file
        for line in f:
            #try:
            json_line = json.loads(line)
            # Access date
            c = 0
            people_set = get_person_set()
            print("og people set is ", people_set)
            #if file is correctly formatted, find people
            for x in json_line['people']:
            
                #current keypoints for specific person
                keypoint_list = x['pose_keypoints_2d']
                person_id = person_association(people_set,keypoint_list)
                
                #adding person in PEOPLE dict
                if person_id not in PEOPLE:# and person_id not in POTENTIAL_PEOPLE_LEFT:
                    if add_person_lag(person_id,keypoint_list):
                        print("person entered, added after lag...............................")
                        PEOPLE_ENTERED += 1
                        PEOPLE[person_id] = POTENTIAL_PEOPLE_ENTER[person_id]['keypoints']
                        POTENTIAL_PEOPLE_ENTER.pop(person_id)
                        
                    else:
                        return
                if person_id  in people_set:
                    people_set.remove(person_id)
                
                for j in range(0,len(keypoint_list),3):
                    tmp = (keypoint_list[j],keypoint_list[j+1],keypoint_list[j+2])
                    #adding keypoint for new person i
                    if j//3 not in PEOPLE[person_id]: 
                        PEOPLE[person_id][j//3] = [tm]
                        assert len(PEOPLE[person_id][j//3]) <= MAX_PREV_LENGTH, " 1 length does not match "+ str(len(PEOPLE[person_id][j//3]))
                    else:
                        remove_from_PEOPLE()
                        PEOPLE[person_id][j//3].append(tmp)
                        assert len(PEOPLE[person_id][j//3]) <= MAX_PREV_LENGTH, " 2 length does not match "+ str(len(PEOPLE[person_id][j//3]))


                c += 1
                if people_set == {}:
                    print("matched everyone")
                else:
                    for person_id in people_set:
                        print("person left in people set...................................................")
                        PEOPLE_LEFT += 1
                        PEOPLE.pop(person_id)
                        check_person_leaving()

        #except (ValueError, KeyError, TypeErro
        #    print ("JSON format error")

        remove_from_PEOPLE()

        '''
        remove a point in person to make sure only have set number of past values to compare with
        '''

        #if PEOPLE != {} and (len(PEOPLE[0][0]) == 4): #ADD ONE BECAUSE CHECK STATE CHANGE REMOVES A VALUE
        if PEOPLE != {} :#and check_length():
            state_change = check_state_change()
            #check_distance()
            #check_angle()

            #if check_distance():
            #	print("close enough to interact with")   
            test_mult_people_helper.map_state_change_to_motion(state_change,PEOPLE)


'''
check if feet are present, if they are return the perspective lines they are between
'''
def check_distance():
    for person_id in PEOPLE:
        #average heel
        avg_y = (test_mult_people_helper.average(1,PEOPLE[person_id][11]) + test_mult_people_helper.average(1,PEOPLE[person_id][14]))/2
        
        horiz_upper_bound = 0
        for tpl in PERSPECTIVE:
            #print("tpl is ", tpl)
            
            horiz_lower_bound = 0
            if avg_y > tpl[0]:
                horiz_upper_bound = tpl[1]
                break
            horiz_lower_bound = horiz_upper_bound - 1
            if horiz_upper_bound == 0:
                print(person_id, " feet are not there")
                return False
            
        
            else:
                continue
                #print(person_id, " feet are there")
            return True
        print(person_id, ": upper bound is ", horiz_upper_bound, " lower bound is ", horiz_lower_bound)


def check_length():
    for person_id in PEOPLE:
        if len(PEOPLE[person_id][0]) == MAX_PREV_LENGTH:
            return True
        return False

#pretty print people 
def print_people():
    spaces = ""
    for person_id in PEOPLE:
        print(person_id)
        for keypoint in PEOPLE[person_id]:
            spaces += ("	")
            print(spaces + str(keypoint))
            spaces += ("  ")
            for val in PEOPLE[person_id][keypoint]:
                print(spaces + str(val))
                spaces = ""


def get_file_number (path):
    len_folder = len(FOLDER_PATH)
    file_number = ""
    for val in path[len_folder + 1:]:
        if val.isdigit():
            file_number += val
    return file_number




def run_all_files():
    order_directory()
    print("in run all files......................... ", ANGLE_PIX)
    flag = False
    b = 0
    for path in list_keypoint_json:
        if b == 287:
            return

        if path[-14:] == "keypoints.json":
            print("\n")
            #print("len of people ", len(PEOPLE))
            print(path)
            decode_keypoints(FOLDER_PATH+path)
            b += 1
        #else
            #decode_images(FOLDER_PATH+path)



def main():

    run_all_files()
    print("Total People Entered is ", PEOPLE_ENTERED)
    print("Total People Left is ", PEOPLE_LEFT)


if __name__ == "__main__":
    main()
