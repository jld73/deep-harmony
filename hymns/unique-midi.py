#!/usr/local/bin/python
import glob, re, os

#
# select one exmaple midi for each incipit-key combo (at random)
#
uniq_midi = {}
for fn in glob.glob('midi/*/*'):
    incipit, _ = fn.split("=")
    incipit = incipit.replace("midi/", "")
#   print(incipit, fn)
    uniq_midi[incipit] = fn

count = 0
for k in uniq_midi.keys():
    fn = uniq_midi[k]
    new_fn = re.sub('midi/', 'midi-unique/', fn)
    cmd = "cp {0} {1}".format(fn, new_fn) 

    print("New fn:", new_fn)
    _, dir, _ = new_fn.split("/")
    print("mkdir midi-unique/{0}".format(dir))
    os.system("mkdir -p midi-unique/{0}".format(dir))
#   os.system("mkdir -p {0}".format(new_fn))
    print(cmd)
    os.system(cmd)
    count += 1

print("Copied {0} midi files".format(count))
