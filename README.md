# pympcanvas

## Introduction

pympcanvas is a Python 3 boilerplate for generating an image in a
background process, displaying updates frequently in a tkinter GUI.
Intermediate images and the final image can be easily saved to file.

The image drawn by the code as written is just to illustrate how an
image can be drawn and displayed.  The code is intended for
computationally intensive image rendering algorithms.  The sections
below suggest two possible images to try.

## Sierpinski Triangle

The Sierpinski Triangle is a fractal that can be drawn with a number
of algorithms, including a simple iterative process:

1. Choose 3 points A=(x<sub>a</sub>, y<sub>a</sub>), B=(x<sub>b</sub>,
   y<sub>b</sub>), C=(x<sub>c</sub>, y<sub>c</sub>) that will be the
   corners of the triangle.

2. Choose one of the three points as the initial point P<sub>0</sub>.

3. Repeat for i=1 to ∞, drawing each point P<sub>i</sub>:

   a. Choose one of the original points A, B, or C at random.

   b. Set P<sub>i</sub> to the midpoint between the chosen point and
      P<sub>i-1</sub>.

That's it!  Don't follow the link below initially if you want to see
the image first by implementing it yourself.  But this algorithm is
the ["Chaos game" construction described on
Wikipedia](https://en.wikipedia.org/wiki/Sierpi%C5%84ski_triangle#Chaos_game).
You might be interested in trying some of the other constructions.

## Mandelbrot Set

The Mandelbrot set can also be rendered using pympcanvas.  The colour
of a point (x, y), where x and y are real numbers, is calculated as
follows:

1. Consider c=(x, y) to represent the complex number x+yi.

2. Set Z<sub>0</sub> to 0.

3. Iteratively compute Z<sub>i</sub>=Z<sub>i-1</sub><sup>2</sup>+c,
   counting the number of iterations before the point Z<sub>i</sub> is
   a distance greater than 2 from the origin.  If Z<sub>i</sub> never
   reaches this distance, it is in the Mandelbrot set.

4. Colour the point with a colour indicative of the number of
   iterations computed in step 3.

Again [Wikipedia](https://en.wikipedia.org/wiki/Mandelbrot_set) is a
possible starting point for learning more, and has some nice
visualizations.

# Known Issues

Occasionally the GUI window opens but stays blank and in this case the
close box doesn't work either.  Press Ctrl-C in the terminal window
that started the program to stop it in this case.  I haven't
identified the cause yet.
