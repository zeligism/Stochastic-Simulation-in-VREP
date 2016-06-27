There is a video in the folder 'Scenes' demonstrating a sample of what this scenario will look like in V-REP.

However, when using actual real-time simulation using SimPy, we may want to wait for several minutes at times to see an acual order coming, so we used a sample process instead of a random one in video for demonstration purposes only. There is a screenshot showing how the actual real-time simulation integration would look like (the perfect timing of the first order was pure luck). Notice the status message bar in V-REP, and youBot going straight to the kitchen.

The screenshot and the video can be found in the folder 'Visuals'.

To run the scenario, simply open the scene 'Scenario 2.ttt' in V-REP, and then run the script 'hospital.py'.

Most of the code for this scene is in the threaded child script of youBot (Inside the path object).