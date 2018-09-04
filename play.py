#!/usr/bin/python
#
# given the filename of a mut file, play it
#
# bug: it fakes it for slurs, simply reducing note velocity for slurred/tied notes
#
from mingus.containers import NoteContainer, Note
from mingus.midi import fluidsynth
import mingus.core.chords as chords
import mingus.core.progressions as progressions
import time, sys, re

SF2 = '/usr/local/share/sf/piano.sf2'    
debug = 1

pitch_class_dict = { 'C':0, 'C#':1, 'Db':1, 'D':2, 'D#':3, 'Eb':3, 'E':4, 'E#':5,
    'Fb':4, 'F':5, 'F#':6, 'F##':7, 'Gb':6, 'G':7, 'G#':8, 'Abb':7, 'Ab':8, 'A':9,
    'A#':10, 'Bb':10, 'B':11, 'B#':0, 'Cb':11, 'rest':12 }
note_dict = { 0:'C', 1:'C#', 2:'D', 3:'D#', 4:'E', 5:'F', 6:'F#', 7:'G',
              8:'G#', 9:'A', 10:'A#', 11:'B' }

def log(s):
    if debug>0:
        print s

tempo = 120.0
secondsPerBeat = 60.0/tempo
channel = 1
velocity_normal = 120
velocity_slur =   60
velocity_chord =  80

#
# take a chord of the sort music21 generates, and take out complexities
# until mingus can understand it.
#
def simplify_chord(c):
    c_orig = c
    c = re.sub(r"[\/\#\-o]", "", c)	# remove slash, #, -o, etc
    c = re.sub(r"(\d)\d+", r"\1", c)	# remove 2nd, 3rd, etc numbers, e.g. V42
    log("simplify: " + c_orig + " -> " + c)
    return c

def read_notes(fn, notes):
    with open(fn) as f:
        content_lines = f.readlines()
    content=[]
    for line in content_lines:
        if not (line.startswith('#')):
            content.extend(line.split())
        elif (line.startswith('### ')):
            meta = line[4:]
            var, val = meta.split(':')
            print(var + '\t' + val)

#
# loop through content, computing start and end events
#
    currtime=0
    tie_forward = False
    for line in content: 
        tie_backward = tie_forward
        tie_forward = False

        if line[:4] in "<key:":		# get key for interpreting chords
#           print "key:", line[5:-1], "keylet:", line[5:6]
            nkey = pitch_class_dict[line[5:6]]
            key = line[5:-1]
            if key[-1] == 'm':
                key=key.lower()
#               key=key[:-1].lower()
#           print "key:", key, "nkey:", nkey

        if line[0] in "<":		# skip tags such as <sot>, <eot>, <time>, <bar>
            continue
#       print("line:", line)
        note, duration = line.split(":")

        if duration.endswith('t'):
            tie_forward = True;
            duration = duration[:-1]

        try:
            dnum, ddenom = duration.split("/")
            duration_num = float(dnum)/float(ddenom)
        except:
           duration_num = int(duration)

        if note[0] in "ABCDEFG":
            n = NoteContainer(Note(note))

            velocity = velocity_normal
            if tie_backward:
                velocity = velocity_slur

            notes.append([currtime, n, "S", velocity])
            notes.append([currtime+duration_num, n, "E"])
            currtime += duration_num
        elif note == "rest":
            currtime += duration_num
        elif note == "backup":
            currtime = currtime - duration_num
        elif note == "forward":
            currtime = currtime + duration_num

        #
        # roman numeral chords, e.g. rchord-viidim7:1
        #
        elif "rchord" in note:			# roman numeral chord such as I, IV
            x, c = note.split('-')
            simple_c = simplify_chord(c)
            log("rchord: "+ c+ "\tsimple: "+ simple_c+ "\tkey:"+ key)
            progression = progressions.to_chords([simple_c], key)
            chord = NoteContainer(progression[0])
            notes.append([currtime, chord, "S", velocity_chord])
            notes.append([currtime+duration_num, chord, "E"])
            currtime += duration_num

        #
        # numeric chord, e.g. nchord-145 = tonic (1) + third (16) + fifth (128)
        #
        elif "nchord" in note:
            x, c = note.split('-')
#           print "--chord:", c, "key:", key
            nc = int(c)
            n = 0
            while nc > 0:
                if nc & 1:
                    note = note_dict[(n+nkey)%12]
#                   print "  --note", note  
                    notes.append([currtime, [n+nkey+48], "S", velocity_chord])
                    notes.append([currtime+duration_num, [n+nkey+48], "E"])
                n += 1
                nc = nc // 2
            currtime += duration_num

        elif "chord" in note:			# chord such as Am7
            x, c = note.split('-')
            chord = NoteContainer(chords.from_shorthand(c))
            notes.append([currtime, chord, "S", velocity_chord])
            notes.append([currtime+duration_num, chord, "E"])
            currtime += duration_num
        else:
            print "Illegal music token item:",note


def play_notes(notes):
    currtime=0
    for note in sorted(notes):
#       print "Note:", note[0], note[1], note[2], "currtime:", currtime

        if currtime < note[0]:
            sleeptime = (note[0]-currtime) * secondsPerBeat
            time.sleep(sleeptime)
            currtime = note[0]
    
        if note[2] == 'E':
            fluidsynth.stop_NoteContainer(note[1], channel)
        if note[2] == 'S':
            fluidsynth.play_NoteContainer(note[1], channel, velocity=note[3])


def main():
    if not fluidsynth.init(SF2):
        print "Couldn't load soundfont", SF2
        sys.exit(1)

    notes = []
    for fn in sys.argv[1:]:
        print fn
        read_notes(fn, notes)

    play_notes(notes)

main()
