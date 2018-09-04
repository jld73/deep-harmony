# harmonizer
A system for generating harmonizations of melodies using neural machine translation software

This system is based on the Music21 python library. It adds the ability to export music in a 
"music tokens" (.mut) format. These tokens, such as C-4:1/2, encode note class, octave, and 
durations in beats as well as other musical elements. Thus a melody can be transformed into 
a "sentence" of tokens or "words," and a neural machine translation system can be trained to 
"translate" the melody in to a bass, alto, or tenor line, thereby generating a harmonization 
in the style of the music on which it was trained.

Python3 and music21 are required. The Tensorflow nmt example is the back end we have tested.

Harry Plantinga, 2018

Also included:
  * play.py, a python script to play one or more mut files on your computer's speakers 
    (requires fluidsynth, mingus)
  * test-mut, a directory of music tokens (.mut) files for verifying that play works
    correctly (and eventually the mut import add-on for music21)
  * incipit.py, a script that will print out the incipit of a music file (e.g. 
    11556-65443-32215 for Twinkle, Twinkle Little Stars)
