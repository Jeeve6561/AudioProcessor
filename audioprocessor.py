import io
import wave
import struct


#####################################
### Loading and Writing Functions ###
#####################################

def load_audio(filename):
    """
    Given a file of name 'filename', we load the file into a dictionary

    Args:
        filename (string): This is the name of the .wav file for the audio
    """

    assert filename[-4:] == ".wav", "Only .WAV files are supported"

    with wave.open(filename, 'r') as f:
        chan, bd, soundrate, count, _, _ = f.getparams()

        assert bd == 2, "Only 16-bit .WAV files are supported"

        left = []
        right = []

        for i in range(count):
            frame = f.readframes(1)
            if chan == 2:
                left.append(struct.unpack('<h', frame[:2])[0])
                right.append(struct.unpack('<h', frame[2:])[0])
            else:
                datum = struct.unpack('<h', frame)[0]
                left.append(datum)
                right.append(datum)

    left = [i/(2**15) for i in left]
    right = [i/(2**15) for i in right]

    return {'rate': soundrate, 'left': left, 'right': right}


def write_wav(sound, filename):
    """
    Given a dictionary representing a sound, and a filename, convert the given
    sound into WAV format and save it as a file with the given filename (which
    can then be opened by most audio players)
    """
    outfile = wave.open(filename, 'w')
    outfile.setparams((2, 2, sound['rate'], 0, 'NONE', 'not compressed'))

    out = []
    for l, r in zip(sound['left'], sound['right']):
        l = int(max(-1, min(1, l)) * (2**15-1))
        r = int(max(-1, min(1, r)) * (2**15-1))
        out.append(l)
        out.append(r)

    outfile.writeframes(b''.join(struct.pack('<h', frame) for frame in out))
    outfile.close()

# Now that we have the sound files in a Python format that we can use, we will write functions to edit them

######################
### Edit Functions ###
######################


def backwards(sound):
    """
    This takes in a sound dictionary and returns the same type but with the 
    sound streams reversed
    """
    left = sound['left'][::-1]
    right = sound['right'][::-1]

    return {'rate': sound['rate'], 'left': left, 'right': right}


def mix(sound1, sound2, p):
    """
    This takes in two sounds of the same rate and mixes them with a 
    proportion p:1-p
    """
    assert sound1['rate'] == sound2['rate'], "Sound rates must be the same"
    assert 0 <= p <= 1, "Proportion must be a real number between 0 and 1"

    samples1 = len(sound1['left'])
    samples2 = len(sound2['left'])
    if samples1 <= samples2:
        samples = samples1
    else:
        samples = samples2
    left = []
    right = []
    for i in range(samples):
        left.append(p*sound1['left'][i] + (1-p)*sound2['left'][i])
        right.append(p*sound1['right'][i] + (1-p)*sound2['right'][i])
    new_sound = {'rate': sound1['rate'], 'left': left, 'right': right}
    return new_sound


def echo(sound, num_echos, delay, scale):
    """
    This takes in a sound, adds in num_echos to it, delays the echo by delay, 
    and applies the echo to a scale of scale
    """
    sample_delay = round(delay * sound['rate'])
    left = sound['left'][:]
    right = sound['right'][:]
    num = 0
    while num < num_echos:
        left.extend([0]*sample_delay)
        right.extend([0]*sample_delay)
        left_echo = multiply_list(sound['left'], scale**(1 + num))
        right_echo = multiply_list(sound['right'], scale**(1 + num))
        for i in range(len(left)):
            if i >= sample_delay * (1 + num):
                left[i] = left[i] + left_echo[i - sample_delay*(1+num)]
                right[i] = right[i] + right_echo[i - sample_delay*(1+num)]
        num = num + 1
    new_sound = {'rate': sound['rate'], 'left': left, 'right': right}
    return new_sound


def pan(sound, left_to_right=True):
    """
    This takes in a sound and pans it from left to right by default.
    If if false is input, it will pan right to left
    """
    n = len(sound['left'])
    left = sound['left'][:]
    right = sound['right'][:]
    for i in range(n):
        if left_to_right:
            left[i] = left[i]*(1 - i/(n-1))
            right[i] = right[i]*(i/(n - 1))
        else:
            left[i] = left[i]*(i/(n-1))
            right[i] = right[i]*(1 - i/(n - 1))
    return {'rate': sound['rate'], 'left': left, 'right': right}


def remove_vocals(sound):
    """
    This takes in a sound and removes the vocals from it. The vocals are
    usually added equally to right and left so removing it is simply to
    subtract the left and right corresponding values.
    """
    new = []
    for i in range(len(sound['left'])):
        new.append(sound['left'][i] - sound['right'][i])
    new_sound = {'rate': sound['rate'], 'left': new, 'right': new[:]}
    return new_sound

########################
### Helper Functions ###
########################


def multiply_list(input_list, number):
    '''
    This helper function takes in a list of floats, and returns a new list 
    with each element multiplied by number
    '''
    output = []
    for i in input_list:
        output.append(i*number)
    return output
