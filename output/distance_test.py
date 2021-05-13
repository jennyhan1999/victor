from PIL import Image,ImageDraw
import math

##################################################################
################# test with angle from ceiling as reference ######
################# uses heigh of camera and height of ceiling #####
##################################################################

test2 = Image.open("./test_distance_with_feet/000000000022_rendered.png")
#print("col is ",test2.size[0])
#print("row is ",test2.size[1])


draw = ImageDraw.Draw(test2) 

draw.line((0,360, 1280,360), fill=1000, width = 3)
draw.line((640,0, 640,720), fill=1000, width = 3)

draw.line((0,180,1280,180),fill = 0 ) #where the door top ends
draw.line((0,150,1280,150),fill = 0xFF) #where the ceiling is

angle_to_ceil = 0.151844
ceil_h = 90
cam_h = 46
o = ceil_h - cam_h
ceil_dist = 300

angle_per_pixel = angle_to_ceil/(360-150)
print("ange per pix is ", angle_per_pixel)

draw.line((0,570,1280,570),fill = 0xFF) #where the ceiling is
angle_bottom = angle_per_pixel * abs(360-570) #bottom to middle
print("floor angle from door is ", angle_bottom)
print("top of door angle is ", angle_per_pixel * abs(360-180))
angle_top = angle_per_pixel * abs(360-180)

top_half = ceil_dist * math.atan(angle_top)
bottom_half = ceil_dist * math.atan(angle_bottom)
print("door height is ", top_half + bottom_half) #estimated height of 84 inches, reality is 83 inches!


########################################################################
############ test with number pix from feet ############################
########################################################################

#me distance is 234 inches (550,650)
#trash distance is 187 inches (755,720)
#door distance is 300 inches
#chairs past door 390 inches


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

	#slope = (y2-y1)/(x2-x1)
	change_x = x2-x1
	change_y = y2-y1
	mult = 10
	return x2 + mult*change_x, y2+mult*change_y
'''
#line 1
A = (0, 0)
B = (5, 19)

#line 2
C = (-2.333, 0)
D = (0, 0)

print line_intersection((A, B), (C, D))
'''


#draw.line((0,360, 1280,360), fill=1000, width = 3)
#draw.line((640,0, 640,720), fill=1000, width = 3)
'''
for i in range (test2.size[0]): #horizontal lines
	if i < 360:
		continue
	elif i % 20 == 0:
		draw.line((0,i,1280,i), fill = 0)
		draw.text((10,i), str(i))
'''

for i in range(test2.size[0]): #vertical lines
	if i % 100 == 0:
		draw.line((i,720,600,400),fill = 0)
		draw.text((i,710), str(i))

	elif i % 50 == 0:
		draw.line((i,720,600,400),fill = 0xFF) #perspective midline

new_horiz_y = 720
horiz_line_curr = ((0,655),(1280,655))
horiz_line_prev = ((0,720),(1280,720))
first_perspective_line = ((0,720),(600,400))
second_perspective_line = ((100,720),(600,400))
midline = ((50,720),(600,400))
#j = 0
start_ref_diag = (0,720)
c = 0

while new_horiz_y > 400:
	if c == 0:
		draw.line((horiz_line_curr[0],horiz_line_curr[1]))
		
	else:
		pt1_ref_line = line_intersection(first_perspective_line,horiz_line_prev) #first pt, prev horizontal line
		midline_intersect = line_intersection(midline,horiz_line_curr) #horizontal line intersection with midline 
		midline_extend = extend_line(((pt1_ref_line[0],pt1_ref_line[1]),(midline_intersect[0],midline_intersect[1]))) #extend pt1 and midline to make a longer line
		pt2_ref_line = line_intersection((pt1_ref_line,midline_extend),second_perspective_line) #see where this longer line intersects with second perspective line

		new_horiz_y = pt2_ref_line[1] #new horizontal line

		draw.line((pt1_ref_line,pt2_ref_line))
		horiz_line_prev = horiz_line_curr #update prev and curr
		horiz_line_curr = (0,new_horiz_y),(1280,new_horiz_y)

		pt1_horiz = line_intersection(first_perspective_line,horiz_line_prev)
		pt2_horiz = line_intersection(second_perspective_line,horiz_line_prev)
		#draw.line((pt1_horiz,1280-pt2_horiz[0],pt2_horiz[1]))
		#draw.line((pt1_ref_line,horiz_line_curr[1]))
		draw.line((horiz_line_curr))
	c += 1
	print("difference in y is ",horiz_line_prev[1][1]-horiz_line_curr[1][1])




me_to_trash = 47
pix_me_to_trash = 70


test2.show()


