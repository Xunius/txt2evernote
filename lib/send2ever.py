'''
Utility classes and tool functions to send texts to Evernote.

Update time: 2016-03-24 11:09:28.
'''


#--------------------Constants--------------------
MAX_NOTEBOOK_TITLE_LEN=100
MAX_NOTE_TAGS=100
MAX_NOTE_TITLE_LEN=255


#---------------------Imports---------------------
import subprocess
import mimetypes
import sys,os

from geeknote import config
from geeknote import out,tools
from geeknote.editor import Editor

import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient

import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types

from geeknote.gclient import GUserStore as UserStore
from geeknote.oauth import GeekNoteAuth
from geeknote.storage import Storage
from geeknote.log import logging

import textparse
import re




#-------------------Trunc string-------------------
def truncStr(string,length):
    if len(string)>=length:
        string=string[:length-3]+'...'
    return string
        


#-----------------Create notebooks-----------------
def createNoteBook(title,geeknote=None,verbose=True):

    #-------------------Trunc title-------------------
    title=title.strip()
    title=truncStr(title,MAX_NOTEBOOK_TITLE_LEN)

    #-------Make sure title doesnt start with #-------
    tp=textparse.TextParser('markdown')
    _h_re=re.compile(tp._h_re_base %'1,', re.X | re.M)
    m=_h_re.match(title)
    if m:
        title=m.group(6)

    #---------------------Connect---------------------
    if geeknote is None:
        geeknote=GeekNoteConnector()
        geeknote.connectToEvertone()

    #-----------------Check if exists-----------------
    notebooks=geeknote.getEvernote().findNotebooks()
    out.preloader.stop()
    if not isinstance(title,unicode):
        title=unicode(title,'utf8')
    notebooks=[unicode(ii.name,'utf8') for ii in notebooks]

    if title in notebooks:
        out.successMessage('Notebook already exists.')
        return 0
    else:
        out.preloader.setMessage("Creating notebook...")
        result = geeknote.getEvernote().createNotebook(name=title)
        if result:
            out.successMessage("Notebook has been successfully created.")
            return 0
        else:
            out.failureMessage("Error while the process "
                               "of creating the notebook.")
            return tools.exitErr()



def createNote(title,content,tags,notebook,geeknote=None,\
        skipnotebook=False):

    #-------------------Trunc texts-------------------
    notebook=notebook.strip()
    notebook=truncStr(notebook,MAX_NOTEBOOK_TITLE_LEN)
    title=title.strip()
    title=truncStr(title,MAX_NOTE_TITLE_LEN)

    #-------Make sure title doesnt start with #-------
    tp=textparse.TextParser('markdown')
    _h_re=re.compile(tp._h_re_base %'1,', re.X | re.M)
    m=_h_re.match(title)
    if m:
        title=m.group(6)
    m=_h_re.match(notebook)
    if m:
        notebook=m.group(6)

    if tags is not None and len(tags.split(','))>=MAX_NOTE_TAGS:
        tags=u','.join(tags.split(',')[:MAX_NOTE_TAGS])
    
    #---------------------Connect---------------------
    if geeknote is None:
        geeknote=GeekNoteConnector()
        geeknote.connectToEvertone()

    #-----------------Create notebook-----------------
    if not skipnotebook:
        result=createNoteBook(notebook,geeknote)

    if skipnotebook or result==0:

        #----------------------Write----------------------
        inputdata=geeknote._parseInput(title,content,tags,notebook,None)
        out.preloader.setMessage('Creating note...')
        result=bool(geeknote.getEvernote().createNote(**inputdata))
        if result:
            out.successMessage("Note has been successfully saved.")
        else:
            out.failureMessage("Error while saving the note.")



class GeekNote(object):

    userStoreUri = config.USER_STORE_URI
    consumerKey = config.CONSUMER_KEY
    consumerSecret = config.CONSUMER_SECRET
    noteSortOrder = config.NOTE_SORT_ORDER
    authToken = None
    userStore = None
    noteStore = None
    storage = None
    skipInitConnection = False

    def __init__(self, skipInitConnection=False):
        if skipInitConnection:
            self.skipInitConnection = True

        self.getStorage()

        if self.skipInitConnection is True:
            return

        self.getUserStore()

        if not self.checkAuth():
            self.auth()

    def EdamException(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception, e:
                logging.error("Error: %s : %s", func.__name__, str(e))

                if not hasattr(e, 'errorCode'):
                    out.failureMessage("Sorry, operation has failed!!!.")
                    tools.exitErr()

                errorCode = int(e.errorCode)

                # auth-token error, re-auth
                if errorCode == 9:
                    storage = Storage()
                    storage.removeUser()
                    GeekNote()
                    return func(*args, **kwargs)

                elif errorCode == 3:
                    out.failureMessage("Sorry, you do not have permissions "
                                       "to do this operation.")

                # Rate limited
                # Patched because otherwise if you get rate limited you still keep
                # hammering the server on scripts
                elif errorCode == 19:
                    print("\nRate Limit Hit: Please wait %s seconds before continuing" %
                          str(e.rateLimitDuration))
                    tools.exitErr()

                else:
                    return False

                tools.exitErr()

        return wrapper

    def getStorage(self):
        if GeekNote.storage:
            return GeekNote.storage

        GeekNote.storage = Storage()
        return GeekNote.storage

    def getUserStore(self):
        if GeekNote.userStore:
            return GeekNote.userStore

        userStoreHttpClient = THttpClient.THttpClient(self.userStoreUri)
        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
        GeekNote.userStore = UserStore.Client(userStoreProtocol)

        self.checkVersion()

        return GeekNote.userStore

    def getNoteStore(self):
        if GeekNote.noteStore:
            return GeekNote.noteStore

        noteStoreUrl = self.getUserStore().getNoteStoreUrl(self.authToken)
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        GeekNote.noteStore = NoteStore.Client(noteStoreProtocol)

        return GeekNote.noteStore

    def checkVersion(self):
        versionOK = self.getUserStore().checkVersion("Python EDAMTest",
                                       UserStoreConstants.EDAM_VERSION_MAJOR,
                                       UserStoreConstants.EDAM_VERSION_MINOR)
        if not versionOK:
            logging.error("Old EDAM version")
            return tools.exitErr()

    def checkAuth(self):
        self.authToken = self.getStorage().getUserToken()
        logging.debug("oAuth token : %s", self.authToken)
        if self.authToken:
            return True
        return False

    def auth(self):
        GNA = GeekNoteAuth()
        self.authToken = GNA.getToken()
        userInfo = self.getUserInfo()
        if not isinstance(userInfo, object):
            logging.error("User info not get")
            return False

        self.getStorage().createUser(self.authToken, userInfo)
        return True

    def getUserInfo(self):
        return self.getUserStore().getUser(self.authToken)

    def removeUser(self):
        return self.getStorage().removeUser()

    @EdamException
    def findNotes(self, keywords, count, createOrder=False, offset=0):
        """ WORK WITH NOTES """
        noteFilter = NoteStore.NoteFilter(order=Types.NoteSortOrder.RELEVANCE)
        noteFilter.order = getattr(Types.NoteSortOrder, self.noteSortOrder)
        if createOrder:
            noteFilter.order = Types.NoteSortOrder.CREATED

        if keywords:
            noteFilter.words = keywords
        return self.getNoteStore().findNotes(self.authToken, noteFilter, offset, count)

    @EdamException
    def loadNoteContent(self, note):
        """ modify Note object """
        if not isinstance(note, object):
            raise Exception("Note content must be an "
                            "instance of Note, '%s' given." % type(note))

        note.content = self.getNoteStore().getNoteContent(self.authToken, note.guid)
        # fill the tags in
        if note.tagGuids and not note.tagNames:
          note.tagNames = [];
          for guid in note.tagGuids:
            tag = self.getNoteStore().getTag(self.authToken,guid)
            note.tagNames.append(tag.name)

    @EdamException
    def createNote(self, title, content, tags=None, notebook=None, created=None, resources=None):
        
        def make_resource(filename):
            try:
                mtype = mimetypes.guess_type(filename)[0]
                    
                if mtype.split('/')[0] == "text":
                    rmode = "r"
                else:
                    rmode = "rb"

                with open(filename, rmode) as f:
                    """ file exists """
                    resource = Types.Resource()
                    resource.data = Types.Data()

                    data = f.read()
                    md5 = hashlib.md5()
                    md5.update(data)
                    
                    resource.data.bodyHash = md5.hexdigest() 
                    resource.data.body = data
                    resource.data.size = len(data) 
                    resource.mime = mtype
                    resource.attributes = Types.ResourceAttributes()
                    resource.attributes.fileName = os.path.basename(filename)
                    return resource
            except IOError:
                msg = "The file '%s' does not exist." % filename
                out.failureMessage(msg)
                raise IOError(msg)

        note = Types.Note()
        note.title = title
        note.content = content
        note.created = created

        if tags:
            note.tagNames = tags

        if notebook:
            note.notebookGuid = notebook

        if resources:
            """ make EverNote API resources """
            note.resources = map(make_resource, resources)
            
            """ add to content """
            resource_nodes = ""
            
            for resource in note.resources:
                resource_nodes += '<en-media type="%s" hash="%s" />' % (resource.mime, resource.data.bodyHash)

            note.content = note.content.replace("</en-note>", resource_nodes + "</en-note>")

        logging.debug("New note : %s", note)

        return self.getNoteStore().createNote(self.authToken, note)

    @EdamException
    def updateNote(self, guid, title=None, content=None,
                   tags=None, notebook=None, resources=None):
        note = Types.Note()
        note.guid = guid
        if title:
            note.title = title

        if content:
            note.content = content

        if tags:
            note.tagNames = tags

        if notebook:
            note.notebookGuid = notebook

        if resources:
            """ TODO """
            print("Updating a note's resources is not yet supported.")
            raise NotImplementedError()

        logging.debug("Update note : %s", note)

        self.getNoteStore().updateNote(self.authToken, note)
        return True

    @EdamException
    def removeNote(self, guid):
        logging.debug("Delete note with guid: %s", guid)

        self.getNoteStore().deleteNote(self.authToken, guid)
        return True

    @EdamException
    def findNotebooks(self):
        """ WORK WITH NOTEBOOKS """
        return self.getNoteStore().listNotebooks(self.authToken)

    @EdamException
    def createNotebook(self, name):
        notebook = Types.Notebook()
        notebook.name = name

        logging.debug("New notebook : %s", notebook)

        result = self.getNoteStore().createNotebook(self.authToken, notebook)
        return result

    @EdamException
    def updateNotebook(self, guid, name):
        notebook = Types.Notebook()
        notebook.name = name
        notebook.guid = guid

        logging.debug("Update notebook : %s", notebook)

        self.getNoteStore().updateNotebook(self.authToken, notebook)
        return True

    @EdamException
    def removeNotebook(self, guid):
        logging.debug("Delete notebook : %s", guid)

        self.getNoteStore().expungeNotebook(self.authToken, guid)
        return True

    @EdamException
    def findTags(self):
        """ WORK WITH TAGS """
        return self.getNoteStore().listTags(self.authToken)

    @EdamException
    def createTag(self, name):
        tag = Types.Tag()
        tag.name = name

        logging.debug("New tag : %s", tag)

        result = self.getNoteStore().createTag(self.authToken, tag)
        return result

    @EdamException
    def updateTag(self, guid, name):
        tag = Types.Tag()
        tag.name = name
        tag.guid = guid

        logging.debug("Update tag : %s", tag)

        self.getNoteStore().updateTag(self.authToken, tag)
        return True

    @EdamException
    def removeTag(self, guid):
        logging.debug("Delete tag : %s", guid)

        self.getNoteStore().expungeTag(self.authToken, guid)
        return True



class GeekNoteConnector(object):
    evernote = None
    storage = None

    def connectToEvertone(self):
        out.preloader.setMessage("Connect to Evernote...")
        self.evernote = GeekNote()
        out.preloader.stop()

    def getEvernote(self):
        if self.evernote:
            return self.evernote

        self.connectToEvertone()
        return self.evernote

    def getStorage(self):
        if self.storage:
            return self.storage

        self.storage = self.getEvernote().getStorage()
        return self.storage

    def getNoteGUID(self, notebook):
        if len(notebook) == 36 and notebook.find("-") == 4:
            return notebook

        result = self.getEvernote().findNotebooks()
        notebook = [item for item in result if item.name == notebook]
        if notebook:
            return notebook[0].guid
        else:
            return None

    def _parseInput(self, title=None, content=None, tags=None, notebook=None, resources=None, note=None):
        result = {
            "title": title,
            "content": content,
            "tags": tags,
            "notebook": notebook,
            "resources": resources,
        }
        result = tools.strip(result)

        # if get note without params
        if note and title is None and content is None and tags is None and notebook is None:
            content = config.EDITOR_OPEN

        if title is None and note:
            result['title'] = note.title

        if content:
            content = Editor.textToENML(content,format='other')
            result['content'] = content
            '''
            if content != config.EDITOR_OPEN:
                if isinstance(content, str) and os.path.isfile(content):
                    logging.debug("Load content from the file")
                    content = open(content, "r").read()

                logging.debug("Convert content")
            '''

        if tags:
            result['tags'] = tools.strip(tags.split(','))

        if notebook:
            #notepadGuid = Notebooks().getNoteGUID(notebook)
            notepadGuid = self.getNoteGUID(notebook)
            if notepadGuid is None:
                #newNotepad = Notebooks().create(notebook)
                newNotepad = self.create(notebook)
                notepadGuid = newNotepad.guid

            result['notebook'] = notepadGuid
            logging.debug("Search notebook")

        return result









