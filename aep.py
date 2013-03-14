#coding=utf-8

#AEP, Automatic E-magazine Processor, a set of modules that simulate
#human action in fetching webpages, extracting main text and removing
#unnecessary characters.
#Currenly, the modules are customized for production of 1510 Weekly.

#Copyright (C) 2013 Shu Xin

__VERSION__ = '0.01'
__AUTHOR__ = "Andy Shu Xin (andy@shux.in)"
__COPYRIGHT__ = "(C) 2013 Shu Xin. GNU GPL 3."

import sys
import codecs
import string
import urllib2
from ExtMainText import extMainText
from ExtMainText import get_text
#from bs4 import BeautifulSoup

#####  Constants  #####

DEBUG = True

MAXSUBLEN = 12        # Any line longer is assumed not subheadline
SUBTHREDSOLD = 0.3    # How relatively short a line would be regarded as sub

CLEANERBOOK = (
               (u'\u3000', ' '),          #"Ideographic" spaces
               (u'\u00A0', ' '),          #&nbsp
               (u'　', ' '),              #Full-width spaces
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
    while text[0] == ' ' or text[0] == '\n':
        text = text[1:]
    while text[-1] == ' ' or text[-1] == '\n':
        text = text[:-1]

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
    subs = []
    lines = cleanText(plainText).split('\n')

    lineNo = 2
    while lineNo < len(lines) - 2:

        # Include phase
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
        for sub in subs:
            endian = sub[-1]
            length = len(sub)
            if (endian in PUNCTUATIONS) or length > MAXSUBLEN:
                subs.remove(sub)
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
    elif _markerPos(htmlText, AUTHORMARKERS) != None:
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
    if _guessSubFromHtml(htmlText) != None:
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
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url, headers=hdr)
    req = urllib2.Request(url)
    try:
        html = urllib2.urlopen(req).read()
    except urllib2.HTTPError as err:
        return err

    # Get encoding info, and decode accordingly.
    try:
        csPos = html.index('charset=') + len('charset=')
        while not _isLegit(html[csPos]):
            csPos += 1
        L = 1
        while _isLegit(html[csPos + L]):
            L += 1
        charset = html[csPos:csPos+L]
    except ValueError:   #charset not declared
        try:
            import chardet
            charset = chardet.detect(html)['encoding']
        except ImportError:
            charset = 'utf-8'
    finally:
        charset = 'gbk' if charset == 'gb2312' else charset
        charset = 'big5-hkscs' if charset == 'big5' else charset
        charset = 'utf-8' if (charset == None) or (charset == '') else charset
        html = html.decode(charset, 'ignore')
        return html

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
