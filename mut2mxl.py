#!/usr/local/bin/python3
from music21 import *
from music_tokens import *
from fractions import Fraction 
from math import ceil
from pprint import pprint
import numpy as np
import re, sys
import os.path
debug = 1

note_vector_length = 28

pitch_class_dict = { 'C':0, 'C#':1, 'D-':1, 'Db':1, 'D':2, 'D#':3, 'E-':3, 'Eb':3, 
    'E':4, 'E#':5, 'F-':4, 'Fb':4, 'F':5, 'F#':6, 'F##':7, 'G-':6, 'Gb':6, 'G':7, 
    'G#':8, 'A--':7, 'Abb':7, 'A-':8, 'Ab':8, 'A':9, 'A#':10, 'B-':10, 'Bb':10, 
    'B':11, 'B#':0, 'C-':11, 'Cb':11, 'rest':12 }
duration_dict = { '8/1':0, '4/1':1, '2/1':2, '1/1':3, '1/2':4, '1/4':5, '1/8':6, 
    '1/16':7, '1/32':8 }
incipit_dict = { 0:'1', 1:'2', 2:'2', 3:'3', 4:'3', 5:'4', 6:'5', 7:'5', 8:'6', 
    9:'6', 9:'6', 10:'7', 11:'7' }

#
# print out loggin data if the debug level is high enough
#
def log(s,level):
    if debug>=level:
        print(s)

def parseData(strData): 
    #
    #  first pass, by line: read metadata, dump comments 
    #
    strDataList = strData.splitlines()
    newData = ""
    s = stream.Part()
    s.insert(0, metadata.Metadata())
    s.metadata.title = "Imported piece"
    offset = 0.0

    for line in strData.splitlines():
        if line == "":
            pass
        elif line[:4] == "### ":
            var, val = line[4:].split(':')
            print("Processing {0} => {1}".format(var,val), 1)
            if var == "title":                  # rewrite this bit more elegantly,
                s.metadata.title = val          # configured with a table?
            elif var == "popularTitle":
                s.metadata.popularTitle = val
            elif var == "composer":
                s.metadata.composer = val
            elif var == "date":
                s.metadata.date = val
            elif var == "hymnalName":
                s.metadata.groupTitle = val
            elif var == "hymnalID":
                s.metadata.collectionDesignation = val
            elif var == "number":
                s.metadata.number = val
            elif var == "authorityNumber": 
                s.metadata.alternativeTitle = val
            elif var == "countryOfComposition":
                s.metadata.countryOfComposition = val
            elif var == "copyright":
                s.metadata.copyright = val
            elif var == "part":
                s.partName = val
            else:
                print("** Unhandled metadata: {0} => {1}".format(var, val))
        elif line[0] != '#':
            newData += line + " "

    if (debug > 2):
        pprint(vars(s.metadata))
    log("Partname: {0}".format(s.partName), 0)

    #
    # now split up into space-separated tokens and process them one at a time
    #
    # first pass: count number of pickup beats. Add a rest for the remainder of
    # the first measure, since music21's makeMeasures function doesn't do pickup beats.
    # 
    quarterlengths_per_measure = 12.0
    offset = 0.0
    pre_pickup_beats = 0.0

    strDataList = newData.split()
    log("First token pass: find pickup beats", 1)
    for token in strDataList:
        log("  Pass 1. token: {0}  current offset {1}".format(token, offset), 2)
        if token == "<bar>":
            log("  Found <bar>: {0} pickup beats".format(offset), 2)
            if offset < quarterlengths_per_measure:
                pre_pickup_beats = quarterlengths_per_measure-offset-1
                offset += pre_pickup_beats
                log("  Setting initial offset to {0}".format(offset), 2)
                break
        elif token.startswith("<time"):
            log("     found <time> {0}".format(token[6:-1]), 2)
            num, denom = token[6:-1].split('/')
            quarterlengths_per_measure = 4.0 * float(num) / float(denom);
            log("     quarterlengths_per_measure: {0}".format(quarterlengths_per_measure), 2)
        elif token[0] != '<':
            note1, durfrac = token.split(':')
            if durfrac.endswith('t'):       # handle t (tie) after duration
                durfrac = durfrac[:-1]
            duration = float(Fraction(durfrac))

            if note1 == "backup":
                offset -= duration
            else:
                offset += duration
            log("     New offset: {0}".format(offset), 2)
        elif offset >= quarterlengths_per_measure:
            break

    #
    # second pass: import music into music21
    #
    tie_forward = False
    tie_back = False
    offset = pre_pickup_beats
    part_number = 0

    strDataList = newData.split()
    log("Second token pass: read in music", 1)
    for token in strDataList:
        log("  Pass 2. Token: {0}  current offset: {1} ".format(token, offset), 2)
        if token[0] == "<":         # e.g. <sot>
            tok = token.replace("<","").replace(">","")
            if tok == "sot":
                offset = pre_pickup_beats           # go back to beginning
                part_number += 1
            elif tok == "eot":
                pass
            elif tok == "bar":
                pass                    
            elif tok == "phrase":
                # can we indicate end of phrase in MusicXML somehow?
                pass
            else:
                op, val = tok.split(':')
                if op == "time":
                    if part_number == 1:                # no second time sig for alto, etc
                        m = meter.TimeSignature(val)
                        s.append(m)
                elif op == "key":
                    if part_number == 1:
                        k = key.Key(val)
                        s.append(k)
        else:           # it's a note, forward backward, rest, or chord
            note1, durfrac = token.split(':')

            if durfrac.endswith('t'):       # handle t (tie) after duration
                tie_forward = True;
                durfrac = durfrac[:-1]
            duration = float(Fraction(durfrac))

            if note1 == "forward":
                offset += duration
                log("Forward: new offset {0}".format(offset),2)
            elif note1 == "backup":
                offset -= duration
                log("Backup: new offset {0}".format(offset),2)
            elif note1[0] in "rR":             # rest
                r = note.Rest()
                r.duration.quarterLength = duration
                s.insert(offset, r)
                offset += duration
            elif note1.startswith("chord"):
                _, chord1 = note1.split('-')
                h = harmony.ChordSymbol(chord1, quarterLength=duration)
                n = note.Rest(quarterLength = duration)
                s.insert(offset, h)
                s.insert(offset, n)
                log("Chord: {0} start {1} duration {2}".format(chord1, offset, duration),2)
                offset += duration

            else:                           # a note
                note1 = note1.replace('-','')
                note1 = note1.replace('b', '-')
                n1 = note.Note(note1)
                n1.duration.quarterLength = duration

                if not tie_forward and tie_back:        # handle ties
                    n1.tie=tie.Tie('stop')
                elif tie_forward and not tie_back:
                    n1.tie=tie.Tie('start')
                elif tie_forward and tie_back:
                    n1.tie = tie.Tie('continue')
                tie_back = tie_forward
                tie_forward = False

                s.insert(offset, n1)
                offset += duration
    
    s.makeMeasures(inPlace=True)
    return s



print("\n\nmusic2mut.py (debug level {0})".format(debug))
print("Input file: {0}".format(sys.argv[1]))
fn = sys.argv[1]
with open(fn, 'r') as f:
  data = f.read()
ofn = fn.replace(".mut", ".musicxml")
if os.path.isfile(ofn):
    print("Output file {0} already exists--exiting".format(ofn))
    exit(0)

s = parseData(data)

if (debug>1):
    print("Parsed music file:")
    s.show('text')         # uncomment to print parsed music file

s.makeMeasures(inPlace=True)
log("Writing output file {0}".format(ofn),1)
s.write('mxl', ofn)

