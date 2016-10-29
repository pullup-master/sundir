# Optimized Time Stretched Pulse Generator

import sys
# import path
sys.path.append('..')


import CWavStream
import numpy as np
import matplotlib.pyplot as plt
import math
import cmath
import ExpImpulse


# global setting
bShowGraph = True
bSaveWav = False
OUTFILENAME = 'out'
gFs = 48000.0

def genSin(n):

    wav = np.zeros(n)
    phy = 0.0
    delta = 0.1
    for i in range(n):
        wav[i] = math.sin(phy)
        phy += delta
        if phy > math.pi : phy -= 2 * math.pi

    return wav

def genOTSP(N,m,inv=0,lv=0.5):
    wav = np.zeros((N//2)+1, dtype=complex)

    m4pi_N2 = 4.0 * m * math.pi / N / N;

    for n in range(0, (N//2)+1):

        sign = 1.0 if inv == 0 else -1.0
        
        img = sign * m4pi_N2 * n * n;
        h = complex(0.0, img)
        h = cmath.exp(h)
        wav[n] = h

    ret = np.fft.irfft(wav)

    L = int((N//2) - m)
    ret2 = np.zeros(len(ret))
    if inv == 0:
        for i in range(N-L):    ret2[i] = ret[i+L]
        for i in range(N-L,N):  ret2[i] = ret[i-(N-L)]
    else:
        for i in range(N-L):    ret2[i+L]     = ret[i]
        for i in range(N-L,N):  ret2[i-(N-L)] = ret[i]


    # nomalize and gain
    maxlv = 0.0
    for i in range(N): maxlv = ret2[i] if ret2[i] > maxlv else maxlv
    gain = 1.0 / maxlv * lv
    for i in range(N): ret2[i] *= gain

    return ret2

def main():
    print('Optimized Time Streached Pulse Generate test')

    FFT_POINTS = 64 * 1024
    TSP_M_VAL = 1500 * FFT_POINTS / 4096

    wave = genOTSP(FFT_POINTS,TSP_M_VAL, -1)

    if bShowGraph:
        plt.grid()
        plt.plot(wave)
        plt.show()

    if bSaveWav:
        writeStream = CWavStream.CWavStream(OUTFILENAME + '.wav' )
        writeStream.WriteOpen( 48000, 1, 4, 'IEEE_FLOAT')
        writeStream.WriteAudio([wave])
        writeStream.Close()

def main2():

    FFT_POINTS = 64 * 1024
    TSP_M_VAL = 1500 * FFT_POINTS / 4096

    wav = genOTSP(FFT_POINTS,TSP_M_VAL)
    inv = genOTSP(FFT_POINTS,TSP_M_VAL, -1)

    inval = np.zeros(len(wav))
    L = 20
    for i in range(len(wav) - L): inval[i+L] = wav[i]

    fftwav = np.fft.fft(inval)
    fftinv = np.fft.fft(inv)

    conv = fftwav * fftinv

    convwav = np.fft.ifft(conv)

    if bShowGraph:
        plt.grid()
        plt.plot(convwav)
        plt.show()
 



def main3():

    start = 15000.0
    stop = 20000.0
    wave = ExpImpulse.Gen(1024, start / gFs, stop / gFs)

    if bShowGraph:
        plt.grid()
        plt.plot(wave)
        plt.show()


if __name__ == '__main__':
    main2()
