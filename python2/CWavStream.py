#-------------------------------------------------------------------------------
# Name:        CWavStream.py
# Purpose:     Wav Stream helper classs
#
# Author:      tatsuhiro
#
# Created:     23/06/2015
# Copyright:   (c) tatsuhiro 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#  Wav File �́@8bit/16bit/24bit/32bit/32bit float �ɑΉ�
#-------------------------------------------------------------------------------
#  Interface �́@float �̂ݑΉ�
#-------------------------------------------------------------------------------

import numpy as np
import math
import struct
import pylab as plt


class CWavStream:

    class audio_spec:

        def __init__(self, freq, ch, reso, fmt ):
            self._nFreq = freq;
            self._nChannels = ch;
            self._Resolution = reso
            
            if fmt == 'PCM':
                self._nWavFormat = 1

            if fmt == 'IEEE_FLOAT':
                self._nWavFormat = 3
                

    def __init__(self,filename):
        self._strFilename = filename;
        self._bCanRead = False;
        self._bCanWrite = False;
        self._hFile = None
        self._audio_spec = None
        self._dwTotalFileSize = 0
        self._dwTotalSamples = 0
        self._dwCurSamplePtr = 0


    def Close(self):

        if self._bCanRead:

            self.ReadClose()

        if self._bCanWrite:

            self.WriteClose()

        if self._hFile != None:

            self._hFile.close()
            self._hFile = None


    #//---------------------------------------------------------
    #//-------  FILE WEITE
    #//---------------------------------------------------------


    def ReadOpen(self):

        self._hFile = open( self._strFilename, 'rb')

        self._bCanRead = self._hFile != None

        if( self._bCanRead ):

            self._bCanRead = self.ReadChunk();

        return self._bCanRead

    def ReadClose(self):

        self._bCanRead = False

    def ReadChunk(self):

        self._hFile.seek(0,0)         # rewind
        self._dwCurSamplePtr = 0

        if self.fileStrCmp('RIFF') != True:
            return False
        self._dwTotalFileSize = self.fileGetUint32()
        if self.fileStrCmp('WAVE') != True:
            return False

        while True:

            header = self.fileGetStr4()
            chunkSize = self.fileGetUint32()

            if header == 'fmt ':

                WAVFMT_chunkSize = 16

                if chunkSize < WAVFMT_chunkSize:
                    break

                format_tag = self.fileGetUint16()
                nChannels = self.fileGetUint16()
                nSamplePerSec = self.fileGetUint32()
                nAvgBytePerSec = self.fileGetUint32()
                nBlockArign = self.fileGetUint16()
                nBitLen = self.fileGetUint16()

                if format_tag == 1:
                    fmt = 'PCM'
                elif format_tag == 3:
                    fmt = 'IEEE_FLOAT'
                else:
                    return False

                self._audio_spec = CWavStream.audio_spec(nSamplePerSec,nChannels,nBitLen//8,fmt )

                # proceed file pointer

                if chunkSize > WAVFMT_chunkSize:

                    self._hFile.seek(chunkSize - WAVFMT_chunkSize, 1 )      # 1 means current

            elif header == 'data':

                self._dwTotalSamples = chunkSize // self._audio_spec._nChannels // self._audio_spec._Resolution
                return True

        return False


    def ReadAudio(self, samples):

        buf = []

        # make buffer
        for i in range(self._audio_spec._nChannels):
            buf.append([])

        for i in range(samples):

            for ch in range(self._audio_spec._nChannels):

                dat = self.ToSingle()

                if dat == None:
                    break

                buf[ch].append(dat)

            self._dwCurSamplePtr += 1
            if self._dwCurSamplePtr >= self._dwTotalSamples:
                break


        return buf



    #//---------------------------------------------------------
    #//-------  FILE WEITE
    #//---------------------------------------------------------

    def WriteOpen(self, freq, ch, reso, fmt = 'PCM'):

        self._audio_spec = CWavStream.audio_spec(freq,ch,reso,fmt)

        if self._audio_spec._nWavFormat == 3 and self._audio_spec._Resolution != 4:

            # Format Error
            return False

        self._hFile = open( self._strFilename, 'wb' )

        self._bCanWrite = self.WriteChunk()

        return True

    def WriteClose(self):

        self.WriteChunk()
        self._bCanWrite = False

    def WriteChunk(self):

        headersize = 0x2c

        self._hFile.seek(0,2)       # 2 ... end positon
        filesize = self._hFile.tell()
        datasize = filesize - headersize

        if filesize == 0:

            self.MakeWavHdr(0,0)

        else:

            self.MakeWavHdr(filesize-8,datasize)

        return True

    def MakeWavHdr(self, filesize, datasize):

        self._hFile.seek(0,0)       # 0 ... absolute

        self.fileSetStr4('RIFF');
        self.fileSetUint32(filesize);
        self.fileSetStr4('WAVE');
        self.fileSetStr4('fmt ');
        self.fileSetUint32(16);
        self.fileSetUint16(self._audio_spec._nWavFormat);
        self.fileSetUint16(self._audio_spec._nChannels);
        self.fileSetUint32(self._audio_spec._nFreq);
        self.fileSetUint32(self._audio_spec._nChannels * self._audio_spec._nFreq * self._audio_spec._Resolution);
        self.fileSetUint16(self._audio_spec._Resolution * self._audio_spec._nChannels);
        self.fileSetUint16(self._audio_spec._Resolution * 8);
        self.fileSetStr4('data');
        self.fileSetUint32(datasize);

    def WriteAudio(self, buf):

        
        samples = len(buf[0])
        swBufSize = samples * self._audio_spec._Resolution * self._audio_spec._nChannels

        for i in range(samples):

            for ch in range(self._audio_spec._nChannels):

                data = self.SetByteArray(buf[ch][i])
                self._hFile.write(bytearray(data))


        return samples

    #//---------------------------------------------------------
    #//-------  Byte -> Float (for read audio)
    #//---------------------------------------------------------
    def ToSingle(self):

        ret = 0

        if self._audio_spec._nWavFormat == 3:

            dat = self._hFile.read(4)
            if len(dat) < 4:
                return None
            S = struct.Struct('<f')
            return S.unpack_from(buffer(dat))[0]

        elif self._audio_spec._Resolution == 1:

            dat = self._hFile.read(1)
            if len(dat) < 1:
                return None
            S = struct.Struct('B')
            return float(int(S.unpack_from(buffer(dat))[0]) - 128) / 128.0


        elif self._audio_spec._Resolution == 2:

            dat = self._hFile.read(2)
            if len(dat) < 2:
                return None
            S = struct.Struct('<h')
            return float(S.unpack_from(buffer(dat))[0]) / 32768.0

        elif self._audio_spec._Resolution == 3:

            dat0 = self._hFile.read(1);
            if len(dat0) < 1: return None
            dat1 = self._hFile.read(1);
            if len(dat1) < 1: return None
            dat2 = self._hFile.read(1);
            if len(dat2) < 1: return None
            s0 = struct.Struct('B')
            d0 = s0.unpack_from(buffer(dat0))[0]
            s1 = struct.Struct('B')
            d1 = s1.unpack_from(buffer(dat1))[0]
            s2 = struct.Struct('b')
            d2 = s2.unpack_from(buffer(dat2))[0]

            ret = (d2<<16) + (d1<<8) + (d0)
            return float(ret) / 8388608.0;


        elif self._audio_spec._Resolution == 4:

            dat = self._hFile.read(4)
            if len(dat) < 4:
                return None
            S = struct.Struct('<i')
            return float(S.unpack_from(buffer(dat))[0]) / 2137483648.0

        return ret

    #//---------------------------------------------------------
    #//-------  Byte <- Float (for write audio)
    #//---------------------------------------------------------
    def SetByteArray(self, val):

        ret = 0

        if self._audio_spec._nWavFormat == 3:

            ret = bytearray(struct.pack('f', val) )

        elif self._audio_spec._Resolution == 1:

            ret = bytearray(struct.pack('B', int(val*128 - 128) & 0xff )  )

        elif self._audio_spec._Resolution == 2:

            ret = bytearray(struct.pack('h', val*32768) )

        elif self._audio_spec._Resolution == 3:

            ival = int(val * 8388608.0)
            byte2 = (ival >> 16) & 0xff
            byte1 = ((ival & 0x0000FF00) >> 8 ) & 0xff
            byte0 = ((ival & 0x000000FF) >> 0 ) & 0xff

            ret = bytearray([byte0,byte1,byte2])


        elif self._audio_spec._Resolution == 4:

            ret = bytearray(struct.pack('i', val*2137483648) )

        return ret



    #//---------------------------------------------------------
    #//-------  FILE UTIL
    #//---------------------------------------------------------

    def fileStrCmp(self,str):

        fstr = self._hFile.read(4).decode()

        return fstr == str

    def fileGetStr4(self):

        return self._hFile.read(4).decode()

    def fileGetUint32(self):

        dat = self._hFile.read(4)
        S = struct.Struct('<I')
        return S.unpack_from(buffer(dat))[0]

    def fileGetUint16(self):

        dat = self._hFile.read(2)
        S = struct.Struct('<H')
        return S.unpack_from(buffer(dat))[0]


    def fileSetStr4(self,str):

        self._hFile.write(str)

    def fileSetUint32(self, val):

        bary = bytearray([ val & 0xFF, (val>>8) & 0xFF, (val>>16) & 0xFF, (val>>24) & 0xFF ])
        self._hFile.write(bary)
           

    def fileSetUint16(self, val):
        self._hFile.write( struct.pack('H', val))




#---- TESTCODE -----

def main():

    PREVTEST = 'NONE'
    TESTNAME = 'BIGIN'

    # Genrate Sine wave
    SampleFreq = 44100
    SinFreq = 1000.0
    SinGain = 0.5
    Samples = SampleFreq * 1
    TestSampleUnit = 1000

    sinwave = np.zeros(Samples)
    phy = 0.0
    delta = 2.0 * math.pi * SinFreq / SampleFreq

    for i in range(Samples):

        sinwave[i] = math.sin(phy) * SinGain;
        phy += delta
        if phy >= 2.0 * math.pi:
            phy -= 2.0 * math.pi

    #########################################
    # TEST1: Write WavFile : Float
    #########################################

    TESTNAME = 'TEST1_DF_F'

    print('TEST1 testing')

    writeStream = CWavStream(TESTNAME + '.wav')

    if writeStream.WriteOpen(SampleFreq,2,4,'IEEE_FLOAT') != True:

        print('writeStream Open Error! ' + TESTNAME)
        return

    writeStream.WriteAudio([ sinwave, sinwave * 0.5 ])
    writeStream.Close()
    print('TEST1 test OK')

    #########################################
    # TEST2: Read Wav File : Float -> Int32
    #########################################

    print('TEST2 testing')
    PREVTEST = TESTNAME
    TESTNAME = 'Test2_F_Int32'

    readStream = CWavStream(PREVTEST + '.wav' )
    writeStream = CWavStream(TESTNAME + '.wav' )

    if readStream.ReadOpen() == True:

        print( TESTNAME + 'Read Open Okay' )
        print('---- Sample Freq %d' % readStream._audio_spec._nFreq )
        print('---- Channels %d' % readStream._audio_spec._nChannels )
        print('---- Resoultion %d' % readStream._audio_spec._Resolution )
        print('---- Samples %d' % readStream._dwTotalSamples )

    else:
        print( TESTNAME + 'Read Open NG' )

    readData = readStream.ReadAudio(readStream._dwTotalSamples*2)

    writeStream.WriteOpen( readStream._audio_spec._nFreq, readStream._audio_spec._nChannels, 4, 'PCM')

    writeStream.WriteAudio(readData)

    writeStream.Close()
    readStream.Close()

    print('TEST2 test OK')
    
    #########################################
    # TEST3: Read Wav File : Int32 -> Int24
    #########################################

    print('TEST3 testing')
    PREVTEST = TESTNAME
    TESTNAME = 'Test3_F_Int24'

    readStream = CWavStream(PREVTEST + '.wav' )
    writeStream = CWavStream(TESTNAME + '.wav' )

    if readStream.ReadOpen() == True:

        print( TESTNAME + 'Read Open Okay' )
        print('---- Sample Freq %d' % readStream._audio_spec._nFreq )
        print('---- Channels %d' % readStream._audio_spec._nChannels )
        print('---- Resoultion %d' % readStream._audio_spec._Resolution )
        print('---- Samples %d' % readStream._dwTotalSamples )

    else:
        print( TESTNAME + 'Read Open NG' )

    readData = readStream.ReadAudio(readStream._dwTotalSamples)

    writeStream.WriteOpen( readStream._audio_spec._nFreq, readStream._audio_spec._nChannels, 3, 'PCM')
    writeStream.WriteAudio(readData)

    writeStream.Close()
    readStream.Close()

    print('TEST3 test OK')

    #########################################
    # TEST4: Read Wav File : Int24 -> Int16
    #########################################

    print('TEST4 testing')
    PREVTEST = TESTNAME
    TESTNAME = 'Test4_F_Int16'

    readStream = CWavStream(PREVTEST + '.wav' )
    writeStream = CWavStream(TESTNAME + '.wav' )

    if readStream.ReadOpen() == True:

        print( TESTNAME + 'Read Open Okay' )
        print('---- Sample Freq %d' % readStream._audio_spec._nFreq )
        print('---- Channels %d' % readStream._audio_spec._nChannels )
        print('---- Resoultion %d' % readStream._audio_spec._Resolution )
        print('---- Samples %d' % readStream._dwTotalSamples )

    else:
        print( TESTNAME + 'Read Open NG' )

    readData = readStream.ReadAudio(readStream._dwTotalSamples)

    writeStream.WriteOpen( readStream._audio_spec._nFreq, readStream._audio_spec._nChannels, 2, 'PCM')
    writeStream.WriteAudio(readData)

    writeStream.Close()
    readStream.Close()
    print('TEST4 test OK')

    #########################################
    # TEST5: Read Wav File : Int16 -> Int8
    #########################################

    print('TEST5 testing')
    PREVTEST = TESTNAME
    TESTNAME = 'Test5_F_Int8'

    readStream = CWavStream(PREVTEST + '.wav' )
    writeStream = CWavStream(TESTNAME + '.wav' )

    if readStream.ReadOpen() == True:

        print( TESTNAME + 'Read Open Okay' )
        print('---- Sample Freq %d' % readStream._audio_spec._nFreq )
        print('---- Channels %d' % readStream._audio_spec._nChannels )
        print('---- Resoultion %d' % readStream._audio_spec._Resolution )
        print('---- Samples %d' % readStream._dwTotalSamples )

    else:
        print( TESTNAME + 'Read Open NG' )

    readData = readStream.ReadAudio(readStream._dwTotalSamples)

    writeStream.WriteOpen( readStream._audio_spec._nFreq, readStream._audio_spec._nChannels, 1, 'PCM')
    writeStream.WriteAudio(readData)

    writeStream.Close()
    readStream.Close()

    print('TEST5 test OK')

    #########################################
    # TEST6: Read Wav File : Int8 -> float
    #########################################

    print('TEST6 testing')
    PREVTEST = TESTNAME
    TESTNAME = 'Test6_F_float'

    readStream = CWavStream(PREVTEST + '.wav' )
    writeStream = CWavStream(TESTNAME + '.wav' )

    if readStream.ReadOpen() == True:

        print( TESTNAME + 'Read Open Okay' )
        print('---- Sample Freq %d' % readStream._audio_spec._nFreq )
        print('---- Channels %d' % readStream._audio_spec._nChannels )
        print('---- Resoultion %d' % readStream._audio_spec._Resolution )
        print('---- Samples %d' % readStream._dwTotalSamples )

    else:
        print( TESTNAME + 'Read Open NG' )

    readData = readStream.ReadAudio(readStream._dwTotalSamples)

    writeStream.WriteOpen( readStream._audio_spec._nFreq, readStream._audio_spec._nChannels, 4, 'IEEE_FLOAT')
    writeStream.WriteAudio(readData)

    writeStream.Close()
    readStream.Close()

    print('TEST6 test OK')

if __name__ == '__main__':
    main()
