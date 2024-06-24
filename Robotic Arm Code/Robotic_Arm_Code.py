import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from adafruit_servokit import ServoKit
import math

# Replace this with the path to your service account key file
cred = credentials.Certificate("key.json")

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://arm4-acb76-default-rtdb.firebaseio.com/'
})

nbPCAServo=16 
pca = ServoKit(channels=16)

pca.servo[1].set_pulse_width_range(500 , 2500)
pca.servo[1].angle = 90

pca.servo[2].set_pulse_width_range(500 , 2500)
pca.servo[2].angle = 180

pca.servo[7].set_pulse_width_range(500 , 2500)
pca.servo[7].angle = 0

pca.servo[11].set_pulse_width_range(500 , 2500)
pca.servo[11].angle = 70

def arm(x,y,L):
    l=20
    x=float(x)
    y=float(y)
    L=str(L)
    if x==0 and y==0:
#             pca.servo[0].set_pulse_width_range(500 , 2500)
#             pca.servo[0].angle = 90
#             pca.servo[1].set_pulse_width_range(500 , 2500)
#             pca.servo[1].angle = 180
            dist=0
            alpha = math.degrees(math.acos(dist/(2*l)))
            #servo1.ChangeDutyCycle(2+(alpha/18))
            pca.servo[1].set_pulse_width_range(500 , 2500) 
            print(alpha)    
            beta = 180-(2*alpha)
            #servo2.ChangeDutyCycle(2+(beta/18))
            pca.servo[2].set_pulse_width_range(500 , 2500)
            pca.servo[1].angle = alpha
            time.sleep(2)
            pca.servo[2].angle = 175-beta
            print(beta)
            time.sleep(2)
            pca.servo[7].set_pulse_width_range(500 , 2500)
            pca.servo[7].angle = 5
    else:    
        dist = math.sqrt((x**2)+(y**2))+4
        print("dist  : ",dist)
        theta = math.degrees(math.acos(x/(dist)))-18
        pca.servo[7].set_pulse_width_range(500 , 2500)
        print("Base Moving : ",theta)
        if theta<2:
            ef=theta
        else:
            ef=theta-2
        for i in range(3,int(ef)) :
            pca.servo[7].angle = i
            time.sleep(0.03)
        
        alpha = math.degrees(math.acos((dist+4)/(2*l)))
        print("AAAAAAAlpha : ",alpha)
        #servo1.ChangeDutyCycle(2+(alpha/18))
    #         pca.servo[1].set_pulse_width_range(500 , 2500)
    #         pca.servo[1].angle = alpha
        #print("alpha : ",alpha)
        time.sleep(1)
        
        beta = 180-(2*alpha)
        #servo2.ChangeDutyCycle(2+(beta/18))
        pca.servo[2].set_pulse_width_range(500 , 2500)
        print("ARM 2 Moving : ",175-beta)
        cd=int(180-beta)
        for j in range(180,cd,-1) :
            pca.servo[2].angle = j
            time.sleep(0.02)
        
        time.sleep(1)
        print("Gripper Opening")
        for l in range(70,9,-1) :
            pca.servo[11].angle = l
            time.sleep(0.02)
        #pca.servo[11].angle = 0
        
        time.sleep(1)
        
        pca.servo[1].set_pulse_width_range(500 , 2500)
        ab=int(alpha)-1+10
        print("ARM 1 Moving : ",alpha)
        for z in range(90,ab,-1) :
            pca.servo[1].angle = z
            time.sleep(0.02)
        
        time.sleep(1)
        
        print("Gripper Closing")
        for l in range(10,56) :
            pca.servo[11].angle = l
            time.sleep(0.02)
        #pca.servo[11].angle = 55
        
        time.sleep(2)
        #pca.servo[1].angle = 70
        
        print("ARM 1 Moving  ")         
        for z in range(ab,91) :
                 pca.servo[1].angle = z
                 time.sleep(0.02)    
        time.sleep(1)
        print("ARM 2 Moving ")
        pca.servo[2].set_pulse_width_range(500 , 2500)
       
        if cd<130:
            for z in range(cd,136) :
                pca.servo[2].angle = z
                time.sleep(0.02)
        else:
            for z in range(cd,134,-1) :
                pca.servo[2].angle = z
                time.sleep(0.02)

        time.sleep(1)
        #pca.servo[7].angle = 180
        
        
        
        print("Base Moving")
        for z in range(int(ef),146) :
                pca.servo[7].angle = z
                time.sleep(0.02)
        time.sleep(1)
        print("Gripper Opening")
        for l in range(55,9,-1) :
            pca.servo[11].angle = l
            time.sleep(0.02)
        
        #pca.servo[11].angle = 0
        time.sleep(1)
        
        print("Gripper Closing")
        for l in range(10,71) :
            pca.servo[11].angle = l
            time.sleep(0.01)
        
        #pca.servo[11].angle = 70
        time.sleep(2)
        
        print("Base Moving")
        for z in range(135,2,-1) :
                pca.servo[7].angle = z
                time.sleep(0.02)
        
        time.sleep(1)
        print("ARM 2 Moving")
        for z in range(135,181) :
                pca.servo[2].angle = z
                time.sleep(0.02)
        
        #pca.servo[7].angle = 0
        



# Reference to the root of your database
ref = db.reference('/')
snapshot = ref.get()
ref.delete()


while True:
	# Get the snapshot of the data
	snapshot = ref.get()

	# If there's data, extract values and pass them to another function
	if snapshot:
		# Extract values from snapshot
		origin_x = snapshot.get('origin_x')
		origin_y = snapshot.get('origin_y')
		label = snapshot.get('Label')

		# Pass values to another function
		arm(origin_x, origin_y, label)
		ref.delete()
	else:
		print("No Object...")
