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

In this directory:
  * music_tokens.py -- the library of helper functions for converting to/from mut format
    and for maniuplating music in other ways

  * play.py, a python script to play one or more mut files on your computer's speakers 
    (requires fluidsynth, mingus)

  * test-mut, a directory of music tokens (.mut) files for verifying that play.py and
    the mut file reader work correctly

  * incipit.py, a script that will print out the incipit of a music file (e.g. 
    11556-65443-32215 for Twinkle, Twinkle Little Stars). Used to tell whether two
    music files are of the same tune

  * music2mut.py -- read a music file and save all parts (e.g. soprano, alto,
    tenor, bass) as mut files. 

  * bach -- training data from ~400 bach chorales (from the music21 corpus)

  * hymns -- training data from 7000 (2000 unique?) hymns (midi files). Should be ready 
    to run experiments with, but not much tested. 

  * music_to_learn: put the training data here for your next experiment

  * test-hymn-melodies.sop: melodies to use for testing the harmony generation. They are 
    hopefully not prtesent in the Bach chorales so suitable for testing the Bach model,
    not necessarily other models. 
    
