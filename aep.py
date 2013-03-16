#coding=utf-8

#AEP, Automatic E-magazine Processor, a set of modules that simulate
#human action in fetching webpages, extracting main text and removing
#unnecessary characters.
#Currenly, the modules are customized for production of 1510 Weekly.

#Copyright (C) 2013 Shu Xin

__VERSION__ = '0.02'
__AUTHOR__ = "Andy Shu Xin (andy@shux.in)"
__COPYRIGHT__ = "(C) 2013 Shu Xin. GNU GPL 3."



## Constants
FONT = u'宋体'


import sys
import os
import codecs
import string
import urllib2
from ExtMainText import extMainText
from ExtMainText import get_text
try:
    import win32com.client as win32
    hasPyWin = True
except ImportError:
    hasPyWin = False


try:
    import chardet
    hasChardet = True
except ImportError:
    hasChardet = False



#####  Constants  #####

try:
    with open('DEBUG'): pass
    DEBUG = True
except IOError:
    DEBUG = False

MAXSUBLEN = 12        # Any line longer is assumed not subheadline
SUBTHREDSOLD = 0.4    # How relatively short a line must be to be a sub

CLEANERBOOK = (
               (u'\u3000', ' '),          #"Ideographic" spaces
               (u'\u00A0', ' '),          #&nbsp
               (u'　', ' '),              #Full-width spaces
               (u'\t', ' '),
               ('\r\n', '\n'),
               ('\n ', '\n'),
               ('\n\n', '\n'),            #duplicate paragraph breaks
               (u'\ue5f1', ''),           #Unknown weird character in CJK
               ('......',  u'……'),
               ('...',  u'……'),
               (u'。。。。。。',  u'……'),
               (u'。。。',  u'……'),
               (u'--', u'——'),
               (u'－－', u'——'),
               (u'■', ''),
              )

AUTHORMARKERS = (u'作者:', u'文:', u'作者：', u'文：')

PUNCTUATIONS = (',', '.', ':', ')', u'，', u'。', u'：', u'）')

#####  Data strcture  #####

class Article(object):

    def __init__(self, title='', author='', text='',
                 subheadLines=[], comments=[], category = '',
                 portraitPath='', url=''):
        self.title = title
        self.author = author
        self.text = text
        self.subheadLines = subheadLines
        self.comments = comments
        self.category = category
        self.portraitPath = portraitPath
        self.url = url

    def addSub(self, sub):
        if sub not in self.subheadLines:
            self.subheadLines.append(sub)

    def delSub(self, sub):
        if sub in self.subheadLines:
            self.subheadLines.remove(sub)

    def addComm(self, comm):
        if comm not in self.comments:
            self.subheadLines.append(comm)

    def delComm(self, comm):
        if comm in self.comments:
            self.subheadLines.remove(comm)

class Issue(object):

    def __init__(self, issueNum='', grandTitle='', ediRemark=''):
        self.issueNum = issueNum
        self.grandTitle = grandTitle
        self.ediRemark = ediRemark
        self.articleList = []

    def addArticle(self, article):
        self.articleList.append(article)

    def deleteArticle(self, article):
        self.articleList.remove(article)

    def __iter__(self):
        for article in self.articleList:
            yield article

#####  Clearner module  #####

def _isChinese(char):
    return 0x4e00 <= ord(char) < 0x9fa6

def cleanText(inputText, patternBook=CLEANERBOOK):
    if len(inputText) <= 2:
        return inputText

    text = inputText
    for patternPair in patternBook:
        key = patternPair[0]
        while string.find(text, key) != -1:
            text = string.replace(text, key, patternPair[1])

    ## Kill spaces and blank lines at BOF and EOF
    text = text.strip(' \n')

    ## Delete unnecessary spaces
    i = 1
    while i < len(text) - 1:
        if text[i] == ' ':
            if _isChinese(text[i-1]) or _isChinese(text[i+1]):
                text = text[:i] + text[i+1:]
                i -= 1
            elif (text[i-1] == ' ') or (text[i+1] == ' '):
                text = text[:i] + text[i+1:]
                i -= 1
        i += 1

    return text

#####  Parser Module  #####

def _markerPos(html, markers):
    for marker in markers:
        if marker in html:
            return (marker, html.find(marker))
    return None

def _guessSubFromHtml(html):
    return None
    #soup = BeautifulSoup(html)
    #H1 = [tag.string for tag in soup.findAll('h1')]
    #H2 = [tag.string for tag in soup.findAll('h2')]
    #H3 = [tag.string for tag in soup.findAll('h3')]
    #P  = [tag.string for tag in soup.findAll('p')]
    ## TODO: People use all sorts of labels for all sorts of purposes,
    ##       how to tell?

def _guessSubFromPlainText(plainText):

    def _subOK(sub):
        if sub.endswith(PUNCTUATIONS) or len(sub) > MAXSUBLEN:
            return False
        return True

    subs = []
    lines = cleanText(plainText).split('\n')

    # Include phase
    lineNo = 2
    while lineNo < len(lines) - 2:
        L = len(lines[lineNo])
        Lup1 = len(lines[lineNo-1])
        Lup2 = len(lines[lineNo-2])
        Ldown1 = len(lines[lineNo+1])
        Ldown2 = len(lines[lineNo+2])
        avgL = (Lup1 + Lup2 + Ldown1 + Ldown2) / 4
        if (L < SUBTHREDSOLD * avgL):
            subs.append(lines[lineNo])
        lineNo += 2  #Subheads should be scatterred.

    # Exclude phase
    subs = [s for s in subs if _subOK(s)]

    return subs

def _guessMeta(htmlText, plainText):

    ## Guess title
    # Extract what's between <title> and </title>
    titleStart = string.find(htmlText, '<title')
    titleEnd = string.find(htmlText, '</title>')
    leftTagEnd = string.find(htmlText, '>', titleStart)
    if leftTagEnd+1 <= titleEnd:
        title = htmlText[leftTagEnd+1:titleEnd]
    else:
        # Unusual tag structure
        title = '*****'

    ## Guess author
    if ':' in title or u'：' in title:
        try:
            pos = title.index(':')
        except ValueError:
            pos = title.index(u'：')
        if pos <= 4:
            author = title[:pos]
            title = title[pos+1:]
        else:
            author = ''
    elif _markerPos(htmlText, AUTHORMARKERS) is not None:
        marker, pos = _markerPos(htmlText, AUTHORMARKERS)
        pos += len(marker)
        L = 0
        TERMINATORS = ('\n', '\r', '<', '>',)
        while htmlText[pos+L] not in TERMINATORS:
            L += 1
        author = htmlText[pos:pos+L]
    else:
        author = ''

    ## Guess subheads
    if _guessSubFromHtml(htmlText) is not None:
        subs = _guessSubFromHtml(htmlText)
    else:
        subs = _guessSubFromPlainText(plainText)

    return (cleanText(title), cleanText(author), subs)

def parseHtml(htmlText):

    """
    Input: htmlText, a string, which is a html file
    Output: a tuple, first element being the content part of the html,
            and the second element being a dictionary mapping meta labels
            with their values
    """

    mainText = extMainText(htmlText)
    ratio = 0.5
    while (len(get_text(mainText)) <= 1) and (ratio > 0):
        mainText = extMainText(htmlText, ratio, False)
        ratio -= 0.1
    mainText = get_text(mainText)

    meta = _guessMeta(htmlText, mainText)
    meta = {
            'title':  meta[0],
            'author': meta[1],
            'sub':    meta[2],
            }

    return (mainText, meta)

#####  Grabber module  #####
def grab(url):

    """
    Input: a URL to a webpage
    Output: the webpage, or an exception instance, if error occurs
    Automatically extract charset, if specified, and convert to UTF-8.
    Will autodetect if charset is not defined. When all other
    measures fail, assume UTF-8 and carry on.
    """

    class SmartRedirectHandler(urllib2.HTTPRedirectHandler):

        def http_error_301(self, req, fp, code, msg, headers):
            result = urllib2.HTTPRedirectHandler.http_error_301(
                self, req, fp, code, msg, headers)
            result.status = code
            return result

        def http_error_302(self, req, fp, code, msg, headers):
            result = urllib2.HTTPRedirectHandler.http_error_302(
                self, req, fp, code, msg, headers)
            result.status = code
            return result

    class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):

        def http_error_default(self, req, fp, code, msg, headers):
            result = urllib2.HTTPError(
                req.get_full_url(), code, msg, headers, fp)
            result.status = code
            return result

    def _isLegit(char):
        """ Return true if char can be part of a charset name """
        if (char in string.ascii_letters or
            char in string.digits or
            char == '-'):
           return True
        else:
           return False

    def _urlClean(url):
        res = url
        if url[:4] != 'http':
            res = 'http://' + url
        return res

    url = _urlClean(url)
    url = url.encode('utf-8')   # In case it's a unicode URI
    req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    opener = urllib2.build_opener(SmartRedirectHandler(),
                                  DefaultErrorHandler())
    try:
        html = opener.open(req).read()
    except urllib2.HTTPError:
        return RuntimeError("Can't grab!")
    except urllib2.URLError:
        return RuntimeError("Bad URL!")

    # Get encoding info, and decode accordingly.
    charset = ''
    try:
        csPos = html.index('charset=') + len('charset=')
        while not _isLegit(html[csPos]):
            csPos += 1
        L = 1
        while _isLegit(html[csPos + L]):
            L += 1
        charset = html[csPos:csPos+L]
    except ValueError:   #charset not found
        if hasChardet:
            charset = chardet.detect(html)['encoding']
        else:
            charset = 'utf-8'
    finally:
        charset = 'gbk' if charset == 'gb2312' else charset
        charset = 'big5-hkscs' if charset == 'big5' else charset
        charset = 'utf-8' if (charset is None) or (charset == '') else charset
        html = html.decode(charset, 'ignore')
        return html


##### MS Word Export module #####
def createDoc(issue):

    word = win32.gencache.EnsureDispatch('Word.Application')
    #doc = word.Documents.Add()
    doc = word.Documents.Open(os.getcwd() + '\\template.doc')

    ##### Set up styles #####

    # Normal Text 
    font = doc.Styles(win32.constants.wdStyleNormal).Font
    font.Size = 11
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleNormal).ParagraphFormat
    paraF.LineSpacingRule = win32.constants.wdLineSpace1pt5
    paraF.CharacterUnitFirstLineIndent = 2

    # Heading 1
    font = doc.Styles(win32.constants.wdStyleHeading1).Font
    font.Bold = True
    font.Size = 24
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleHeading1).ParagraphFormat
    paraF.Alignment = win32.constants.wdAlignParagraphLeft
    paraF.LineSpacingRule = win32.constants.wdLineSpaceDouble
    paraF.CharacterUnitFirstLineIndent = 0

    # Heading 2
    font = doc.Styles(win32.constants.wdStyleHeading2).Font
    font.Bold = True
    font.Size = 18
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleHeading2).ParagraphFormat
    paraF.Alignment = win32.constants.wdAlignParagraphCenter
    paraF.LineSpacingRule = win32.constants.wdLineSpaceDouble
    paraF.CharacterUnitFirstLineIndent = 0

    # Subheads
    font = doc.Styles(win32.constants.wdStyleHeading3).Font
    font.Bold = True
    font.Italic = False
    font.Size = 11
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleHeading3).ParagraphFormat
    paraF.Alignment = win32.constants.wdAlignParagraphCenter
    paraF.LineSpacingRule = win32.constants.wdLineSpaceDouble
    paraF.CharacterUnitFirstLineIndent = 0

    # Foot notes
    font = doc.Styles(win32.constants.wdStyleQuote).Font
    font.Bold = True
    font.Size = 10
    font.Name = FONT


    ##### Add contents #####

    ## Add Header
    C = win32.constants.wdHeaderFooterPrimary
    fullTitle = u'一五一十周刊第' + issue.issueNum + u'期' + \
                u'：' + issue.grandTitle
    doc.Sections(1).Headers(C).Range.InsertAfter(fullTitle+'\r\n')

    ## Footer requires no additional actions.  ##

    rng = doc.Range(0, 0)

    ## Add Cover page
    rng.InsertAfter(u'【封面圖片】\r\n')
    rng.Collapse( win32.constants.wdCollapseEnd )
    rng.InsertBreak( win32.constants.wdPageBreak )

    ## Add Editor's Remark
    rng.InsertAfter(u'【编者的话】\r\n')
    rng.InsertAfter(issue.ediRemark)
    rng.Collapse( win32.constants.wdCollapseEnd )
    rng.InsertBreak( win32.constants.wdPageBreak )

    ## Add Contents Page
    rng.InsertAfter(u'目录\r\n')
    rng.Collapse( win32.constants.wdCollapseEnd )
    tocPos = rng.End
    rng.InsertBreak( win32.constants.wdPageBreak )

    ## Add articles
    rng.Collapse( win32.constants.wdCollapseEnd )
    category = ''
    for article in issue.articleList:

        # Category
        if article.category != category:
            category = article.category
            rng.InsertAfter(u'【' + category + u'】' + '\r\n')
            rng.Style = win32.constants.wdStyleHeading1
            rng.Collapse( win32.constants.wdCollapseEnd )

        # Title
        rng.InsertAfter(article.author + u'：' + article.title + '\r\n')
        rng.Style = win32.constants.wdStyleHeading2
        rng.Collapse( win32.constants.wdCollapseEnd )

        # Main text
        for line in article.text.split('\n'):
            rng.Collapse( win32.constants.wdCollapseEnd )
            rng.InsertAfter(line+'\r\n')
            if line in article.subheadLines:
                rng.Style = win32.constants.wdStyleHeading3

        rng.Collapse( win32.constants.wdCollapseEnd )
        rng.InsertBreak( win32.constants.wdPageBreak )

    ## Extra infomation -> embeded in template.doc
    #infodoc = word.Documents.Open(os.getcwd() + '\\extrainfo.doc')
    #rng2 = infodoc.Range()
    #rng2.Copy()
    #rng.Paste()
    #infodoc.Close(False)

    # Add TOC
    doc.TablesOfContents.Add(doc.Range(tocPos, tocPos), True, 1, 2)
    #doc.TablesOfContents(1).Update()

    # Unify font, just in case
    rng = doc.Range()
    rng.Font.Name = FONT

    # Finalizing
    doc.SaveAs(FileName=os.getcwd() + '\\' + fullTitle,
               FileFormat=win32.constants.wdFormatDocument)
    word.Visible = True
    #word.Application.Quit()


#####  File operation module  ####

def readfile(filename):
    f = codecs.open(filename, 'r', 'utf-8')
    text = f.read()
    f.close()
    return text

def writefile(filename, content):
    f = codecs.open(filename, 'w', 'utf-8')
    f.write(content)
    f.close()

def readArgv(n):

    '''
    n: number arguments expected to be returned
    Return: a tuple of n length consisting of arguments,
    if argument is inadequate, use None to fill in.
    '''

    res = []
    for i in range(1, len(sys.argv)):
        res.append(sys.argv[i])
    if len(res) > n:
        return res[:n]
    elif len(res) == n:
        return tuple(res)
    else:
        return tuple(res) + (None,) * (n - len(res))


