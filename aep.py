#coding=utf-8

#AEP, Automatic E-magazine Processor, a set of modules that simulate
#human action in fetching webpages, extracting main text and removing
#unnecessary characters.
#Currenly, the modules are customized for production of 1510 Weekly.

#Copyright (C) 2013 Shu Xin

__VERSION__ = 'Build 0001'
__AUTHOR__ = "Andy Shu Xin (andy@shux.in)"
__COPYRIGHT__ = "(C) 2013 Shu Xin. GNU GPL 3."

import sys
import codecs
import string
import urllib2
from ExtMainText import extMainText
from ExtMainText import get_text
from bs4 import BeautifulSoup

#####  Constants  #####

DEBUG = True

MAXSUBLEN = 12                     #Any line longer is assumed not subheadline
SUBTHREDSOLD = 0.3

CLEANERBOOK = (
        (u'\u3000', ' '),          #"Ideographic" spaces
        (u'\u00A0', ' '),          #&nbsp
        (u'　', ' '),              #Full-width spaces
        ('\r\n', '\n'),
        ('\n ', '\n'),
        #('\r\n ', '\r\n'),
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

CLEANER_EXCEPTION_BOOK = {}

#####  Data strcture  #####

class Article(object):

    def __init__(self, title='', author='', text='',
                 subheadLines=[], category = '', portraitPath=''):
        self.title = title
        self.author = author
        self.text = text
        self.subheadLines = subheadLines
        self.portraitPath = portraitPath

    def __str__(self):
        return '====Article====\n' + \
               'Title is '+self.title+'\n'+ \
               'Author is '+self.author+'\n'+ \
               '***Main text starts ***\n' + self.text + '***Main text ends ***\n' + \
               'Subhead line numbers: ' + str(self.subheadLines)

class Issue(object):

    def __init__(self, issueNum='', grandTitle='', ediRemark=''):
        self.issueNum = issueNum
        self.grandTitle = grandTitle
        self.ediRemark = ediRemark
        self.articleList = []
        self.categoryList = []

    def addArticle(self, article):
        self.articleList.append(article)

    def deleteArticle(self, article):
        self.articleList.remove(article)

    def __str__(self):
        res = 'Issue no.'+unicode(self.issueNum)+' '+self.grandTitle+'\n'+\
               'total article number:'+unicode(len(self.articleList))+'\n'+\
               'Editor says:'+self.ediRemark+'\n'
        for article in self.articleList:
            res += unicode(article) + '\n'
        return res

    #def addCategory(self, word, articlesContained):
        #newCategory = Category(word, articlesContained)
        #self.categoryList.append(newCategory)

##########  Clearner module  ##########

def _isChinese(char):
    return 0x4e00 <= ord(char) < 0x9fa6

def cleanText(input, patternBook=None):
    if patternBook == None:
        patternBook = CLEANERBOOK

    text = input
    for patternPair in patternBook:
        key = patternPair[0]
        while string.find(text, key) != -1:
            text = string.replace(text, key, patternPair[1])

    ## Kill spaces and blank lines at BOF
    while text[0] == ' ' or text[0] == '\n':
        text = text[1:]
    while text[0:2] == '\r\n':
        text = text[2:]

    ## Dealing with spaces
    i = 1
    while i < len(text) - 1:
        if text[i] == ' ':

            # Delete spaces around Chinese characters
            if _isChinese(text[i-1]) or _isChinese(text[i+1]):
                text = text[:i] + text[i+1:]

            # Combine multiple consecutive spaces
            elif (text[i-1] == ' ') or (text[i+1] == ' '):
                text = text[:i] + text[i+1:]

        i += 1

    return text

#####  Parser Module  #####

def _guessTitle(htmlText):
    titleStart = string.find(htmlText, '<title')
    titleEnd = string.find(htmlText, '</title>')
    leftTagEnd = string.find(htmlText, '>', titleStart)
    if leftTagEnd+1 <= titleEnd:
        title = htmlText[leftTagEnd+1:titleEnd]
    else:
        title = '*****'
    return title

def _guessAuthor(htmlText):
    #TODO
    return ''

def _guessSubhead(htmlText, mainText):
    #TODO: (a) use <h3> stuff (b) use length
    subs = []
    lines = cleanText(mainText).split('\n')

    for lineNo in range(1, len(lines) - 1):
        L = len(lines[lineNo])
        Lup = len(lines[lineNo-1])
        Ldown = len(lines[lineNo+1])

        if (L < SUBTHREDSOLD * (Lup + Ldown) / 2) and (L < MAXSUBLEN):
            subs.append(lineNo+1)
    return subs

def parseHtml(htmlText):

    """
    Input: htmlText, a string, which is a html file
    Output: a tuple, first element being the content part of the html,
            and the second element being a dictionary mapping meta labels
            with their values
    """

    mainText = extMainText(htmlText)
    ratio = 0.5 - 0.1
    while len(get_text(mainText)) < 10:
        mainText = extMainText(htmlText, ratio, True)
        ratio -= 0.1
    mainText = get_text(mainText)

    meta = {
            'title': _guessTitle(htmlText),
            'author': _guessAuthor(htmlText),
            'sub': _guessSubhead(htmlText, mainText),
            }

    return (mainText, meta)

#####  Grabber module  #####
def grab(url):

    def _isLegit(char):

        """
        Return true if char can be part of the name of a charset
        """

        if char in string.ascii_letters or \
           char in string.digits or \
           char == '-':
           return True
        else:
           return False

    def _urlClean(url):
        #TODO: transform renren.com -> www.renren.com
        res = url
        if url[:4] != 'http':
            res = 'http://www.' + url
        return res

    #End internal func

    url = _urlClean(url)

    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url, headers=hdr)
    try:
        html = urllib2.urlopen(req).read()
    except:
        pass #TODO

    #Handle encoding
    csPos = html.index('charset=') + len('charset=')
    while not _isLegit(html[csPos]):
        csPos += 1
    L = 1
    while _isLegit(html[csPos + L]):
        L += 1
    charset = html[csPos:csPos+L]
    if charset == 'gb2312':       #just to be safe
        charset = 'gbk'
    try:
        html = html.decode(charset, 'ignore')
        return html
    except UnicodeDecodeError, err:
        #TODO
        print err
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
