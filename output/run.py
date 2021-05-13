from __future__ import division
import json, os, math
from pprint import pprint
from PIL import Image,ImageDraw,ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import kalman_filter_test
import test_mult_people_helper
import DetectChangesDict
import copy
import cv2
import numpy as np
import time

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

#FOLDER_PATH = "./head_right_left_down_up/"
#FOLDER_PATH ="./looking_at_objects/"

#FOLDER_PATH = "./head_360/"
#FOLDER_PATH = "./left_head_9pts/"
#FOLDER_PATH = "./right_head_9pts/"

#FOLDER_PATH = "./head_9pts_2people_center_right/"
#FOLDER_PATH = "./one_person_walking_across/"
#FOLDER_PATH = "./walk_away_then_towards/"


#FOLDER_PATH = "./interaction_success_invite_to_play/"
#FOLDER_PATH = "./interaction_success_one_with_background/"
#FOLDER_PATH = "./interaction_no_interest/"
#FOLDER_PATH = "./interaction_success_one/"
FOLDER_PATH = "./interaction_success_two/"
VICTOR_SPEAK = None
VICTOR_STATE = None

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
VICTOR_CONTEXT = DetectChangesDict.DetectChangesDict({
    "GAME_CONTEXT" : {
        "number_players" : 0,
        "players_id" : set() 
        #TODO: add a L C R dictionaries with body position information
    },
    "POTENTIAL_PLAYERS" : {
        "number_potential" : 0,
        "potential_id" : set()
    },
    "LEFT_GAME": {
        "number_left": 0,
        "left_id": set()
    }
 }) #tracks changes for victor_context for victor_fsm, if something changes, then send to victor fsm

INTERACT = set() #TODO: obselete

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

        remove_from_victor_state(person_id)
        #print("Person left, removed.................................................")
        PEOPLE_LEFT += 1

    popped_people = set()
    for person_id in PEOPLE_DATA_LENGTH:

        if person_id in PEOPLE and PEOPLE_DATA_LENGTH[person_id] > 10 and person_id not in remove:
            PEOPLE.pop(person_id)
            remove_from_victor_state(person_id)
            PEOPLE_LEFT += 1
            #print("Person left, outlier!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
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
        #print("new person 0")
        return 0
    for person_id in people_set:
        keypoint_match = 0
        for keypoint in keypoint_set:
            
            #print(keypoint)
            #print("person id",person_id)
            #print("PEOPLE ",PEOPLE[person_id],"\n")
            #direction = test_mult_people_helper.check_direction(PEOPLE,person_id)
            #average_x = test_mult_people_helper.average(0,PEOPLE[person_id][keypoint])
            if (person_id in PEOPLE):
                arr = kalman_filter_test.kalman_array(PEOPLE[person_id],keypoint)
                x_val, x_difference = kalman_filter_test.get_x_val(arr)
                pred_x, pred_sig = kalman_filter_test.kalman_filter_using_math(x_val,x_difference)
                #direction = test_mult_people_helper.check_direction(PEOPLE,person_id)
                #average_x = test_mult_people_helper.average(0,PEOPLE[person_id][keypoint])
                
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
            #try:i
            '''ret,frame = VIDEO.read()
            if ret == True:
                cv2.imshow("Frame",frame);
                print("showing image")
                time.sleep(2)
               
            '''
            #img = cv2.imread('messi5.jpg',0)
            #ycv2.waitKey(0)

            json_line = json.loads(line)
            # Access date
            c = 0
            people_set = get_person_set()
            #print("people set: ", people_set)
            #if file is correctly formatted, find people
            for x in json_line['people']:
            
                #current keypoints for specific person
                keypoint_list = x['pose_keypoints_2d']
                person_id = person_association(people_set,keypoint_list)
                
                #adding person in PEOPLE dict
                if person_id not in PEOPLE:# and person_id not in POTENTIAL_PEOPLE_LEFT:
                    if add_person_lag(person_id,keypoint_list):
                        PEOPLE_ENTERED += 1
                        PEOPLE[person_id] = POTENTIAL_PEOPLE_ENTER[person_id]['keypoints']

                        POTENTIAL_PEOPLE_ENTER.pop(person_id)

                        #TODO:add to potential players in victor context
                        #add_to_victor_state_potential(person_id)
                        
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
                        if (person_id in PEOPLE):
                            print("person left in people set...................................................")
                            PEOPLE_LEFT += 1
                            PEOPLE.pop(person_id)
                            remove_from_victor_state(person_id)


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

def update_game_state(state):
    global VICTOR_STATE
    print ("state is ",state)
    VICTOR_STATE = state

def decode_images(path):
    global VICTOR_SPEAK, VICTOR_STATE
    #print("decode image "+path)
    img = cv2.imread(path,1)
    font =cv2.FONT_HERSHEY_PLAIN
    img_height,img_width,img_channels = img.shape

    #print("VICTOR SPEAKS .....",VICTOR_SPEAK,int(get_file_number(path)))
    cv2.rectangle(img, (0,0), (img_width,(img_height//10)), (255,255,255), -1)
    cv2.putText(img, "Current State:", (20,20), font, 2, (0,0,0), 2, cv2.LINE_AA)
    cv2.putText(img, "Victor:", (20,50), font, 2, (0,0,0), 2, cv2.LINE_AA)

    if VICTOR_STATE:
        cv2.putText(img,VICTOR_STATE, (300,20),font,2,(0,0,0),2,cv2.LINE_AA)
    if VICTOR_SPEAK:
        cv2.putText(img,VICTOR_SPEAK[1], (150,50),font,2,(0,0,0),2,cv2.LINE_AA)
        if time.time() - VICTOR_SPEAK[0] > 10:
            VICTOR_SPEAK = None

    image_id = FOLDER_PATH+"output_images/"+get_file_number(path) + ".png"
    #image_id = "./output_images/"+get_file_number(path)+".png"
    #image_id = FOLDER_PATH+get_file_number(path)+".png"
    #print("image ",PEOPLE)
    if (PEOPLE != {}):
        for person_id in PEOPLE:
            nose = PEOPLE[person_id][0][-1]
            neck = PEOPLE[person_id][1][-1]
            eye_L= PEOPLE[person_id][14][-1]
            eye_R = PEOPLE[person_id][15][-1]
            l_ear= PEOPLE[person_id][16][-1]
            r_ear= PEOPLE[person_id][17][-1]

            w = abs(l_ear[0]-r_ear[0])
            eye_avg = (eye_L[1]+eye_R[1])/2

            h = abs(eye_avg - nose[1])*2

            top_left = (int(nose[0] - w//2),int(nose[1]-h//2))

            bottom_right = (int(nose[0] + w//2),int(nose[1]+h//2))
        
            hip = PEOPLE[person_id][9][-1][0] + PEOPLE[person_id][12][-1][0]
            knee = PEOPLE[person_id][13][-1][0] + PEOPLE[person_id][10][-1][0]
            foot = PEOPLE[person_id][19][-1][0] + PEOPLE[person_id][22][-1][0]

            #cv2.rectangle(img, top_left,bottom_right, (0, 255, 0), 5)
            cv2.putText(img, "Person "+str(person_id), (int(nose[0]),int(eye_R[1]-100)), font, 2, (0,0,0), 1, cv2.LINE_AA)
            #direction = test_mult_people_helper.map_state_change_to_motion(PEOPLE_CHANGE,PEOPLE)   #img = cv2.rectangle(img,(l_ear[0],eyebrow[1]),(r_ear[0],nose[1]),(0,255,0),3)
            try:
                (horiz,vert,seating_pos,missing_ear,missing_eye) = test_mult_people_helper.check_face_angle(PEOPLE,person_id)
            except:
                (horiz,vert) = (0,0)
                cv2.putText(img, "Error", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)

            #if (person_id == 0): cv2.putText(img, "horiz: {:.2f} vert: {:.2f} ".format(horiz,vert), (20,50), font, 2, (255,255,255), 2, cv2.LINE_AA)

            if ((horiz,vert) != (0,0)): 
                '''if person_id not in INTERACT:
                    if knee != 0: 
                        cv2.putText(img, "Too Far", (int(nose[0]),int(eye_R[1]-70)), font, 2, (0,0,0), 1, cv2.LINE_AA)
                    else: 
                        cv2.putText(img, "Potential Player", (int(nose[0]),int(eye_R[1]-70)), font, 2, (0,0,0), 1, cv2.LINE_AA)
                        #initiate_conversation()
                        if hip != 0: INTERACT.add(person_id)
                else:'''
                if foot == 0 and knee != 0:
                    #add to potential players in victor context
                    if person_id in VICTOR_CONTEXT["GAME_CONTEXT"]["players_id"]:
                       #remove_from_victor_state(person_id)
                       add_to_victor_state_left(person_id)
                    else:
                        add_to_victor_state_potential(person_id)
                        cv2.putText(img, "Potential Player", (int(neck[0]),int(neck[1]-70)), font, 2,(0,0,0), 1, cv2.LINE_AA)

                elif knee == 0:
                    if (seating_pos == "center"):
                        add_to_victor_state_players(person_id)

                        cv2.putText(img, "Sitting: Center", (int(nose[0]),int(eye_R[1]-70)), font, 2, (0,0,0), 1, cv2.LINE_AA)

                        cv2.putText(img, "Center",(img_width//2,(img_height*9//10)), font, 2,  color=[255, 255, 255], lineType=cv2.LINE_AA, thickness=2)
                        find_sitting_center_head_position(vert,horiz,nose,font,eye_R,cv2,img)
                    elif (seating_pos == "left"):
                        cv2.putText(img, "Sitting: Left", (int(nose[0]),int(eye_R[1]+70)), font, 2, (0,0,0), 1, cv2.LINE_AA)
                        cv2.putText(img, "Left",(img_width*4//5,(img_height*9//10)), font, 2,  color=[255, 255, 255], lineType=cv2.LINE_AA, thickness=2)
                        find_sitting_left_head_position(vert,horiz,nose,font,eye_R,cv2,img,missing_ear,missing_eye)
                    elif (seating_pos == "right"):
                        cv2.putText(img, "Sitting: Right", (int(nose[0]),int(eye_R[1]-70)), font, 2, (0,0,0), 1, cv2.LINE_AA)
                        cv2.putText(img, "Right",(img_width//5,(img_height*9//10)), font, 2,  color=[255, 255, 255], lineType=cv2.LINE_AA, thickness=2)

                        find_sitting_right_head_position(vert,horiz,nose,font,eye_R,cv2,img,missing_ear,missing_eye)
                else:
                    cv2.putText(img, "Too Far", (int(neck[0]),int(neck[1]-70)), font, 2, (0,0,0), 1, cv2.LINE_AA)

            
        cv2.namedWindow("image",cv2.WINDOW_NORMAL)
        cv2.imshow("image",img)
        cv2.waitKey(5)
        cv2.imwrite(image_id,img)

'''
#obsolete, moved to FSM control
def initiate_conversation():
    time.sleep(10)
    set_victor_speech("Hey you! Want to play scrabble?")
'''

def find_sitting_right_head_position(vert,horiz,nose,font,eye_R,cv2,img,missing_ear,missing_eye):
    global VICTOR_SPEAK 
    if (vert > -16): 
        if (missing_eye):
            cv2.putText(img, "Look up away from robot", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "look up at robot", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)

    elif ( vert <-16 and vert > -30):
        if (missing_eye):
            cv2.putText(img, "Look center away from robot", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
            #set_victor_speech("RIGHT, pay attention to me!")
        else:
            cv2.putText(img, "Look center at robot", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
            #set_victor_speech("RIGHT, what are you looking at?")

    else:
        if (missing_eye):
            cv2.putText(img, "Look down away from robot", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "Look down at robot", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
            #VICTOR_SPEAK = (time.time(),"Hi RIGHT, would you like to play a game?")
            #set_victor_speech("RIGHT, would you like to play scrabble?")

def find_sitting_left_head_position(vert,horiz,nose,font,eye_R,cv2,img,missing_ear,missing_eye):
    
    if (vert > -16): 
        if (missing_eye):
            cv2.putText(img, "Look up away from robot", (int(nose[0]-150),int(eye_R[1]+150)), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "look up at robot", (int(nose[0]-150),int(eye_R[1]+150)), font, 2, (0,0,0), 1, cv2.LINE_AA)

    elif ( vert <-16 and vert > -30):
        if (missing_eye):
            cv2.putText(img, "Look center away from robot", (int(nose[0])-150,int(eye_R[1]+150)), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "Look center at robot", (int(nose[0]-150),int(eye_R[1]+150)), font, 2, (0,0,0), 1, cv2.LINE_AA)
    else:
        if (missing_eye):
            cv2.putText(img, "Look down away from robot", (int(nose[0]-150),int(eye_R[1]+150)), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "Look down at robot", (int(nose[0]-150),int(eye_R[1]+150)), font, 2, (0,0,0), 1, cv2.LINE_AA)

def find_sitting_center_head_position(vert,horiz,nose,font,eye_R,cv2,img):
    global VICTOR_SPEAK
    if (vert <-14 and vert > -30):
        if (abs(horiz) < 5):
            cv2.putText(img, "looking straight", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        elif (horiz < 5):
            cv2.putText(img, "center right", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "center left", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
    elif (vert < -30):
        if (abs(horiz) < 5) :
            cv2.putText(img, "down center", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
            #set_victor_speech("Hi CENTER, tap the board to play!")
        elif (horiz < 5):
            cv2.putText(img, "down right", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "down left", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
            #set_victor_speech("Great! Can't wait for another win.")
    elif (vert > -14):
        if (abs(horiz)< 5) :
            cv2.putText(img, "up center", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        elif (horiz <5) :
            cv2.putText(img, "up right", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "up left", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)

def set_victor_speech(statement):
    global VICTOR_SPEAK

    if VICTOR_SPEAK == None:
        VICTOR_SPEAK = (time.time(),statement)
    elif time.time() - VICTOR_SPEAK[0] > 5:
        VICTOR_SPEAK = (time.time(),statement)

#add to potential players in victor context
def add_to_victor_state_potential(person_id):
    VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"].add(person_id)
    VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["number_potential"] = len(VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"])

def add_to_victor_state_left(person_id):
    VICTOR_CONTEXT["LEFT_GAME"]["left_id"].add(person_id)
    VICTOR_CONTEXT["LEFT_GAME"]["number_left"] = len(VICTOR_CONTEXT["LEFT_GAME"]["left_id"])


def add_to_victor_state_players(person_id):
    if person_id in VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"]:
        VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"].remove(person_id)
        VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["number_potential"] = len(VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"])

    VICTOR_CONTEXT["GAME_CONTEXT"]["players_id"].add(person_id)
    VICTOR_CONTEXT["GAME_CONTEXT"]["number_players"] = len(VICTOR_CONTEXT["GAME_CONTEXT"]["players_id"])

    print(VICTOR_CONTEXT)

def remove_from_victor_state(person_id):
    if person_id in VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"]:
        VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"].remove(person_id)
        VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["number_potential"] = len(VICTOR_CONTEXT["POTENTIAL_PLAYERS"]["potential_id"])
    elif person_id in VICTOR_CONTEXT["GAME_CONTEXT"]["players_id"]:
        #TODO: remove from c l r dict
        VICTOR_CONTEXT["GAME_CONTEXT"]["players_id"].remove(person_id)
        VICTOR_CONTEXT["GAME_CONTEXT"]["number_players"] =len(VICTOR_CONTEXT["GAME_CONTEXT"]["players_id"])



'''
def find_sitting_center_head_position(vert,horiz,nose,font,eye_R,cv2,img):
    if (abs(horiz) < 27) and  (abs(vert) <10):
            cv2.putText(img, "looking straight", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
    if (abs(vert) < 10 ):
        if (horiz < -90):
            cv2.putText(img, "center left", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        if (horiz < -25) :
            cv2.putText(img, "center right", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
    if (vert < -10):
        if (abs(horiz) < 25) :
            cv2.putText(img, "down center", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        elif (horiz < -90):
            cv2.putText(img, "down left", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "down right", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)

    if (vert > 10):
        if (abs(horiz)< 25) :
            cv2.putText(img, "up center", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        if (horiz > 25):
            cv2.putText(img, "up left", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
        if (horiz < -25) :
            cv2.putText(img, "up right", (int(nose[0]),int(eye_R[1])), font, 2, (0,0,0), 1, cv2.LINE_AA)
'''

def run_all_files():
    order_directory()
    print("in run all files......................... ", ANGLE_PIX)
    flag = False
    b = 0
    
    #if (VIDEO.isOpened()==False): print("error in opening video stream");
    #time.sleep(5)
    for path in list_keypoint_json:

        '''if b == 287:
            VIDEO.release()
            cv2.destroyAllWindows()
            return

        '''
        if path[-14:] == "keypoints.json":
            print("\n")
            #print("len of people ", len(PEOPLE))
            print(path)
            if b >90:
                decode_keypoints(FOLDER_PATH+path)
            b += 1
        elif path[-4:] ==".png":
            decode_images(FOLDER_PATH+path)

    cv2.destroyAllWindows()

def save_output():
    image_folder =FOLDER_PATH+ 'output_images/'
    video_name = FOLDER_PATH+"output_images/"+'output_video.avi'
    
    images = []
    for img in os.listdir(image_folder):
        images.append(img)

    #list of json file in order
    images.sort()

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape

    #fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
    video = cv2.VideoWriter(video_name, fourcc, 30, (width,height))

    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))

    cv2.destroyAllWindows()
    video.release()
    return

def main():

    path = FOLDER_PATH+"output_images"
    #path = "output_images"
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)
    run_all_files()
    #print("Total People Entered is ", PEOPLE_ENTERED)
    #print("Total People Left is ", PEOPLE_LEFT)

    save_output()
    print("Output Save: Success")
    return VICTOR_CONTEXT

if __name__ == "__main__":
    main()
