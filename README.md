# Shakashaka Solver

A solver for the [Shakashaka](https://en.wikipedia.org/wiki/Shakashaka) puzzle.

## Description

Solves shakashaka puzzle of size up to 15x15. Can do 10x10 instantly, 15x15 takes minutes, anything larger takes hours.

Main method of deduction involves finding the "rectangle closure" of a given cell (the smallest axis-aligned or diagonal rectangle that contains the cell) and seeing if this closusre could be satisfied by the current board state. This, along with some basic logic around numbered cells, makes up the majority of the algorithm. The only remaining piece is the handling of unfinished edges of partial diagonal rectangles, which essentially boils down to "if the triangles are headed into a wall, they have to turn. If the triangles can't turn, they have to continue in the same direction. If they can do neither, backtrack."

## Usage

Boards are loaded from a text file, from an image, or by scraping a board from the shakashaka puzzle website. The image processing is not very smart and expects all images to have cells of the same pixel dimensions (25x25 pixels per cell, 1 pixel grid lines), which is what you get if you screenshot the website without zooming in or out.

## Improvements

Realistically, this type of problem is much better suited by a SAT solver or similar. However, I wanted to make something without invoking that more heavy machinery. There are several aspects of it that are clearly suboptimal - the multithreading is not done particularly intelligently, the triangle_logic algorithms are slow, and there is some redundant checking done in places. I have left it in this state because even fixing all of these things wouold still not materially change the size of the boards the solver can do. I doubt this appraoch would be able to do 20x20 boards without some significant overhauling. I'm happy with its performance for the time being, given how simple it is.
