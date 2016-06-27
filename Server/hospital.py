import vrep
try:
    import vrep
except:
    print('--------------------------------------------------------------')
    print('"vrep.py" could not be imported. This means very probably that')
    print('either "vrep.py" or the remoteApi library could not be found.')
    print('Make sure both are in the same folder as this file,')
    print('or appropriately adjust the file "vrep.py"')
    print('--------------------------------------------------------------')
    print('')
import sys
import ctypes
import time
import random
import simpy

def clockTime(t):
    t = round(t)
    t = t % 86400
    # Avoid division by 0
    if t < 60:
        if t < 10: return '00:00:0' + str(t)
        else: return '00:00:' + str(t)
    (m,s) = divmod(t, 60)
    (h,m) = divmod(m, 60)
    time = ''
    for n in [h,m,s]:
        if n < 10: time += '0' + str(n)
        else: time += str(n)
        time += ':'
    return(time[:-1])  # Ignore last ':'

def process_order(env, res, order, patID):
    t0 = env.now
    print('*ORDER* Patient #%d ordered %s at %s' % (patID, order, clockTime(t0)))
    with res.request() as req:  # Request event
        yield req  # Wait for a request
        t1 = env.now  # Done with queue (seize)
        print('Processing %s order from patient #%d at %s' % (order, patID, clockTime(t1)))
        # Start robot process in V-REP
        simulationProcessTime = waitForRobot(order, patID)
        yield env.timeout(simulationProcessTime)
        t2 = env.now  # Done with process (release)
    print('Robot is done with the order at %s' % clockTime(t2))
    # Note here 'return' can work as well, but only for Python > 3.3
    env.exit((t0, t1-t0, t2-t1))
    
def generate_order(env, res, order, patID, data):
    tfactor = 60  # Minutes to seconds
    while True:
        # Generate some really random processes
        if order == 'food':
            lamb = 5 + 20*(patID % 6)  # In minutes
            k = 3  # Hunger increases over time
            delay = random.weibullvariate(lamb*tfactor, k)
        else:
            a, b = 10, 20+20*(patID % 6)
            mu = random.randint(a, b)  # Random mean in minutes
            sd = 10  # Standard deviation in minutes
            delay = abs(random.normalvariate(mu*tfactor, sd*tfactor))
        yield env.timeout(delay)  # Interarival time
        # Delay is complete, order arrived
        # Start process and return queue time and process time
        (t_arrival, qtime, ptime) = yield env.process(process_order(env,res,order,patID))
        # Update data
        data.append((patID, order, clockTime(t_arrival), round(qtime,3), round(ptime,3)))
    
def waitForRobot(order, patID):
    time.sleep(1)
    ptime = None
    orderID = 16*(order == 'linen') + patID
    signalTo = 'order_ToVREP'
    signalBack = 'ptime_FromVREP'
    # Send order ID to be processed
    vrep.simxSetIntegerSignal(clientID,signalTo,orderID,vrep.simx_opmode_oneshot)
    # Start the receiving process
    err,ptime=vrep.simxGetFloatSignal(clientID,signalBack,vrep.simx_opmode_streaming)
    # While we haven't received anything
    while not ptime:
        err,ptime=vrep.simxGetFloatSignal(clientID,signalBack,vrep.simx_opmode_buffer)	
    if err != vrep.simx_return_ok:
        print('!!!\nAn error occured while receiving data from vrep...\n!!!')
    # Clear signal
    vrep.simxClearFloatSignal(clientID,signalBack,vrep.simx_opmode_oneshot)
    # Return the signal received (processing time)
    return ptime

def interactWithVREP():
    numPat = 16  # Number of patients
    startingTime = 0
    runningTime = 20*60  # In seconds
    data = []
    # Set up the simulation environment (real-time)
    env = simpy.rt.RealtimeEnvironment(factor=1,strict=False)
    #env = simpy.Environment()
    # Our resource (the robot) can handle one order at a time
    robot = simpy.Resource(env, capacity=1) 
    # Add processes
    procs = []
    procs = [env.process(generate_order(env,robot,'food',i+1,data)) for i in range(numPat)]
    procs += [env.process(generate_order(env,robot,'linen',i+1,data)) for i in range(numPat)]
    # Run simulation
    print('Simulation started at %s\n' % clockTime(startingTime))
    env.run(until=runningTime)
    numOrders = len(data)
    numFoodOrders = len([x for x in data if x[1]=='food'])
    # Results
    print()
    print('Simulation ended at %s' % clockTime(runningTime))
    print('Food orders processed = %d' % numFoodOrders)
    print('Linen orders processed = %d' % (numOrders-numFoodOrders))
    print('Orders not processed = %d' % len(robot.queue))
    print()
    print('The data of the processed orders are as follows:')
    print('(Patient ID, Type of order, Arrival time, Time in queue, Time processing)')
    for d in data: print(d)
    print()

start_time = time.time()
# For continuos remote API use 19997, else use 19999
port = 19997
print('Starting connection...')
vrep.simxFinish(-1)  # just in case, close all opened connections
clientID = vrep.simxStart('127.0.0.1', port, True, True, 5000, 5)  # Connect to V-REP
if clientID != -1:
    print('Connected.')
    # Check status bar in V-REP to confirm connection
    vrep.simxAddStatusbarMessage(clientID,'Hello V-REP! (from a python script)',vrep.simx_opmode_oneshot) 
    if port == 19997:
        vrep.simxStartSimulation(clientID, vrep.simx_opmode_oneshot)
    # Start process here
    time.sleep(1)  # Make sure simulation started and ready
    interactWithVREP()  # clientID is global
    # Try this for a sample process
    if False:
        p1 = waitForRobot('food',11)
        print('ptime = %.2f seconds' % p1)
        p2 = waitForRobot('linen',6)
        print('ptime = %.2f seconds' % p2)

    # Pause the simulation before closing connection
    if port == 19997:
        vrep.simxPauseSimulation(clientID, vrep.simx_opmode_oneshot)
    # Make sure that the last command sent out had time to arrive
    vrep.simxGetPingTime(clientID)
    # Now close the connection to V-REP:
    vrep.simxFinish(clientID)
    print('Closing connection... Bye!')
    time.sleep(2)
else:
    print ('Failed connecting to remote API server')
print()
print ('Program ended.')
print('Time spent = %.2f minutes.' % ((time.time()-start_time)/60))
