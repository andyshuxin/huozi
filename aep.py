#coding=utf-8

# AEP, Automatic E-magazine Processor, a set of modules that simulate
# human action in the following procedures:
#   fetching webpages,
#   extracting main text,
#   removing unnecessary characters,
#   creating doc files.

# Currenly, the modules are customized for production of 1510 Weekly.

# Copyright (C) 2013 Shu Xin

__version__ = '0.05'
__author__ = "Andy Shu Xin (andy@shux.in)"
__copyright__ = "(C) 2013 Shu Xin. GNU GPL 3."

import sys
import os
import string
import urllib2
import wx
from PIL import Image
from datetime import date, timedelta
from ExtMainText import extMainText
from ExtMainText import get_text
try:
    import win32com.client as win32
    import win32clipboard
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
               (u'\u3000',    ' '),          #Ideographic spaces
               (u'\u00A0',    ' '),          #&nbsp;
               (u'　',        ' '),          #Full-width spaces
               (u'\t',        ' '),
               ('\r\n',       '\n'),
               ('\n ',        '\n'),
               ('\n\n',       '\n'),         #duplicate paragraph breaks
               (u'\ue5f1',    ''),           #Unknown weird character in CJK
               ('......',     u'……'),
               ('...',        u'……'),
               (u'。。。。。。',  u'……'),
               (u'。。。',    u'……'),
               (u'--',        u'——'),
               (u'－－',      u'——'),
               (u'■',         ''),
              )

AUTHORMARKERS = (u'作者:', u'文:', u'作者：', u'文：')

PUNCTUATIONS = (',', '.', ':', ')', u'，', u'。', u'：', u'）')

BRA_L, BRA_R = u'【', u'】'

MAGIC_WIDTH = 120.0   # useful in portrait positioning

#####  Data strcture  #####

class Article(object):

    def __init__(self, title='', author='', authorBio='', text='', teaser='',
                 subheadLines=[], comments=[], category = '',
                 portraitPath='', url='', urlAlt=''):
        self.title = title
        self.author = author
        self.authorBio = authorBio
        self.text = text
        self.teaser = teaser
        self.subheadLines = subheadLines
        self.comments = comments
        self.category = category
        self.portraitPath = portraitPath
        self.url = url
        self.urlAlt = urlAlt

    def addSub(self, sub):
        if sub not in self.subheadLines:
            self.subheadLines.append(sub)

    def delSub(self, sub):
        if sub in self.subheadLines:
            self.subheadLines.remove(sub)

    def addComm(self, comm):
        if comm not in self.comments:
            self.comments.append(comm)

    def delComm(self, comm):
        if comm in self.comments:
            self.comments.remove(comm)

class Issue(object):

    def __init__(self, issueNum='', grandTitle='', ediRemark=''):
        self.issueNum = issueNum
        self.grandTitle = grandTitle
        self.ediRemark = ediRemark
        self.articleList = []

    def addArticle(self, article, pos=None):
        if pos is None or pos == -1:
            pos = len(self.articleList)
        self.articleList.insert(pos, article)

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
        while key in text:
            text = text.replace(key, patternPair[1])

    text = text.strip(' \n')

    ## Delete unnecessary spaces
    i = 1
    while i < len(text) - 1:
        if text[i] == ' ':
            if _isChinese(text[i-1]) or _isChinese(text[i+1]):
                text = text[:i] + text[i+1:]
                i -= 1
            elif text[i+1] == ' ':
                text = text[:i] + text[i+1:]
                i -= 1
        i += 1

    return text

#####  HTML Analyser Module  #####

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

    ## Include phase
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

    ## Exclude phase
    subs = [s for s in subs if _subOK(s)]

    return subs

def _guessMeta(htmlText, plainText):

    ## Guess title
    titleStart = htmlText.find('<title')
    titleEnd = htmlText.find('</title>')
    leftTagEnd = htmlText.find('>', titleStart)
    if leftTagEnd+1 <= titleEnd:
        title = htmlText[leftTagEnd+1:titleEnd]
    else:
        # Unusual tag structure
        title = '*****'

    ## Guess author

    # Guess from title in form of <Author: Foo bar>
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

    # Guess author from <Author: Mr. Foobar> in text
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

def analyseHTML(htmlText, ratio=None):

    """
    Input: htmlText, a string, which is a html file
    Output: a tuple, first element being the content part of the html,
            and the second element being a dictionary mapping meta labels
            with their values
    """

    mainText = extMainText(htmlText)
    if ratio:
        mainText = extMainText(htmlText, ratio, False)
    else:
        ratio = 0.5
        while (len(get_text(mainText)) <= 1) and (ratio > 0):
            mainText = extMainText(htmlText, ratio, False)
            ratio -= 0.1
    mainText = get_text(mainText)

    meta = _guessMeta(htmlText, mainText)
    meta = {'title':  meta[0],
            'author': meta[1],
            'sub':    meta[2],
           }

    return (mainText, meta)

#####  Grabber module  #####

def urlClean(url):
    url = url.encode('utf-8')
    if url[:4] != 'http':
        url = 'http://' + url
    return url

def grab(url):

    """
    Input: a URL to a webpage
    Output: the webpage, or an exception instance, if error occurs.
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
        """ Return true if char can be part of a charset statement """
        if (char in string.ascii_letters or
            char in string.digits or
            char == '-'):
           return True
        return False

    userAgent = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; Huozi)'
    req = urllib2.Request(url, headers={'User-Agent': userAgent})
    opener = urllib2.build_opener(SmartRedirectHandler(),
                                  DefaultErrorHandler())
    try:
        html = opener.open(req).read()
    except urllib2.HTTPError:
        raise RuntimeError(url, "Connection fails!")
    except urllib2.URLError:
        raise RuntimeError(url, "Bad URL!")

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
    charset = 'gbk' if charset == 'gb2312' else charset
    charset = 'big5hkscs' if charset == 'big5' else charset
    charset = 'utf-8' if (charset is None) or (charset == '') else charset
    html = html.decode(charset, 'ignore')
    return html

##### .doc Export module #####

def createDoc(issue):
    try:
        _createDoc(issue)
    except:
        print 'Shit happened'
    finally:
        # createDoc screws clipboard. better to clear it.
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()

def _createDoc(issue):
    """Polutes clipboard! Use with caution!"""

    word = win32.gencache.EnsureDispatch('Word.Application')
    doc = word.Documents.Open(os.getcwd() + r'\template.dot')

    ##### Add contents #####

    ## Cover page
    rng = doc.Content
    rng.Find.Execute(FindText='[COVERIMAGE]', ReplaceWith='')
    #TODO

    ## Editor's Remarks
    rng = doc.Content
    rng.Find.Execute(FindText='[EDITORREMARK]', ReplaceWith='')
    rng.InsertAfter(issue.ediRemark)

    ## Header
    today = date.today()
    for offset in range(7):
        pubDay = today + timedelta(days=offset)
        if pubDay.weekday() == 4:  #Friday
            break
    year, month, day = pubDay.timetuple()[:3]
    pubDayS = str(year) + u'年' + str(month) + u'月' + str(day) + u'日'
    fullTitle = (u'第' + issue.issueNum + u'期' +
                 ' ' + issue.grandTitle)

    C = win32.constants.wdHeaderFooterPrimary
    doc.Sections(1).Headers(C).Range.InsertAfter(pubDayS + ' ' + fullTitle +
                                                 '\r\n' * 2)
    doc.Sections(1).PageSetup.DifferentFirstPageHeaderFooter = True
    # No title for contents page
    doc.Sections(3).Headers(C).Range.InsertAfter(pubDayS + ' ' + fullTitle +
                                                 '\r\n' * 2)

    # Copy teaser
    docTeaser = word.Documents.Open(os.getcwd() + r'\teaser.dot')
    docTeaser.Tables(1).Range.Copy()
    docTeaser.Close()

    ## Add articles
    rng = doc.Content
    rng.Find.Execute(FindText='[ARTICLES]', ReplaceWith='')
    rng.Collapse( win32.constants.wdCollapseEnd )
    category = ''
    articleCount = len(issue.articleList)
    count = 1
    for article in issue:

        # Category name, if any
        if article.category != category:
            category = article.category
            rng.InsertAfter(BRA_L + category + BRA_R + '\r\n')
            rng.Style = win32.constants.wdStyleHeading1
            rng.Collapse( win32.constants.wdCollapseEnd )

        # Title
        rng.InsertAfter(str(articleCount) + '-' + str(count) + ' ')
        count += 1
        if article.author:
            rng.InsertAfter(article.author + u'：' + article.title + '\r\n')
        else:
            rng.InsertAfter(article.title + '\r\n')
        rng.Style = win32.constants.wdStyleHeading2
        rng.Collapse( win32.constants.wdCollapseEnd )


        # Teaser
        rng.InsertAfter('\r\n')
        rng.Collapse( win32.constants.wdCollapseEnd )
        article.portraitPos = rng.Start
        rng.Paste()
        rng.Find.Execute(FindText='[TEASER]', ReplaceWith='')
        rng.InsertAfter(article.teaser)  # Long teaser crashes Find.Execute()
        endPos = rng.End + 8  # move current position out of the table
        rng = doc.Range(endPos, endPos)
        rng.InsertAfter('\r\n')
        rng.Collapse( win32.constants.wdCollapseEnd )

        # Main text
        for line in article.text.splitlines():
            rng.Collapse( win32.constants.wdCollapseEnd )
            rng.InsertAfter(line + '\r\n')
            rng.Style = win32.constants.wdStyleNormal
            if line in article.subheadLines:
                rng.Style = win32.constants.wdStyleHeading3
        rng.InsertAfter('\r\n')
        rng.Collapse( win32.constants.wdCollapseEnd )

        # Original URL and Back To Contents
        if article.url:
            tokenLink = u'【原文链接】'
            pos = rng.End
            rng.InsertAfter(tokenLink + ' '*4)
            rngLink = doc.Range(pos, pos+len(tokenLink))
            doc.Hyperlinks.Add(Anchor=rngLink, Address=article.url)

        tokenLink = u'【回到目录】'
        pos = rng.End
        rng.InsertAfter(tokenLink + ' ')
        rngLink = doc.Range(pos, pos+len(tokenLink))
        doc.Hyperlinks.Add(Anchor=rngLink, SubAddress='TOC')

        rng.Font.Underline = False
        rng.ParagraphFormat.Alignment = win32.constants.wdAlignParagraphRight
        rng.Collapse( win32.constants.wdCollapseEnd )
        rng.InsertBreak( win32.constants.wdPageBreak )

    ### Portraits and author's bio
    for article in issue:
        anchor = doc.Range()
        anchor.Find.Execute(FindText=article.title)
            #TODO: Add format condition to avoid accidental match
        anchor.Collapse( win32.constants.wdCollapseEnd )
        anchor = doc.Range(anchor.End+2, anchor.End+2)  # easier for positioning

        # Portrait
        if article.portraitPath:
            w, h = Image.open(article.portraitPath).size
            if w > MAGIC_WIDTH:
                h = h * MAGIC_WIDTH / w
                w = MAGIC_WIDTH
            doc.Shapes.AddPicture(FileName=article.portraitPath,
                                  LinkToFile=False,
                                  SaveWithDocument=True,
                                  Left=-MAGIC_WIDTH - 27,
                                  Top=0,
                                  Width=w,
                                  Height=h,
                                  Anchor=anchor)
            top = h + 10
        else:
            top = 0

        # Bio
        textBox = doc.Shapes.AddTextbox(Orientation=1,
                                        Left=-MAGIC_WIDTH - 27,
                                        Top=top,
                                        Width=MAGIC_WIDTH,
                                        Height=120,
                                        Anchor=anchor)
        textBox.Line.Visible = False
        textBox.TextFrame.MarginBottom = 0
        textBox.TextFrame.MarginTop = 0
        textBox.TextFrame.MarginLeft = 0
        textBox.TextFrame.MarginRight = 0
        rng = textBox.TextFrame.TextRange
        rng.Text = article.authorBio
        rng.Style = win32.constants.wdStyleHeading5

    ### Table of Contents
    rng = doc.Content
    rng.Find.Execute(FindText='[TOC]', ReplaceWith='')
    doc.TablesOfContents.Add(doc.Range(rng.End, rng.End), True, 1, 2)


    # Finalizing
    doc.SaveAs(FileName=(os.getcwd() + '\\' + fullTitle),
               FileFormat=win32.constants.wdFormatDocument)
    word.Visible = True
    #word.Application.Quit()


if __name__ == '__main__':
    from test import test
    test()
