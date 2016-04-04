'''
Extract tags from Mendeley annotations and re-organize by tags.

Takes the output of Menotexport.py, which is notes organized
by titles, and re-organize by the tags.

Optionally send the results to evernote

-> Tag summary (notebook) -> @Tag1 (note), @Tag2 (note), ... 




Update time: 2016-03-26 20:30:11.
'''



#---------------------Imports---------------------
import sys,os
import re
import pandas as pd
import argparse
from textwrap import TextWrapper
from lib import send2ever



getField=lambda x,f: x[f].unique().tolist()
conv=lambda x:unicode(x)


class Note(object):
    def __init__(self,text,title=None,cite=None):

        self.text=text
        self.title=title
        self.cite=cite
        self.tags=None
        self.ctime=None

    def addTags(self,tags):
        try:
            tags.remove('')
        except:
            pass
        if self.tags is None:
            self.tags=tags
        else:
            self.tags=self.tags+tags
        self.tags.sort()
        self.tags=[ii.strip() for ii in self.tags]
        #---------Surpress None if others present---------
        if '@None' in self.tags and len(self.tags)>1:
            self.tags.remove('@None')
            

    def __repr__(self):
        reprstr='''\
Annotation text:    %s
Creation time:      %s
Paper title:        %s
Citation key:       %s
Tags:               %s
''' %(self.text, self.ctime, self.title,\
      self.cite,', '.join(self.tags))
        
        reprstr=reprstr.encode('ascii','replace')

        return reprstr



def processLine(line):

    titlep=re.compile('^# (\\w+.+$)', re.LOCALE)    #group 1
    quotep1=re.compile('^\\t> (.+$)', re.LOCALE)    #group 1
    quotep2=re.compile('^\\t  (.+$)', re.LOCALE)    #group 1
    notep1=re.compile('^\\t- (.+$)', re.LOCALE)    #group 1
    notep2=re.compile('^\\t  (.+$)', re.LOCALE)    #group 1
    citep=re.compile('^\\t\\t- (@\\w+)')  #group1
    tagsp=re.compile('^\\t\\t(- Tags: | {8})(.+$)')    #group2
    ctimep=re.compile('^\\t\\t- Ctime: (.+$)') #group1

    patterns={'title': [titlep,1],\
              'quote1': [quotep1,1],\
              'quote2': [quotep2,1],\
              'note1':  [notep1,1],\
              'note2':  [notep2,1],\
              'cite':  [citep,1],\
              'tags':  [tagsp,2],\
              'ctime': [ctimep,1]\
              }

    for kk,vv in patterns.items():
        m=vv[0].match(line)
        if m:
            return kk,m.group(vv[1]).encode('utf8')

    return None,''






#------------Organize by tags and save------------
def export2Txt(annodf,abpath_out,verbose=True):
    '''Organize annotations by tags and save to txt.

    <annodf>: pandas DataFrame. Annotations.
    <abpath_out>: str, absolute path to output txt.
    '''

    if os.path.isfile(abpath_out):
        os.remove(abpath_out)

    if verbose:
        print('\n# <export2Txt>: Exporting all taged annotations to:')
        print(abpath_out)

    wrapper=TextWrapper()
    wrapper.width=70
    wrapper.initial_indent=''
    #wrapper.subsequent_indent='\t\t'+int(len('> '))*' '
    wrapper.subsequent_indent='\t\t'

    wrapper2=TextWrapper()
    wrapper2.width=60
    wrapper2.initial_indent=''
    #wrapper2.subsequent_indent='\t\t\t'+int(len('- Title: '))*' '
    wrapper2.subsequent_indent='\t\t\t'

    taggroup=annodf.groupby('tags')
    tags=getField(annodf,'tags')
    
    #---------------------Get tags---------------------
    if len(tags)==0:
        print('\n# <export2Txt>: No tags found in data.')
        return
    tags.sort()

    #---------------Put @None at the end---------------
    if '@None' in tags:
        tags.remove('@None')
        tags.append('@None')

    with open(abpath_out, mode='a') as fout:

        #----------------Loop through tags----------------
        for tagii in tags:

            if verbose:
                print('# <export2Txt>: Get tag: %s.' %tagii)

            outstr=u'''\n\n{0}\n# {1}'''.format(int(80)*'-', conv(tagii))
            outstr=outstr.encode('ascii','replace')
            fout.write(outstr)

            groupii=taggroup.get_group(tagii)
            citesii=getField(groupii,'cite')

            #--------------Loop through cite keys--------------
            for citejj in citesii:

                outstr=u'''\n\n\t{0}:'''.format(conv(citejj))
                outstr=outstr.encode('ascii','replace')
                fout.write(outstr)
                notesjj=groupii[groupii.cite==citejj]

                #-------------Loop through annotations-------------
                for kk in range(notesjj.shape[0]):
                    notekk=notesjj.iloc[kk]
                    strkk=wrapper.fill(notekk.text)
                    title=wrapper2.fill(notekk.title)
                    if notekk.type=='quote':
                        outstr=u'''
\n\t\t> {0}

\t\t\t- Title: {1}
\t\t\t- Ctime: {2}'''.format(*map(conv,[strkk, title,\
                  notekk.ctime]))
                    else:
                        outstr=u'''
\n\t\t- {0}

\t\t\t- Title: {1}
\t\t\t- Ctime: {2}'''.format(*map(conv,[strkk, title,\
                  notekk.ctime]))


                    outstr=outstr.encode('ascii','replace')
                    fout.write(outstr)

            

    return  



#------------Organize by tags and save------------
def export2Evernote(annodf,verbose=True):
    '''Organize annotations by tags and save to txt.

    <annodf>: pandas DataFrame. Annotations.
    '''

    geeknote=send2ever.GeekNoteConnector()
    geeknote.connectToEvertone()

    if verbose:
        print('\n# <export2Txt>: Exporting all taged annotations to Evernote')

    wrapper=TextWrapper()
    wrapper.width=70
    wrapper.initial_indent=''
    wrapper.subsequent_indent=int(len('> '))*' '

    wrapper2=TextWrapper()
    wrapper2.width=70
    wrapper2.initial_indent=''
    wrapper2.subsequent_indent='\t'+int(len('- Title: '))*' '

    taggroup=annodf.groupby('tags')
    tags=getField(annodf,'tags')
    
    #---------------------Get tags---------------------
    if len(tags)==0:
        print('\n# <export2Evernote>: No tags found in data.')
        return
    tags.sort()

    #---------------Put @None at the end---------------
    if '@None' in tags:
        tags.remove('@None')
        tags.append('@None')

    #----------------Loop through tags----------------
    for tagii in tags:

        if verbose:
            print('# <export2Evernote>: Get tag: %s.' %tagii)

        groupii=taggroup.get_group(tagii)
        citesii=getField(groupii,'cite')
        evercontentii=[]

        #--------------Loop through cite keys--------------
        for citejj in citesii:

            outstr=u'''\n## {0}:\n'''.format(conv(citejj))
            evercontentii.append(outstr)

            notesjj=groupii[groupii.cite==citejj]

            #-------------Loop through annotations-------------
            for kk in range(notesjj.shape[0]):
                notekk=notesjj.iloc[kk]
                #strkk=wrapper.fill(notekk.text)
                strkk=notekk.text
                title=wrapper2.fill(notekk.title)
                if notekk.type=='quote':
                    outstr=\
                    u'\n> {0}\n\n\t- Title: {1}\n\t- Ctime: {2}\n'\
                    .format(*map(conv,[strkk, title,notekk.ctime]))
                else:
                    outstr=\
                    u'\n- {0}\n\n\t- Title: {1}\n\t- Ctime: {2}\n'\
                    .format(*map(conv,[strkk, title,notekk.ctime]))

                evercontentii.append(outstr)

        #-----------------Send to Evernote-----------------
        send2ever.createNote(tagii,\
            ''.join(evercontentii),\
            tagii,'Tags summary',geeknote,skipnotebook=True)
        

    return  
        


#-------------------Read in text file and store data-------------------
def readFile(abpath_in,verbose=True):
    '''Read in text file and store data

    <abpath_in>: str, absolute path to input txt.
    '''

    if not os.path.exists(abpath_in):
        raise Exception("\n# <tagextract>: Input file not found.")

    if verbose:
        print('\n# <readFile>: Open input file:')
        print(abpath_in)
        print('\n# <readFile>: Reading lines...')
        
    annodata=[]

    with open(abpath_in, 'r') as fin:
        for line in fin:

            line=line.strip('\n')
            if len(line)==0: continue

            linetype,linestr=processLine(line)

            if linetype=='title':
                title=linestr
            elif linetype in ['quote1','note1']:
                notetype='quote' if linetype=='quote1' else 'note'
                note=[linestr,]
            elif linetype in ['quote2','note2']:
                note.append(linestr)
            elif linetype=='cite':
                noteobj=Note(u' '.join(note), cite=linestr, title=title)
                noteobj.notetype=notetype
            elif linetype=='tags':
                tags=linestr.split(',')
                noteobj.addTags(tags)
            elif linetype=='ctime':
                noteobj.ctime=linestr

                #----------------Append to annodata----------------
                for tagii in noteobj.tags:
                    annodata.append([\
                            title,noteobj.cite,noteobj.text,\
                            tagii,noteobj.ctime,noteobj.notetype])

    #---------------Convert to dataframe---------------
    annodata=pd.DataFrame(data=annodata,columns=['title','cite','text',\
            'tags','ctime','type'])
    if verbose:
        print('# <readFile>: Got all data.')

    return annodata






def main(filein,fileout,evernote,verbose):

    annodata=readFile(filein,verbose)
    export2Txt(annodata,fileout,verbose)
    if evernote:
        export2Evernote(annodata,verbose)
    print('\n# <tagextract>: All done.')

    return






#-----------------------Main-----------------------
if __name__=='__main__':

    parser=argparse.ArgumentParser(description=\
            'Organize Mendeley annotations by tags.')

    parser.add_argument('file',type=str,\
            help='Mendeley annotation text file.')
    parser.add_argument('-o','--out',type=str,\
            default='Mendeley_annotations_by_tags.txt',\
            help='Target file name to save outputs.')
    parser.add_argument('-e','--ever',action='store_true',\
            default=False,\
            help='Send result to Evernote.')
    parser.add_argument('-v','--verbose',action='store_true',\
            default=True,\
            help='Print some texts.')

    try:
        args=parser.parse_args()
    except:
        sys.exit(1)

    FILEIN=os.path.abspath(args.file)
    FILEOUT=os.path.abspath(args.out)
    EVERNOTE=args.ever

    main(FILEIN,FILEOUT,EVERNOTE,args.verbose)




            





