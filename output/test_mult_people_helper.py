from __future__ import division
import math
import head_position # test_multiple_people
import kalman_filter_test

MOTION_MAPPING = {
  0: "Waving",
  1: "Standing",
  2: "Sitting",
  3: "Looking at Robot",
  4: "Walking Towards",
  5: "Eye Contact"
}

PERSON_STATE = {
  0: False,
  1: False,
  2: False,
  3: False,
  4: False,
  5: False
}


def distance(x1,y1,x2,y2):
  return math.sqrt((x2-x1)**2+(y2-y1)**2)

def distance_1d(x1,x2):
  return abs(x2-x1)

def speed(x1,y1,t1,x2,y2,t2):
  dist = distance(x1,y1,x2,y2)
  time = t2-t1
  try:
    return (dist/time)
  except:
    return

def angle(x1,y1,x2,y2):
  return math.degrees(math.atan2(y2-y1, x2-x1))

def average(c,l):
  tot = 0
  for i in range(len(l)):
    tot += l[i][c]
  return tot/(len(l))

def difference(l):
  if l == []:
    #print("got here")
    return 
  smallest_x, smallest_y = l[0][0],l[0][1]
  biggest_x, biggest_y = l[0][0],l[0][1]
  for i in range(1,len(l)):
    if l[i][0] > biggest_x:
      biggest_x = l[i][0]
    if l[i][1] > biggest_y:
      biggest_y = l[i][1]
    if l[i][0] < smallest_x:
      smallest_x = l[i][0]
    if l[i][1] < smallest_y:
      smallest_y = l[i][1]

  
  return biggest_x-smallest_x, biggest_y-smallest_y


def check_eye_contact(PEOPLE):
  #print("checking eye contact....")
  #print(PEOPLE)

  for person_id in PEOPLE:
    prev_body_keypoints = PEOPLE[person_id]
    if (len(prev_body_keypoints[15]) == 0 or len(prev_body_keypoints[16]) == 0):
      continue

    #print("person id is ", person_id)
    prev_body_keypoints = PEOPLE[person_id]
    Reye = average(0,prev_body_keypoints[15])
    Leye = average(0,prev_body_keypoints[16])
    #print("Reye average is ", Reye)
    #print("Leye average is ", Leye)
    if (Reye == 0) or (Leye == 0):
      PERSON_STATE[5] = False
      #print(person_id, " looking away")
      continue

    PERSON_STATE[5] = True
    #print(person_id," looking at")
  
def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

def extend_line(line):
  x1 = line[0][0]
  y1 = line[0][1]
  x2 = line[1][0]
  y2 = line[1][1]

  change_x = x2-x1
  change_y = y2-y1
  mult = 10
  return x2 + mult*change_x, y2+mult*change_y


def check_direction(PEOPLE,person_id):
  torso_set = {0,1,8,9,12}
  direction = 0 #positive is right, negative is left
  for keypoint in torso_set:
    prev_val = None
    for tpl in PEOPLE[person_id][keypoint]:
      val = tpl[0]
      if prev_val == None:
        prev_val = val
      else:
        if prev_val > val : #going right
          direction += 1
        else:
          direction -= 1
  #print("direction is ", direction)
  return direction

def check_look_direction(PEOPLE,person_id):
    face_set = {0,15,16,17,18}
    result = dict() #1: up, 2:keft; 3:down 4:rihgt
    offset = 100
    for keypoint in face_set:
        for tpl in PEOPLE[person_id][keypoint]:
            

            #if (abs(horiz) < 25) and (abs(vert) < 25):
            #    return 5
            if keypoint == 15 or keypoint == 16:
                eye_y = tpl[1] 
                ear_y = (PEOPLE[person_id][17][0][1]+PEOPLE[person_id][18][0][1])//2
                nose_y = PEOPLE[person_id][0][0][1]
                #print("eye ",eye_y)
                #print("ear ",ear_y)
                #print("nose ",nose_y) 

                center_y = (eye_y + nose_y) //2
                if eye_y == 0  or nose_y == 0 or  PEOPLE[person_id][18][0][1] == 0 or PEOPLE[person_id][17][0][1] == 0:
                    continue


                elif center_y > (ear_y - 70):
                    #print("looking down")
                    return 2

            if keypoint == 0:
                eye_y = (PEOPLE[person_id][15][0][1]+PEOPLE[person_id][16][0][1])//2
                nose_y = tpl[1]
                ear_y = (PEOPLE[person_id][17][0][1]+PEOPLE[person_id][18][0][1])//2

                center_y = (eye_y + nose_y) //2
                if nose_y == 0 or  PEOPLE[person_id][18][0][1] == 0 or PEOPLE[person_id][17][0][1] == 0 or PEOPLE[person_id][16][0][1] == 0 or PEOPLE[person_id][15][0][1] == 0:
                    continue


                elif center_y <(ear_y - 30):
                    #print("looking up")
                    return 1
                
            if keypoint == 17:
                if tpl == (0,0,0):
                    #print("looking right")
                    return 3


            if keypoint == 18:
                if tpl == (0,0,0):
                    print("looking left");
                    return 4
    return 0

def check_face_angle(PEOPLE,person_id):
    #x: left and right calculate angle look
    #y: calculate angle up and down
    face_set = {0,1}
    #person_id = 0
    seating_pos = ""
    missing_ear = ""
    missing_eye = ""
    for tpl in PEOPLE[person_id][0]:
        try:
            nose_arr = kalman_filter_test.kalman_array(PEOPLE[person_id],0)
            nose_x_arr, x_difference = kalman_filter_test.get_x_val(nose_arr)
            nose_x = sum(nose_x_arr) / len(nose_x_arr) 

            neck_arr = kalman_filter_test.kalman_array(PEOPLE[person_id],1)
            neck_x_arr, x_difference = kalman_filter_test.get_x_val(neck_arr)
            neck_x = sum(neck_x_arr) / len(neck_x_arr)
            
            #print("\nhelper: neck x is ",neck_x) 
            nose_y_arr, y_difference = kalman_filter_test.get_y_val(nose_arr)
            neck_y_arr, y_difference = kalman_filter_test.get_y_val(neck_arr)
            
            nose_y = sum(nose_y_arr) / len(nose_y_arr)
            neck_y = sum(neck_y_arr) / len(neck_y_arr)
            #print("helper: got here\n")

            #print("\nhelper: nose x is ",nose_x," nose y is ",nose_y)
           
            ear_r = PEOPLE[person_id][17][0]
            ear_l = PEOPLE[person_id][18][0]
            #print("ear r ",ear_r," ear l ",ear_l)
            if (ear_l == (0,0,0)): missing_ear = "l_ear"
            if (ear_r == (0,0,0)): missing_ear = "r_ear"
       
            eye_l = PEOPLE[person_id][16][0]
            eye_r = PEOPLE[person_id][15][0]
            if (eye_l == (0,0,0)): missing_eye = "l_eye"
            if (eye_r == (0,0,0)): missing_eye = "r_eye"
            '''
            ear_r_arr = kalman_filter_test.kalman_array(PEOPLE[0],17)
            ear_r_arr_x, x_difference = kalman_filter_test.get_x_val(ear_r_arr)
            ear_r_x = sum(ear_r_arr_x) / len(ear_r_arr_x)
            print("ear r x is ", ear_r_x)
            ear_l_arr = kalman_filter_test.kalman_array(PEOPLE[0],16)
            ear_l_arr_x, x_difference = kalman_filter_test.get_x_val(ear_l_arr)
            ear_l_x = sum(ear_l_arr_x) / len(ear_l_arr_x)
            print("ear l x is ", ear_l_x)
            '''
            '''
            #nose_x = tpl[0]
            nose_y = tpl[1]
            #neck_x = PEOPLE[person_id][1][0][0]
            neck_y = PEOPLE[person_id][1][0][1]
            
            '''
        except:
            return (0,0)
        horiz = ((nose_x - neck_x)*.5)
        
        offset = 270 #nose smaller than neck

        vert = 0

        if (450 < neck_x and neck_x < 690):
            #print("HELPER ",person_id," ",neck_x,"  center");
            seating_pos = "center"
        if (neck_x > 690):
            #print("HELPER ",person_id," ",neck_x,"  left");
            seating_pos = "left"
        if (neck_x < 340):
            #print("HELPER ",person_id," ",neck_x,"  right");
            seating_pos = "right"

        if ((neck_y - nose_y) > offset):
            #print("looking up") #up is 330
            #print("up vert angle is ",((neck_y-nose_y-offset)*.7))
            vert = (neck_y-nose_y-offset)*.7
        else:
            #print("looking down")#down is 150
            #print("down vert angle is ",((nose_y-neck_y+offset)*(-.3)))
            vert = (nose_y-neck_y+offset)*(-.3)


        if nose_x == 0 or neck_x == 0:
            #print("horixontal angle cannot be calculated")
            horiz = 0
            continue
        if nose_y == 0 or neck_y == 0:
            #print("verticle angle cannot be calculated");
            vert = 0
            continue
        return (horiz,vert,seating_pos,missing_ear,missing_eye)

def line_of_vision(PEOPLE,horiz,vert,img_size):
    person_id = 0
    for tpl in PEOPLE[person_id][15]:
        eye_x = (tpl[0]+PEOPLE[person_id][16][0][0])//2
        eye_y = (tpl[1]+PEOPLE[person_id][16][0][1])//2
    
        r,xr,yr = 500,500,500
         
        if horiz>0:
            xr = 10000
            yr = -10000
        x = xr*math.sin(horiz) * math.cos(vert);
        z = r*math.sin(horiz) * math.sin(vert);
        y = yr*math.sin(vert);

        
            
        print("from helper ",[(eye_x,eye_y),(x,y)])
        if tpl[0] == 0 or tpl[1] == 0 or PEOPLE[person_id][16][0][0]==0 or  PEOPLE[person_id][16][0][1]==0 or x==0 or y==0:  return [0,0,0,0]
        '''if horiz>0:
            x = -abs(x)
            y = -abs(y)
        '''


        return [int(eye_x),int(eye_y),int(abs(x)),int(abs(y))]
        return extend(0,0,img_size[0],img_size[1],int(eye_x),int(eye_y),int(x),int(y))#[int(eye_x),int(eye_y),int(x),int(y)]


def extend(xmin, ymin, xmax, ymax, x1, y1, x2, y2):

    # based on (y - y1) / (x - x1) == (y2 - y1) / (x2 - x1)
    # => (y - y1) * (x2 - x1) == (y2 - y1) * (x - x1)
    m = (y2-y1)/(x2-x1)
    
    y_final = m*xmax+y1

    return [x1,y1,int(xmax),int(y_final)]
    



def map_state_change_to_motion(state_change_dict,PEOPLE):
  #check_face_angle(PEOPLE)
  return check_look_direction(PEOPLE,0)  
  
  #check_eye_contact(PEOPLE)
  #check_stand()
  #check_direction(PEOPLE,0)
  #check_wave(state_change_dict)
  #check_interaction()
  #check_walking_towards(state_change_dict)
  #return
