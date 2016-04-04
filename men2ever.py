'''
Send Mendeley annoations to Evernote.

Input should be the exported annotations from Menotexport.py
grouped by titles (NOT by tags).

For sending to evernote tag-grouped notes, use tagextract.py

Update time: 2016-03-26 20:19:05.
'''

from lib import send2ever
import sys,os
import argparse
import txt2ever



    



def main(file_in,verbose=True):
    '''Read in text from file and prepare jobs to submit to evernote.

    <file_in>: str, absolute path to file.

    '''

    #-------------------Prepare jobs-------------------
    mapping={'notebook':'heading1', 'title':'tablevel1', 'content': 'tablevel1'}
    jobparser=txt2ever.JobParser(file_in, mapping, 'markdown')
    jobs=jobparser.createJobs()

    if len(jobs)>0:
        #--------------------Connect evernote--------------------
        geeknote=send2ever.GeekNoteConnector()
        geeknote.connectToEvertone()

        #-----------------Send to Evernote-----------------
        num=len(jobs)
        nd=len(str(num))
        for ii,jobii in enumerate(jobs):
            if verbose:
                print('\n# <men2ever>: Sending job # %d/%d to Evernote' %(ii+1,len(jobs)))

            notebook=jobii['notebook']
            title=jobii['title']
            content=jobii['content']

            citekey=jobparser.textparser.findCitekey(content)
            citekey=citekey[0]
            notebook=u'%s - %s' %(citekey,notebook)

            title=u'#%s of %s'\
                    %(str(ii+1).rjust(nd,'0'), notebook)

            tags=jobparser.textparser.findTags(content)
            tags=u', '.join(tags)

            send2ever.createNote(title,content,tags,\
                notebook,geeknote,skipnotebook=False)



        


#-----------------------Main-----------------------
if __name__=='__main__':

    parser=argparse.ArgumentParser(description='''\
    Send Mendeley annotations to Evernote.''')

    parser.add_argument('file',type=str,help='Input Mendeley annotation file')
    parser.add_argument('-v','--verbose',action='store_true',\
            default=True,\
            help='Show processing messages.')

    try:
        args=parser.parse_args()
    except:
        sys.exit(1)

    FILEIN=os.path.abspath(args.file)
    main(FILEIN,args.verbose)

    

