#!/usr/bin/python3

# Example demonstrating drawing on a tkinter canvas from a background
# process, periodically updating the image displayed.  This is
# appropriate only if the image rendering is computationally
# expensive.  A subprocess is necessary to avoid having a frozen user
# interface during image rendering.  Intermediate images and the final
# image can be saved to a file.

# To change the image being rendered, adjust the width and height
# values if desired and modify the draw() function.

import multiprocessing
import queue
import random
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

# The width of the drawing canvas in pixels
width=1000

# The height of the drawing canvas in pixels
height=800

# The base name of the file output when "Save" is clicked. An integer
# and imageFileExtension are appended to this name.  Existing files
# are not overwritten.
imageFileBaseName="pympcanvas"

# The output file extension (including the leading .); this controls
# the file format as well.  png is lossless.
imageFileExtension=".png"

# The polling interval for communication between the drawing and GUI
# processes, in milliseconds.  Image updates take two polling
# intervals.
pollInterval=125

# Draws the image.  This is called from a separate process.
# drawerQueue and tkQueue are queues needed by the
# periodicallyUpdateImage() and notifyImageComplete() functions that
# must be called by this method.  periodicallyUpdateImage() should be
# called periodically to send intermediate images to the GUI, and the
# function should return if periodicallyUpdateImage() returns True.
# Call notifyImageComplete() before returning when the drawing is
# complete (unless periodicallyUpdateImage() has already returned
# True).
def draw(drawerQueue, tkQueue):
    # Flag to indicate that the GUI requested that we exit
    drawerQuitFlag=False

    # Create an image and a drawing context to draw on it
    image=Image.new('RGBA', (width, height), (255, 255, 255, 255))
    drawContext=ImageDraw.Draw(image)


    A=(random.randrange(width/4, 3*width/4), random.randrange(0, height/10))
    B=(random.randrange(0, width/10), random.randrange(3*height/4, height))
    C=(random.randrange(9*width/10, width), random.randrange(3*height/4, height))

    startingPoints=[A,B,C]

    Pi=A

    # Draw the image.  This is a tight loop that periodically calls
    # periodicallyUpdateImage().
    while not drawerQuitFlag:

        # periodicallyUpdateImage() takes some time.  Call it
        # occasionally, but not every time through the loop.
        for i in range(10000):
            # As a simple demo, colour a random pixel using a colour
            # derived from the position.
            # x=random.randrange(0, width)
            # y=random.randrange(0, height)

            P=startingPoints[random.randint(0,2)]
            x=(P[0]+Pi[0])/2
            y=(P[1]+Pi[1])/2
            Pi=(x,y)


            drawContext.point((x, y),
                              (int(255*x/(width-1)),
                               int(255*(height-1-y)/(height-1)),
                               int(255*(width-1-x)*y/(width-1)/(height-1)),
                               255))



        # periodicallyUpdateImage is called periodically to update the
        # image in the GUI.  The function returns true if the drawing
        # process must exit.  periodicallyUpdateImage must not be
        # called again after true has been returned.
        drawerQuitFlag=periodicallyUpdateImage(drawerQueue, tkQueue, image)

    # The example above never considers the drawing done.  But if the
    # image is done, call notifyImageComplete() before exiting, unless
    # periodicallyUpdateImage() returned True.
    if not drawerQuitFlag:
        notifyImageComplete(drawerQueue, tkQueue, image)



# The code above this comment is all that needs to be understood to
# generate images.  Read on to understand the inner workings if you
# are interested.

# Communication between the drawing process and the GUI is done using
# two queues.  Messages put on the tkQueue queue are read by the GUI
# process.  drawerQueue is read by the drawing process.  The classes
# below are the messages sent on the queues.

# Sent by the GUI to the drawing process to request that it exit.  The
# drawing process must respond with QuitResponse then exit unless it
# has already sent a DrawingDoneNotification.  The GUI process sends
# no further messages on the drawing queue after this one.
class QuitRequest:
    pass

class QuitResponse:
    pass

# Sent to the GUI to indicate that the drawing process is done.  The
# drawing process must continue to read its queue until it receives
# DrawingDoneAcknowledgement or QuitRequest.
class DrawingDoneNotification:
    pass

# Sent by the GUI to acknowledge the DrawingDoneNotification unless it
# has already sent a QuitRequest.
class DrawingDoneAcknowledgement:
    pass

# Sent by the GUI to request an updated image from the drawing
# process.  The GUI will not send this message again until an
# ImageUpdateResponse is received.
class ImageUpdateRequest:
    pass

# Sent by the drawing process to update the image shown in the GUI.
# This can be sent even if no ImageUpdateRequest was received, but
# doing so will not result in more frequent updates of the GUI.
class ImageUpdateResponse:
    def __init__(self, image):
        self.image=image

# Helper function for the drawing process, that reads messages on the
# drawing process's queue and responds with an image update when
# asked.  image is the current image.  Returns True if a QuitRequest
# is received, and False otherwise.  If True is returned,
# periodicallyUpdateImage() and notifyImageComplete() must not be
# called, and the process should exit.
def periodicallyUpdateImage(drawerQueue, tkQueue, image):
    imageSent=False
    while True:
        try:
            message=drawerQueue.get_nowait()
        except queue.Empty:
            break
        if isinstance(message, QuitRequest):
            tkQueue.put(QuitResponse())
            return True
        elif isinstance(message, ImageUpdateRequest):
            if not imageSent:
                imageSent=True
                tkQueue.put(ImageUpdateResponse(image))
        else:
            # ignore unrecognized messages
            pass
    return False

# Called by the drawing process if the image is complete and
# periodicallyUpdateImage() has not indicated that the process has
# been asked to exit.  The function sends the final image to the GUI
# then sends a DrawingDoneNotification and waits for the
# acknowledgement.
def notifyImageComplete(drawerQueue, tkQueue, image):
    tkQueue.put(ImageUpdateResponse(image))
    tkQueue.put(DrawingDoneNotification())
    while True:
        message=drawerQueue.get()
        if isinstance(message, QuitRequest):
            # DrawingDoneNotification sent, so QuitResponse must not
            # be sent.
            return
        elif isinstance(message, DrawingDoneAcknowledgement):
            return
        else:
            # ignore unrecognized messages
            pass

# The code below was based on:
# https://docs.python.org/3/library/tkinter.html#a-simple-hello-world-program,
# https://pythonbasics.org/tkinter-canvas/,
# http://effbot.org/zone/tkinter-threads.htm, and
# https://stackoverflow.com/questions/34764535/why-cant-matplotlib-plot-in-a-different-thread

class PyMPCanvas(tk.Frame):
    def __init__(self, master=None):
        global root
        super().__init__(master)
        # The currently displayed image
        self.image=None

        # The currently displayed image, as a PhotoImage
        self.photoImage=None

        # Set to True when the user has asked the application to exit.
        self.quitFlag=False

        # Set to True when the drawing process has indicated it was done.
        self.drawingProcessDone=False

        # When saving an image, a counter is used in the file name to
        # avoid overwriting existing files.  This is the next counter
        # value to try.
        self.imageFileCounter=0
        self.master=master
        self.pack()
        self.create_widgets()

        # Register requestQuit as the function to call when the window
        # is closed.
        root.protocol('WM_DELETE_WINDOW', self.requestQuit)

        # Start the callbacks to the drawing process
        self.requestUpdate()

    # Create all the widgets for the GUI
    def create_widgets(self):
        self.canvas=tk.Canvas(self, bg="white", height=height, width=width)
        self.canvas.pack()

        # The canvas will hold a single image object
        self.canvasImage=self.canvas.create_image((0,0), anchor="nw")

        # The bottom frame contains a message area and a Save button.
        self.bottomFrame=tk.Frame(self)
        self.bottomFrame.pack(side="bottom", fill="x")
        self.saveButton=tk.Button(self.bottomFrame, text="Save", command=self.saveImage)
        self.saveButton.pack(side="right")
        self.messageText=tk.Label(self.bottomFrame)
        self.messageText.pack(side="left")

    # Display the specified message in the status area
    def displayStatus(self, message):
        self.messageText.config(text=message)

    # Initiates application shutdown.  Shut down if the drawing
    # process is already done.  Otherwise, request that it exit.
    def requestQuit(self):
        global drawerQueue
        self.quitFlag=True
        if self.drawingProcessDone:
            self.master.destroy()
        else:
            drawerQueue.put(QuitRequest())

    # Sends an ImageUpdateRequest if the drawing process is still
    # active.  Schedules a call to updateCanvas.
    def requestUpdate(self):
        global drawerQueue
        if not self.quitFlag and not self.drawingProcessDone:
            drawerQueue.put(ImageUpdateRequest())
        self.after(pollInterval, self.updateCanvas)

    # Processes the GUI queue
    def updateCanvas(self):
        global tkQueue
        global drawerQueue
        drawingDone=False # Becomes true if drawing process is done
        imageToDraw=None # The last image update received
        while True:
            try:
                message=tkQueue.get_nowait()
            except queue.Empty:
                break
            if isinstance(message, ImageUpdateResponse):
                imageToDraw=message.image
            elif isinstance(message, QuitResponse):
                self.master.destroy()
                return
            elif isinstance(message, DrawingDoneNotification):
                drawingDone=True
                if self.quitFlag:
                    # If quit has been requested, no QuitResponse is
                    # expected after DrawingDoneNotification.
                    self.master.destroy()
                    return
            else:
                pass
        if imageToDraw!=None:
            self.image=imageToDraw
            self.photoImage=ImageTk.PhotoImage(self.image)
            self.canvas.itemconfigure(self.canvasImage, image=self.photoImage)
        if drawingDone:
            self.drawingProcessDone=True
            if not self.quitFlag:
                drawerQueue.put(DrawingDoneAcknowledgement())
            self.displayStatus("Image is complete")
        self.update_idletasks()
        # Schedule to be called again later
        if not self.drawingProcessDone:
            if imageToDraw==None:
                # The current update request is unanswered; wait some more.
                self.after(pollInterval, self.updateCanvas)
            else:
                # Send a new request for update after the polling delay.
                self.after(pollInterval, self.requestUpdate)

    # Save the currently displayed image to a file
    def saveImage(self):
        if self.image==None:
            return
        # Find the next available file name
        while True:
            fileName=imageFileBaseName+"."+str(self.imageFileCounter)+imageFileExtension
            self.imageFileCounter=self.imageFileCounter+1
            try:
                outputFile=open(fileName, mode="xb")
                break
            except FileExistsError:
                pass
        self.image.save(outputFile)
        outputFile.close()
        self.displayStatus("Image saved to "+fileName)

if __name__ == '__main__':
    # Configure the multiprocessing module
    multiprocessing.set_start_method('spawn')

    # Create the shared queues
    drawerQueue=multiprocessing.Queue()
    tkQueue=multiprocessing.Queue()

    # Start the image rendering subprocess
    process=multiprocessing.Process(target=draw, args=(drawerQueue, tkQueue))
    process.start()

    root=tk.Tk()

    app=PyMPCanvas(master=root)
    app.mainloop()
