import re


class TextParser(object):

    _tab_re=re.compile('^(\\s+)(\\S.*)', re.X | re.L | re.M | re.DOTALL)
    _tag_re=re.compile('(?<=@)(.+?)[;,@\\n\\t\\Z]', re.L | re.X | re.M)
    _ws_only_line_re = re.compile(r"^[ \t]+$", re.M)
    _empty_line_re = re.compile(r"^([ \t]+$)?", re.M)
    _citekey_re=re.compile('\\s((@?)([a-zA-Z]+)(\\d{4}\\w?))\\b', re.LOCALE | re.UNICODE)

    tab_width=4

    def __init__(self, syntax='markdown'):

        self.syntax=syntax
        self.defSyntax()

    def defSyntax(self):
        '''Define re patterns according to syntax.'''

        #------------------REGEX patterns------------------

        if self.syntax=='markdown':

            self._img_re=re.compile('^(.*)!\\[(.+?)\\]\\((.+?)\\)', re.M | re.L)
            self._h_re_base = r'''
            (^(.+)[ \t]*\n(=+|-+)[ \t]*\n+)
            |
            (^(\#{%s})  # \1 = string of #'s
            [ \t]*
            (.+?)       # \2 = Header text
            [ \t]*
            (?<!\\)     # ensure not an escaped trailing '#'
            \#*         # optional closing #'s (not counted)
            \n+
            )
            '''
            self._all_h_re=re.compile(self._h_re_base %'1,6', re.X | re.M)

        elif self.syntax=='zim':

            self._img_re=re.compile('^(.*)\\{\\{(.+?)\\}\\}(.*)$', re.M | re.L)
            self._h_re_base = r'''
                ^(\={%s})  # \1 = string of ='s
                [ \t]*
                (.+?)       # \2 = Header text
                [ \t]*
                \1
                \n+
                '''
            self._all_h_re=re.compile(self._h_re_base %'1,6', re.X | re.M)
        else:
            raise Exception("Unknown syntax %s" %self.syntax)
            
        return


    @classmethod
    def unifyNewline(cls, text):
        return re.sub("\r\n|\r", "\n", text)

    @classmethod
    def isEmpty(cls,text):
        if len(text)==0 or cls._ws_only_line_re.match(text)\
                or text=='\n':
            return True
        else:
            return False


    @classmethod
    def tab2space(cls,text):
        '''Replace leading tabs to spaces and return space length.'''

        m=cls._tab_re.match(text)
        if m:
            spc=m.group(1)
            spclen=spc.count(' ')+cls.tab_width*spc.count('\t')
            return '%s%s' %(' '*spclen, m.group(2)), spclen
        else:
            return text, 0



    @classmethod
    def space2tab(cls,text):
        '''Replace leading spaces to tabs and return tab num.'''

        m=cls._tab_re.match(text)
        if m:
            spc=m.group(1)
            spclen=spc.count(' ')+cls.tab_width*spc.count('\t')

            ntab=int(spclen/cls.tab_width)
            nspc=int(spclen % cls.tab_width)
            
            return '%s%s%s' %('\t'*ntab, ' '*nspc, m.group(2)), \
                    spclen/float(cls.tab_width)
        else:
            return text, 0



    @classmethod
    def findCitekey(cls, text):
        cites=cls._citekey_re.findall(text)
        cites=[ii[0] for ii in cites]
        cites=list(set(cites))

        return cites



    @classmethod
    def findTags(cls,text):
        tags=cls._tag_re.findall(text)
        tags=['@'+ii for ii in tags]
        tags=list(set(tags))

        return tags


    @classmethod
    def leftJust(cls, lines):
        '''Left adjust by removing leading spaces/tabs
        <lines>: list of strings.
        '''

        spc=100
        linelist=[]
        #--------------Get min leading spaces--------------
        for lineii in lines:
            if cls.isEmpty(lineii):
                linelist.append(lineii)
                continue
            lineii2,spcii=cls.tab2space(lineii)
            linelist.append(lineii2)
            spc=min(spc,spcii)

        if spc==0:
            return lines

        #-------------Strip min leading spaces-------------
        elif spc>0:
            spc=int(spc)
            result=[]
            for lineii in linelist:
                if cls.isEmpty(lineii):
                    result.append(lineii)
                    continue
                lineii=lineii[spc:]
                result.append(cls.space2tab(lineii)[0])

            return result


    def isHeader(self,text):
        if self._all_h_re.match(text):
            return True
        else:
            return False


    def isImg(self,text):
        m=self._img_re.match(text)
        if m:
            return True
        else:
            return False



