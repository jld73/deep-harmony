
# python functions for converting music to music tokens (.mut) format, and for
# various other music hacking
#
#  possible future extension: handle polyphonic parts, returning multiple
#  separate homophonic lines.  Then you could feed it a flat SATB midi file 
#  or a SATB hymn with two staves and get out separate S, A, T, B .mut files
#
from music21 import *
from music21 import note, converter
from fractions import Fraction 
from math import ceil
from pprint import pprint
import numpy as np
import re
debug = 0
theKey = 'C'

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

#
# get the first element from a music21 stream of a certain class
#
def get_first(stream, cls):
    try:
        e = stream.getElementsByClass(cls)
        return e[0]
    except:
#       print("No elements in stream of class", cls)
        return None

#
#   given a stream, return its key (the better of embedded or analyzed)
#   i.e. if the stream has a "key" object, usually use that; otherwise use
#   music21's 'analyze' function to try to figure out the key. Here's the alg:
#
#   key algorithm:
#       ekey = embedded key
#       akey = key from music21's analyze('key')
#       thekey = ekey
#       if (ekey != akey and ekey.tonic != lastnote and 
#           (akey == lastnote or ekey == 'C')): 
#           thekey = akey
#
#   this seems the best bet for midi files because music21's analyze is 95% accurate, 
#   but the embedded key is only 50% accurate for midifiles when the key is C 
#   (maybe because C is default and gets in there accidentally quite often. For other
#   keys, the embedded key is 98% accurate).
#
def get_key(s):
    ekey = s.flat.getElementsByClass(key.Key)[0]
    akey = s.analyze('key')
    parts = partify(s)
    sop_notes = [x for x in parts[0].flat.getElementsByClass(note.Note)]
    lastnote = sop_notes[-1]
    theRealKey = ekey
    if ((ekey.tonic.pitchClass != akey.tonic.pitchClass or ekey.mode != akey.mode) and
        ekey.tonic.pitchClass != lastnote.pitch.pitchClass and
        (akey.tonic.pitchClass == lastnote.pitch.pitchClass or ekey.tonic.pitchClass==0)):
            theRealKey = akey
    if ekey != theRealKey:
        print("*** Embedded key was {0}, but analysis suggests it's really {1}".format(ekey, theRealKey))
    return theRealKey

#
# covert note, rest, or chord to printable string
#
def note_string(n):
    if isinstance(n, note.Note):
        s = "{0}-{1}: note {2}-{3}".format(n.offset, n.offset+n.duration.quarterLength,
            n.pitch.midi, n.pitch.name)
    elif isinstance(n, note.Rest):
        s = "{0}-{1}: rest".format(n.offset, n.offset+n.duration.quarterLength)
    elif isinstance(n, chord.Chord):
        s = "{0}-{1}: chord".format(n.offset, n.offset+n.duration.quarterLength)
        for n1 in n:
            s += " {0}-{1}".format(n1.pitch.midi, n1.pitch.name) 
    else:
        s = "{0}".format(n)
    return s


#
# get incipit (1 = do, 2 = re, 3 = mi, etc)
#
def get_incipit(s):
    key0 = get_key(s)
    tonic_class = key0.tonic.pitchClass
    log("get_incipit(): key: {0}  tonic_class: {1}".format(key0.name, tonic_class), 1)

    parts = partify(s)
    melody = parts[0]
    incipit = ""
    for n in melody.flat:
        if isinstance(n, note.Note):
            pitch_class = pitch_class_dict[n.pitch.name]          # 0...11
            inc = incipit_dict[(pitch_class - tonic_class) % 12]  # '1', '2', ..., '7'
            incipit += inc
    log("get_incipit(): returning {0}".format(incipit),1)

    return key0, incipit

#
# turn a stream into as many separate parts as needed, e.g. break up 
# four-part harmony into four separate parts
#
# note: this algorithm does badly on recorded midi files because notes aren't
# always held their full duration. This leaves a gap between the end of one note
# and the start of the next, where (e.g.) to fill in a tenor line gap the 
# algorithm will steal the bass note, etc. 
#
# algorithm:
#   make an empty list of parts
#   make a list of notes sorted by start time, then high to low pitch
#   for each note in list:
#     see if there is a part with space for that note. If not, add another part.
#     add the note to the first part with no note at that time
#       (before adding note, fill in the gap between the end of that part and the
#       start of the note, if there is one:
#           first, copy notes from the above part to fill the gap
#           if that's not possible, or doesn't entirely fill gap, add spaces
#       
num_parts = 1

def partify(s):
    global num_parts
    myKey  = get_first(s, key.Key)
    myTime = get_first(s, meter.TimeSignature)
    if myTime == None:
        myTime = meter.TimeSignature('4/4')
    myInstrument = get_first(s, instrument.Instrument)
    part0 = get_first(s, stream.Part)
    if part0 != None:
        part_name = part0._partName
    else:
        part_name = "Part"
    log("===========partify(): '{3}' ({0} {1}/{2})==========".format(myKey, myTime.numerator, 
        myTime.denominator, part_name), 1)

    #
    # make a list of sorted notes, by start time then pitch (high to low)
    #
    notes = []
    for n in s.flat:
        if isinstance(n, note.Note):
            notes.append(n)
        elif isinstance(n, chord.Chord):
            for p in n.pitches:
                n1 = note.Note(p)
                n1.offset = n.offset
                n1.duration.quarterLength = n.duration.quarterLength
                notes.append(n1)
    notes = sorted(notes, key=lambda n: (n.offset, 100-n.pitch.midi))
    log ("\n-------after sort-------\n", 2)
    for n1 in notes:
        log(note_string(n1), 3)

    #
    # place notes in parts, high to low, creating parts as needed
    #
    parts = []              # create empty list of monophonic parts for notes, high to low
    for n in notes:

        #
        # do we need to add another part for this note?
        #
        placeable = False
        log("trying to place note {0}".format(n), 2)
        for p in parts:  
            if n.offset >= p.duration.quarterLength:
                placeable = True

        if placeable == False:          # add a new part if needed
            p = stream.Part()
            if myKey != None:
                p.insert(0, myKey)
            if myTime != None:
                p.insert(0, myTime)
            if myInstrument != None:
                p.insert(0, myInstrument)
                p._partName = myInstrument
            if part_name != None:
                p._partName = "{0} {1}".format(part_name,num_parts)
            p.id = str(num_parts)
            log("Need another part: adding part {0} (name {1})".format(p.id, p._partName), 2)
            parts.append(p)
            num_parts += 1

        #
        # find highest available part in which to place note
        #
        for pn, p in enumerate(parts):  # place note in highest available part
            placed = False
            if n.offset < p.offset + p.duration.quarterLength and not placed:
#               log("skipping part {0}".format(p.id), 1)
                continue                # skip parts that extend beyond start of note

            else:                       # we've found a part to place it in 

                # is there a gap between end of part and this note? Fill it. 
                gap_beats = n.offset - p.duration.quarterLength     # really gap_quarterlengths
                if gap_beats > 0:
                    log("found gap: start {0}, duration {1} beats".format(n.offset, gap_beats), 2)
                    # first try copying a note from above
                    if (pn > 0):        # skip top part (# 0) because there is no higher part
                        els = parts[pn-1].flat.getElementsByOffset(p.duration.quarterLength)
                        nts = els.getElementsByClass(note.Note)
                        while (gap_beats > 0 and 
                            len(parts[pn-1].flat.getElementsByOffset(p.duration.quarterLength)) > 0 and
                            gap_beats >= (parts[pn-1].flat.getElementsByOffset(p.duration.quarterLength))[0].duration.quarterLength and
                            len(parts[pn-1].flat.getElementsByOffset(p.duration.quarterLength).getElementsByClass(note.Note)) > 0):
                            nts = parts[pn-1].flat.getElementsByOffset(p.duration.quarterLength)
                            n1 = nts.getElementsByClass(note.Note)[0]
                            n2 = note.Note(n1.nameWithOctave, quarterLength=n1.duration.quarterLength)
                            p.insert(n2)
                            gap_beats -= n2.duration.quarterLength
                    
                    # if necessary, add spaces
                    log("Space needed to fill: {0}".format(gap_beats), 3)
                    for t in [4, 1]:
                        while (gap_beats >= t):
                            log("  adding {0} rest".format(t),2)
                            r = note.Rest(quarterLength=t)
                            r.offset=p.duration.quarterLength
                            p.insert(r)
                            gap_beats -= t
                        if gap_beats >= t:
                            log("  adding {0} rest".format(t),2)
                            r = note.Rest(quarterLength=t)
                            r.offset=p.duration.quarterLength
                            p.insert(r)

                p.insert(n.offset, n)
                log("Placing note in part {0}".format(p.id), 2)
                placed = True
                break

    for id, p in enumerate(parts):
        log("---part {0}\n{1}".format(id + 1, p), 2)
        for n in p:
            log(note_string(n), 2)

    log("returning {0} parts".format(len(parts)), 2)
    return parts

#
# percent of duration of part that is notes, rather than rests
#
def coverage(p):
    total = p.duration.quarterLength
    if total == 0.0:
        total = 1.0
    sound = 0.0
    for n in p.getElementsByClass(note.Note):
        sound += n.duration.quarterLength
    return "{0:.0f}%".format(100 * sound / total)

#
# try to return a reasonable fraction for a float
# (as_integer_ratio returns (6004799503160661, 18014398509481984) for 1/3)
#
def as_ratio(x):
    factors = [3, 5, 7, 9, 11, 13]
    for f in factors:
        x = x * f
    x = float(x)
    num, denom = x.as_integer_ratio()
    for f in factors:
        denom = denom * f
    for f in factors:
        while num % f == 0 and denom % f == 0:
            num = num // f
            denom = denom // f
    return num, denom

#
# convert a part.Part to a mut string
#
# (expects monophonic part--one voice, no chords)
#
def to_mut(part):
    global theKey
    mut = "<sot>\n"
    for el in part.flat:
        if isinstance(el, (clef.Clef, instrument.Instrument, layout.SystemLayout, bar.Barline,
            layout.PageLayout, layout.StaffLayout, spanner.Slur, expressions.TextExpression)):
            continue
        elif isinstance(el, meter.TimeSignature):
            mut += "<time:{0}/{1}>\n".format(el.numerator, el.denominator)

        elif isinstance(el, key.Key):
            k = el.name
            k = re.sub(' minor','m',k)
            k = re.sub(' major', '', k)
            k = re.sub('-', 'b', k)
            mut += "<key:{0}>\n".format(k)
            theKey = k

        elif isinstance(el, note.Rest):
            num, denom = as_ratio(el.duration.quarterLength)
            if denom == 1:
                duration = str(num)
            else:
                duration = str(num) + "/" + str(denom)
            mut += "rest:{0}\n".format(duration)
            log("rest:{0}".format(duration),2)

        elif isinstance(el, note.Note):
            num, denom = as_ratio(el.duration.quarterLength)
            if denom == 1:
                duration = str(num)
            else:
                duration = str(num) + "/" + str(denom)
            pitch = re.sub("-", "b", el.pitch.name)
            notespec = "{0}-{1}:{2}".format(pitch, el.pitch.octave, duration)
            mut += notespec + "\n"
            log("note {0} {1} ({2}) --> {3} ".format(el.pitch.name, el.pitch.octave, el.duration.quarterLength, notespec),2)

        elif isinstance(el, chord.Chord):
#           print("Found a chord --", el)
            num, denom = as_ratio(el.duration.quarterLength)
            if denom == 1:
                duration = str(num)
            else:
                duration = str(num) + "/" + str(denom)
            m = ""
            backup = ""
            for n in el._notes:
#               print(n)
                pitch = re.sub("-", "b", n.pitch.name)
                m += backup
                m += "{0}-{1}:{2}\n".format(pitch, n.octave, duration)
                backup = "backup:{0}\n".format(duration)
#           print(" ",m)
            mut += m
        else:
            print("Unhandled object:", el)
    mut += "<eot>\n"
    return mut


def chord_number(chord, nkey):
    nch = set()
    for p in chord.pitchClasses:
        p_rel = (p - nkey) % 12
#       nch.add(2**(p_rel))
        nch.add(1<<p_rel)
        log("{0} - {1}, nch now {2}".format(p, p_rel, nch),4)
    nchord = sum(nch)
#   log("  nchord: {0}".format(nchord),3)
#   log("chord_number: chord {0} nkey:{1} nchord {2}".format(chord,nkey, nchord),3)
    return(nchord)

#
# make mut strings of the chords of this piece: one for roman numeral chords (rchords),
# and one for numeric chords (nchords). The rchords are as assigned by music21. The nchords
# are as follows: 
#  - add 1 if the tonic is in the chord
#  - add 2 if the minor second is present
#  - add 4 if a major second is present, etc.
# Thus chords will have 12 bits for 12 possible tones, with 4096 total possible.
# We'll use a dictionary (note_to_bit) to map, e.g., a major third to 16. To get
# the power of two, take the note (e.g. A, 9) and subtract the tonic (e.g. F, 5);
# raise to the power of two toget 16 for an A in the key of F, which is a maj 3rd.
#
# Note that this code only prints out chords for beats of at least a certain level
# of importance. Setting beats = 1 gets chords on each beat. Setting beats = 4
# gets chords on the first beat of every (4/4) measure. 
#
# bug: if you have a 1/2-beat pickup with chords every beat, you won't get a chord
# for that first half beat and all chords will sound 1/2 beat early. Probably this 
# means you should use beats=1 unless that bug is fixed. A fix might be to generate 
# a chord for the pick-up beat, if any, and then start generating chords normally
# for the first beat of the first full measure.
#
# also: it doesn't work correclty generating chords more frequently than on the beat.
# (In that case, the time counter in get_chords misbehaves, using that ceil function
#
def get_chords(s,beats):
    nkey = pitch_class_dict[re.sub('m','',theKey)]
    log("In get_chords. Key: {0} (numeric {1})".format(theKey, nkey),2)
    rmut = "<sot>\n<key:{0}>\n".format(theKey)
    nmut = "<sot>\n<key:{0}>\n".format(theKey)
    sc = s.chordify()
    time = 0
    for c in sc.flat:
        if isinstance(c, chord.Chord):
            duration = int(ceil(max(c.duration.quarterLength, beats)))
            log("Time {0}. Chord [{1}-{2}]: {3} (using duration {4})".format(time, c.offset, 
                c.offset + c.duration.quarterLength, c.pitchNames, duration), 3)
            if c.offset < time:
                continue
            cname = roman.romanNumeralFromChord(c, key.Key(theKey)).figure
            rmut += "rchord-{0}:{1}\n".format(cname, duration)
            cnum = chord_number(c, nkey)
            n = "nchord-{0}:{1}\n".format(cnum, duration)
            log("Adding chord {0} at time {1}".format(n, time),3)
            nmut += n
            time += duration
#           print("{0} {1} {2} ({3})".format(c, c.beatStrength, cname, cnum))
        elif isinstance(c, note.Rest):
            if c.offset < time:
                continue
            duration = c.duration.quarterLength
            rtext = "rest:{0}\n".format(duration)
            rmut += rtext
            nmut += rtext
            log(rtext, 1)
        else:
            log("Skipping object {0}".format(c),2)
    return rmut, nmut

#
# convert a note in mut format to a 28-element float vector of 0s and 1s, where
# bits 0..12 are a 1-hot rep for pitch classes C, C#, D, ... B, rest
# bits 13, 14, 15, 16 for octaves 2, 3, 4, 5
# bits 17..25 for note type (8, 4, 2, 1, 1/2, 1/4, 1/8, 1/16, 1/32 beats)
# bit 26 is for "times 3" duration, i.e. 12, 6, 3, etc [for dots]
# bit 27 is for "div 3" duration, i.e. 4/3, 2/3, etc [for triplets]
#
# currently this is not used, but it would make a much better representation of
# musical notes for machine learning for someone willing to modify the ML code --
# 28 bits total, 26 in 3 one-hot groups and two single bits, compared to 700+ for
# mut notation converted to a single one-hot representation
#
def note_to_vector(n):
    notespec, duration = n.split(':')
    notespec = re.sub("rest", "rest-4", notespec)
    try:
        nname, octave = notespec.split('-')
    except:
        print("Couldn't split notespec {0}".format(notespec))
        exit(3)
    octave = int(octave)
    if octave < 2 or octave > 5:
        print("Octave {0} out of supported range".format(octave))
        exit(2)
    try:
        pitch_class = pitch_class_dict[nname]
    except:
        print("Pitch class {0} not understood".format(nname))
        exit(1)
    
    if '/' not in duration:
        duration += "/1"
    num, denom = duration.split("/")
    num, denom = int(num), int(denom)
    times3 = 0.0
    if (num // 3) * 3 == num:
        times3 = 1.0
        num = num // 3
    div3 = 0.
    if (denom // 3) * 3 == denom:
        div3 = 1.0
        denom = denom // 3
    try:
        duration_type = duration_dict["{0}/{1}".format(num, denom)]
    except: 
        print("Unhandled duration: {0}/{1}".format(num, denom))
        duration_type = 3

    note_vec = np.zeros([note_vector_length])
    note_vec[pitch_class] = 1.0
    note_vec[octave+11] = 1.0
    note_vec[duration_type + 17] = 1.0
    note_vec[26] = times3
    note_vec[27] = div3
    return note_vec


#
# convert a 28-element note vector into a mut-format string
# (bug: does no error checking)
#
def vector_to_note(v):
    note_names = [ 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B', 'rest' ]
    duration_dict = { '8/1':0, '4/1':1, '2/1':2, '1/1':3, '1/2':4, '1/4':5, '1/8':6, '1/16':7, '1/32':8 }
    type_dict = {v: k for k, v in duration_dict.items()}

    for i in range(13):
        if v[i] == 1.0:
            note = note_names[i]
    octave = 0
    for i in range(4):
        if v[i+13] == 1.0:
            octave = str(i+2)
    num, denom = 1, 1
    num = 8 if v[17] == 1.0 else 1
    num = 4 if v[18] == 1.0 else 1
    num = 2 if v[19] == 1.0 else 1
    for i in range(6):
        if v[20+i] == 1.0:
            denom = denom * 2**i
    if v[26] == 1.0:
        num *= 3
    if v[27] == 1.0:
        denom *= 3
    if denom == 1:
        denom = ""
    else:
        denom = "/" + str(denom)

    if note == 'rest':
        note = "{0}:{2}{3}".format(note, octave, num, denom)
    else:
        note = "{0}-{1}:{2}{3}".format(note, octave, num, denom)
            
    return(note)


# 
# this function is for testing the encoding/decoding code
#
def test_note_encoding():
    note_specs = ["A-2:1", "A#-3:1", "Ab-4:1", "Abb-5:1", "A-6:1", "A-0:1", "B-4:1", "C-4:8",
                    "C-4:1", "D-4:1", "E-4:1", "F-4:1", "G-4:1", "Cb-4:1", "rest:1", "F##-4:1",
                    "C-4:6", "C-4:9", "C-4:3/2", "C-4:2/3", "C-4:3/3", "C-4:1/4", "C-4:1/7"]
    for note in note_specs:
        try:
            converted_note = vector_to_note(note_to_vector(note))
        except:
            converted_note = "illegal notespec"
        print("{0} -> {1}".format(note, converted_note))

####################################################################3
#
# music tokens subconverter (read, parse mut files)
#
# see a separate definition of mut format. Note that it really
# only defines ties, between two notes of the same pitch. If you
# tie notes with different pitches, I'm not sure how MusicXML
# software will deal with it.
#
####################################################################3

class MusicTokens(converter.subConverters.SubConverter):
    registerFormats = ('musictokens',) 
    registerInputExtensions = ('mut',)  
    f=open("log.txt", "a")

    def parseData(self, strData, number=None): 
        f.write("In parseData")
        #
        #  first pass, by line: read metadata, ignore comments 
        #
        strDataList = strData.splitlines()
        newData = ""
        s = stream.Part()
        s.insert(0, metadata.Metadata())
        s.metadata.title = "Imported piece"

        for line in strData.splitlines():
            if line == "":
                pass
            elif line[:4] == "### ":
                var, val = line[4:].split(':')
                f.write("Processing {0} => {1}".format(var,val))
                if var == "title":                  # configure this bit with table, etc?
                    s.metadata.title = val
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
                    f.write("** Unhandled metadata: {0} => {1}".format(var, val))
            elif line[0] != '#':
                newData += line + " "

        # for debug only
        f.write(pprint(vars(s.metadata)))
        f.write("Partname: {0}".format(s.partName))

    
        #
        # now split up into space-separated tokens and process them one at a time
        #
        offset = 0.0
        strDataList = newData.split()
        for token in strDataList:
            f.write("Token: ", token)
            if token[0] == "<":         # e.g. <sot>
                tok = token.replace("<","").replace(">","")
                if tok == "sot" or tok == "eot":
                    continue
                elif tok == "bar":
#                   b = bar.BarLine()
#                   s.insert(offset, b)
                    pass
                    # close off measure; start new one
                elif tok == "phrase":
                    # can we indicate end of prhase in MusicXML somehow?
                    pass
                else:
                    op, val = tok.split(':')
                    if op == "time":
                        m = meter.TimeSignature(val)
                        s.append(m)
                    elif op == "key":
                        k = key.Key(val)
                        s.append(k)
            else:
                note1, durfrac = token.split(':')
                duration = float(Fraction(durfrac))
                if note1 == "forward":
                    offset += duration
                    f.write("Forward: new offset {0}".format(offset))
                elif note1 == "backup":
                    offset -= duration
                    f.write("Backup: new offset {0}".format(offset))
                elif note1[0] in "rR":             # rest
                    r = note.Rest()
                    r.duration.quarterLength = duration
                    s.insert(offset, r)
                    offset += duration
                else:
                    note1 = note1.replace('-','')
                    note1 = note1.replace('b', '-')
                    n1 = note.Note(note1)
                    n1.duration.quarterLength = duration
                    s.insert(offset, n1)
                    f.write("Inserting note {0} at offset {1}".format(n1, offset))
                    offset += duration
        
        self.stream = s.makeMeasures()

# converter.registerSubconverter(MusicTokens)

