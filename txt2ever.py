'''
Send texts from text files to Evernote given a structural design.

Update time: 2016-03-24 11:44:40.
'''

from lib import tools
from lib import send2ever
from lib import textparse
import sys,os
import re
import argparse




class TextContainer(object):
    def __init__(self, name, _type, rng=None):
        '''Store line number range
        '''
        self.name=name
        self._type=_type
        self._rng=rng or []   #Line number range

    @property
    def rng(self):
        return self._rng

    def __str__(self):
        string='name: %s type: %s range: %s' %(self.name, self._type, self.rng)
        return string

    def __repr__(self):
        string='name: %s type: %s range: %s' %(self.name, self._type, self.rng)
        return string

    def add(self,value):
        if type(value) is int:
            if len(self._rng)==0:
                self._rng=[value,value+1]
                return
            if value<=self._rng[-1]:
                return
            else:
                self._rng[-1]=value
                return



    



class JobParser(object):

    #-----------------Structure levels-----------------
    structures={'filename': 0,\
                'heading1': 1,\
                'heading2': 2,\
                'heading3': 3,\
                'heading4': 4,\
                'heading5': 5,\
                'heading6': 6,\
                'tablevel0': 10,\
                'tablevel1': 11,\
                'tablevel2': 12,\
                'tablevel3': 13,\
                'tablevel4': 14,\
                'tablevel5': 15,\
                'given': -1\
                }


    def __init__(self, file_in, mapping, syntax='markdown'):
        '''Read in text file and prepare jobs to send to evernote.

        <file_in>: str, absolute path to txt file.
        <mapping>: dict, defines the notebook, note title and note content structures.
        <syntax>: string, syntax of <file_in>, either "markdown" or "zim".
        '''
        self.textparser=textparse.TextParser(syntax)

        self.file_in=file_in
        self.mapping=mapping
        self.syntax=syntax

        self.preprocess()


    @staticmethod
    def rel2abs(rng,start):
        return [rng[0]+start, rng[-1]+start]



    def preprocess(self):
        self.filename=os.path.splitext(os.path.split(self.file_in)[1])[0]

        self.text=tools.readFile(self.file_in)
        #self.text=self.text.encode('utf8')
        self.text=self.textparser.unifyNewline(self.text)
        
        self.lines=self.text.split('\n')
        self.lines=[ii+'\n' for ii in self.lines]

        self.nb_struc=self.mapping['notebook']
        self.tt_struc=self.mapping['title']
        self.cnt_struc=self.mapping['content']

        #-------Structure should follow a tree model-------
        struc=[self.structures[ii] for ii in [self.nb_struc,self.tt_struc,self.cnt_struc]]
        if struc!=sorted(struc):
            raise Exception("Structure level wrong")

        return



    def findHeadings(self, lines, struc):

        linenum=len(lines)
        level=struc[-1]
        _h_re=re.compile(self.textparser._h_re_base % level, re.X | re.M)

        hidx=[]

        for ii in xrange(linenum):
            if _h_re.match(lines[ii]):
                hidx.append(ii)

        hidx.append(linenum)
        groups=[[hidx[ii],hidx[ii+1]] for ii in xrange(len(hidx)-1)]

        result=[]
        for ii in groups:
            #--------Use heading line as container name--------
            result.append(TextContainer(lines[ii[0]],struc,ii))

        return result



    def findTabLevel(self, lines, struc):

        linenum=len(lines)
        targetlvl=int(struc[-1])

        result=[]

        isin=False     # Inside a tab block or not
        curlvl=0       # Previous tab level

        #------Find all lines with same or more tabs------
        for ii in xrange(linenum):
            lineii=lines[ii]
            text, tablvl=self.textparser.space2tab(lineii)

            #---------Include within-block empty lines---------
            if self.textparser.isEmpty(lineii):
                if isin:
                    block.add(ii)
                #-------------------End of lines-------------------
                if ii==linenum-1:
                    try:
                        result.append(block)
                    except:
                        pass
                continue

            #------------------Block finishes------------------
            if tablvl<=targetlvl and tablvl<curlvl:
                if isin:
                    result.append(block)
                isin=False

            if tablvl>=targetlvl:
                #----------------Get to a new block----------------
                if not isin:
                    block=TextContainer(lineii,struc,[ii,ii+1])
                #--------------Still in same block--------------
                elif isin:
                    block.add(ii)
                isin=True

            if isin:
                curlvl=tablvl
            else:
                curlvl=0

            #-------------------End of lines-------------------
            if ii==linenum-1:
                try:
                    result.append(block)
                except:
                    pass

        return result


    def findStruc(self,lines,struc):
        '''Find line number range(s) of a structure

        <lines>: list, text lines.
        <struc>: str, type of structure, see self.structures.

        Return <result>: list, contains TextContainer objs, each defining the line
                         number range of <struc> from <lines>, and its 1st line
                         as its name attribute.
        '''


        #--------Find text contents in a file--------
        if struc=='filename':
            linenum=len(lines)
            return [TextContainer(self.filename,struc,[0,linenum]),]

        #--------Find text contents under headings--------
        if 'heading' in struc:
            result=self.findHeadings(lines,struc)
            return result

        #--------Find text contents under a tablevel--------
        elif 'tablevel' in struc:
            result=self.findTabLevel(lines, struc)
            return result



    def createJobs(self,**kargs):
        '''Prepare jobs to submit to evernote.
        <kargs>: user given texts for notebook or note title. If not specified,
                 notebook or title are taken from text file.

        Return <jobs>: list, contains dicts each defining a job:
                       {'notebook': notebook name to send to,
                        'title':    note title,
                        'content':  note content texts}
                       If no contents found, return [].
        '''


        #------------------Get notebook(s)------------------
        if self.nb_struc=='given' and 'notebook' in kargs:
            nblist=[TextContainer(kargs['notebook'],'given',[0,len(self.lines)]),]
        else:
            nblist=self.findStruc(self.lines,self.nb_struc)
        if len(nblist)==0:
            print("<txt2Ever>: ERROR: Notebook structure not found in file")
            return []

        #-----------Get title(s) for each notebook-----------
        notes=[]
        for nbii in nblist:
            rngii=nbii.rng
            if self.tt_struc=='given' and 'title' in kargs:
                ttlist=[TextContainer(kargs['title'],'given',[0,len(self.lines)]),]
            else:
                ttlist=self.findStruc(self.lines[rngii[0]:rngii[-1]],self.tt_struc)
            if len(ttlist)==0:
                continue

            for ttjj in ttlist:
                ttrng=ttjj.rng
                #------------Relative to absolute range------------
                ttrng=self.rel2abs(ttrng, rngii[0])

                notes.append([nbii.name,ttjj.name,ttrng])

        if len(notes)==0:
            print("<txt2Ever>: ERROR: Note structure not found in file")
            return []

        #--------------Get contents for each note--------------
        jobs=[]

        for jobii in notes:
            nbii,ttii,rngii=jobii

            cntlist=self.findStruc(self.lines[rngii[0]:rngii[-1]],self.cnt_struc)
            if len(cntlist)==0:
                continue

            contentii=self.fetchContent(cntlist, rngii[0])

            jobii={'notebook':nbii, 'title':ttii, 'content':contentii}
            jobs.append(jobii)


        return jobs


    def fetchContent(self,cntlist, startidx):
        '''Get text lines from line number ranges.
        <cntlist>: list of TextContainer objs, whose rng attributes define
                   line numbers to fetch.
        <startidx>: int, offset index.
        '''
        lines=[]
        for ii in cntlist:
            rngjj=self.rel2abs(ii.rng, startidx)
            lines.extend(self.lines[rngjj[0]:rngjj[-1]])

        lines=self.textparser.leftJust(lines)
        lines=u''.join(lines)
        return lines




    



def txt2Ever(file_in,mapping,syntax='markdown',verbose=True,**kargs):
    '''Read in text from file and prepare jobs to submit to evernote.

    <file_in>: str, absolute path to file.
    <mapping>: dict, defines the notebook, note title and note content structures.
    <syntax>: string, syntax of <file_in>, either "markdown" or "zim".
    <kargs>: supported kargs:
             notebook = str, user given notebook to send to.
             title = str, user given note title.

    Return <jobs>: list, contains dicts each defining a job:
                   {'notebook': notebook name to send to,
                    'title':    note title,
                    'content':  note content texts}
                   If no contents found, return [].
    '''

    #-------------------Prepare jobs-------------------
    jobparser=JobParser(file_in, mapping, syntax)
    jobs=jobparser.createJobs(**kargs)

    if len(jobs)>0:
        #--------------------Connect evernote--------------------
        geeknote=send2ever.GeekNoteConnector()
        geeknote.connectToEvertone()

        #-----------------Send to Evernote-----------------
        for ii,jobii in enumerate(jobs):
            if verbose:
                print('\n# <txt2Ever>: Sending job # %d/%d to Evernote' %(ii+1,len(jobs)))
            notebook=jobii['notebook']
            title=jobii['title']
            content=jobii['content']

            send2ever.createNote(title,content,None,\
                notebook,geeknote,skipnotebook=False)



        


#-----------------------Main-----------------------
if __name__=='__main__':

    parser=argparse.ArgumentParser(description='''\
    Read in text file and prepare evernote submit jobs.''')

    helpstr='''
    structures to choose from:
    -n, -t, -c:      choose from 'filename',
                         'heading1',
                         'heading2',
                           ...
                         'heading6',
                         'tablevel0',
                         'tablevel1',
                           ...
                         'tablevel5'
    -n and -t can also use 'given'.
    '''

    parser.add_argument('file',type=str,help='Input text file')
    parser.add_argument('-n','--notebook',type=str,help=helpstr, required=True)
    parser.add_argument('-t','--title',type=str,help=helpstr, required=True)
    parser.add_argument('-c','--content',type=str,help=helpstr, required=True)

    syntax=parser.add_mutually_exclusive_group(required=True)
    syntax.add_argument('-m','--markdown', action='store_true',\
            default=True,help='Input text uses markdown syntax.')
    syntax.add_argument('-z','--zim', action='store_true',\
            help='Input text uses zim wiki syntax.')

    parser.add_argument('-v','--verbose',action='store_true',\
            default=True,\
            help='Show processing messages.')

    try:
        args=parser.parse_args()
    except:
        sys.exit(1)

    FILEIN=os.path.abspath(args.file)

    if args.markdown:
        SYNTAX='markdown'
    elif args.zim:
        SYNTAX='zim'

    """
    FILEIN='Mendeley_annotations.txt'
    SYNTAX='markdown'
    mapping={'notebook':'heading1', 'title':'heading1', 'content': 'tablevel1'}
    txt2Ever(FILEIN,mapping,SYNTAX)
    """
    mapping={'notebook':args.notebook, 'title':args.title, 'content': args.content}
    txt2Ever(FILEIN,mapping,SYNTAX)

    

