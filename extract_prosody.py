# Michelle Morales
# QP2 Work: This script is used to extract prosody features
# Input = directory of wav files, Output = arff

import sys, os, subprocess, csv, pandas, scipy.stats, codecs
import numpy as np

def RunStats(vector):
    if vector != []:
        mean = np.mean(vector)
        rms = np.sqrt(np.mean(np.square(vector)))
        maximum = np.max(vector)
        minimum = np.min(vector)
        std = np.std(vector)
        skewness = scipy.stats.skew(vector)
        kurtosis = scipy.stats.kurtosis(vector)
        percent1 = np.percentile(vector, 1)
        percent25 = np.percentile(vector, 25)
        percent50 =  np.percentile(vector, 50)
        percent90 = np.percentile(vector, 90)
        percent99 = np.percentile(vector,99)
        percentRange = percent99 - percent1
        p_1 = (len([x for x in vector if x > (minimum+percent1) ])/len(vector)) * 100
        p_50 = (len([x for x in vector if x > (minimum+percent50) ])/len(vector)) * 100
        p_90 = (len([x for x in vector if x > (minimum+percent90) ])/len(vector)) * 100
        return mean, rms, maximum, minimum, std, skewness, kurtosis, percent1, percent99, percentRange, p_1, p_50, p_90
    else:
        return [0]*13

def Prosody(wav_file):
    """ Runs OpenSmile to get prosody features, then applies stats to them. """
    command = '/home/apps/opensmile-2.0-rc1/opensmile/SMILExtract -C /home/apps/opensmile-2.0-rc1/opensmile/config/prosodyShs.conf -I'
    subprocess.Popen(['/home/apps/opensmile-2.0-rc1/opensmile/SMILExtract',
    '-C', '/home/apps/opensmile-2.0-rc1/opensmile/config/prosodyShs.conf', '-I', '%s'%wav_file,'-O','prosody_out.csv'], stdout=subprocess.PIPE).communicate()[0]
    output = open('prosody_out.csv','r').readlines()
    f0 = []
    voicing = []
    loudness = []
    for line in output[1:]:
        items = line.strip().split(';')
        f0.append(float(items[-3]))
        voicing.append(float(items[-2]))
        loudness.append(float(items[-1]))
    f0_feats = RunStats(f0)
    voicing_feats = RunStats(voicing)
    loudness_feats = RunStats(loudness)
    prosody_feats = f0_feats + voicing_feats + loudness_feats
    return prosody_feats

def SpeechRate(wav_file):
    # Use AuToBI Syllabifier in Python
    """ Calls AuToBI and outputs syllable regions and calculates speech rate of wav file."""
    regions = subprocess.Popen(['java','-cp', 'AuToBI.jar', 'edu.cuny.qc.speech.AuToBI.Syllabifier', '%s'%wav_file], stdout=subprocess.PIPE).communicate()[0]
    syll_list = regions.split('\n')
    syll_count = len(syll_list) - 2
    if syll_count != 0:
        seconds = float(syll_list[-2].split()[-2].replace(']',''))
        rate = syll_count / seconds
    else:
        rate = 0
    return rate


dir = sys.argv[1]
arff_name = sys.argv[2]
split = arff_name.lower()[:3]
# arff_name = 'train_prosodyModel.arff'
arff = open(arff_name,'w')
arff.write('@Relation ProsodyModel\n')
arff.write('@attribute name string\n')
arff.write('@attribute speechRate numeric\n')

prosody_feats = ['f0','voicing','loudness']
prosody_stats = 'mean, rms, maximum, minimum, std, skewness, kurtosis, percent1, percent99, percentRange, p1, p50, p90'.split(',')
for f in prosody_feats:
    for s in prosody_stats:
        arff.write('@attribute %s_%s numeric\n'%(f,s.strip()))

arff.write('@attribute label numeric\n')
arff.write('@data\n')

files = [f for f in sorted(os.listdir(dir)) if f.endswith('.wav')]
for f in files:
    name = f[:5]
    label = labels[name]
    rate = SpeechRate(dir+'/'+f)
    prosody = Prosody(dir+'/'+f)
    instance = "'%s_%s',%s,%s,%s\n" %(split,name,rate,','.join([str(x) for x in prosody]),label)
    arff.write(instance)
