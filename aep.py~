# -*- coding: utf-8 -*-

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
import logging
import urllib2
from copy import deepcopy
import wx
from PIL import Image
from lxml import etree
from datetime import date, datetime, timedelta
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

##### logging config #####
logging.basicConfig(filename='aep.log', level=logging.DEBUG)
logging.info('\r\n' + '='*30)
logging.info('AEP running '+str(datetime.now()))

#####  Constants  #####

try:
    with open('DEBUG'): pass
    DEBUG = True
except IOError:
    DEBUG = False

SYSENC = sys.getfilesystemencoding()

### Not used; to be tested ###
p = sys.platform
if p.startswith('linux'):
    OS = 'linux'
elif p.startswith('win'):
    OS = 'win'
elif p.startswith('darwin'):
    OS = 'mac'
### End to be tested ###

MAXSUBLEN = 12        # Any line longer is assumed not subheadline
SUBTHREDSOLD = 0.4    # How relatively short a line must be to be a sub

CLEANERBOOK = ((u'\u3000',    ' '),          #Full-with spaces
               (u'\u00A0',    ' '),          #&nbsp;
               (u'\t',        ' '),
               ('\r\n',       '\n'),
               ('\n ',        '\n'),
               ('\n\n',       '\n'),         #duplicate paragraph breaks
               (u'\ue5f1',    ''),           #Some private-use unicode garbage
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

ASCII_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
DIGITS = '0123456789'

FALLBACKENC = 'utf-8'

#####  Data strcture  #####

class Article(object):

    def __init__(self, title='', author='', authorBio='', text='', teaser='',
                 subheadLines=[], comments=[], category='',
                 portraitPath='', url='', urlAlt='', ratio='0.5'):
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
        self.ratio = ratio

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

    def loadURL(self, url, issue, ratio=None, detectDuplicate=False):
        """
        Load self with the contents of what url directs to.
        Use analyseHTML to extract main text and guess author and subheads.
        Implicitly calling cleanText to clean title and main text.

        Input: url, str or unicode
               issue: the issue the article is in; only to check duplicates.
               ratio: the thresold ratio for main text extraction.
        """

        if len(url) <= 2:
            return None

        url = urlClean(url)
        if detectDuplicate:
            urlList = [article.url for article in issue]
            if url in urlList:
                raise RuntimeError(url, "Duplicated website!")

        htmlText = grab(url)
        if not ratio:
            ratio = 0.5
        analysis = analyseHTML(htmlText, ratio)
        mainText = cleanText(analysis[0])
        if len(mainText) <= 1:
            raise RuntimeError(url, "Can't extract content!")

        meta = analysis[1]
        self.title = meta['title']
        self.author = meta['author']
        self.text = mainText
        self.subheadLines = meta['sub']
        self.url = url
        self.ratio = unicode(ratio)

    def copy(self):
        return deepcopy(self)

class Issue(object):

    def __init__(self, issueNum='999', grandTitle='', ediRemark=''):
        self.issueNum = issueNum
        self.grandTitle = grandTitle
        self.ediRemark = ediRemark
        self.articleList = []

    def addArticle(self, article, pos=None):
        """ Insert article to the article list, by default to the end. """
        if pos is None or pos == -1:
            pos = len(self.articleList)
        self.articleList.insert(pos, article)

    def deleteArticle(self, article):
        """ Delete article from article list. """
        self.articleList.remove(article)

    def replaceArticle(self, articleToDelete, articleToAdd):
        """Delete articleToDelete and put articleToAdd in its position"""
        try:
            i = self.articleList.index(articleToDelete)
            self.articleList.remove(articleToDelete)
            self.articleList.insert(i, articleToAdd)
        except ValueError:
            return

    def __iter__(self):
        for article in self.articleList:
            yield article
        # So that (for article in issue:) works.

#####  Clearner module  #####

def _isChinese(char):
    """ A very rough approximation. Produces false negatives. """
    return 0x4E00 <= ord(char) < 0x9FCC

def cleanText(text, patternBook=CLEANERBOOK):
    """
    Replace contents according to patterns in patternBook, delete all spaces
    next to Chinese characters, and combine consective spaces.
    """

    logging.info('cleanText running '+str(datetime.now()))
    if len(text) > 20:
        logging.info('cleanText input: %s ...' % text[20])
    else:
        logging.info('cleanText input: %s ...' % text)

    if len(text) <= 2:
        return text

    for patternPair in patternBook:
        key, replacement = patternPair[0], patternPair[1]
        while key in text:
            text = text.replace(key, replacement)

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

    logging.info('cleanText about to return')
    return text

#####  HTML Analyser #####

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
    Input: htmlText, a string, which is a html file;
           ratio, the thresold ratio to be used in main text extraction.
           If ratio is not given, try 0.5, then if there are too
           few contents, try 0.4, then 0.3...
    Return: a tuple (maintext, metaInfo) -
                the first element is the content part of the html,
                and the second element is a dictionary mapping meta labels
                with their values.
    """

    logging.info('analyseHtml running '+str(datetime.now()))

    mainText = extMainText(htmlText)
    if ratio:
        mainText = extMainText(htmlText, ratio, False)
    else:
        ratio = 0.5
        while (len(get_text(mainText)) <= 1) and (ratio > 0):
            mainText = extMainText(htmlText, ratio, False)
            ratio -= 0.1
    mainText = get_text(mainText)

    metaSeq = _guessMeta(htmlText, mainText)
    meta = {'title':  metaSeq[0],
            'author': metaSeq[1],
            'sub':    metaSeq[2],
           }

    logging.info('analyseHtml about to return')
    return (mainText, meta)

#####  Grabber #####

def urlClean(url):
    if url[:4] != 'http':
        url = 'http://' + url
    return url

def grab(url):

    """
    Input: a URL to a webpage. (doc and pdf support to be done)
    Output: the webpage.
    Will extract charset declaration, if specified, and decode. If not,
    try to call chardet to detect. If that fails (either chardet is absent or
    chardet can't determine), assume UTF-8.
    """

    logging.info('grab running '+str(datetime.now()))

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
        if (char in ASCII_LETTERS or
            char in DIGITS or
            char == '-'):
           return True
        return False

    url = url.encode(SYSENC)
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
    logging.info('grab(): detected charset %s' % charset)
    html = html.decode(charset, 'ignore')
    logging.info('grab about to return')
    return html

##### MS .doc Formatter #####

def createDoc(issue):
    _createDoc(issue)
    # createDoc screws clipboard. better to clear it.
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.CloseClipboard()

def _createDoc(issue):

    """Polutes clipboard! Use with caution!"""

    def _getPublishDate():
        today = date.today()
        for offset in range(7):
            pubDay = today + timedelta(days=offset)
            if pubDay.weekday() == 4:  #Friday
                break
        return pubDay.timetuple()[:3]

    logging.info('Doc creation module running %s' % str(datetime.now()))
    logging.info('Connecting MS Word')
    word = win32.gencache.EnsureDispatch('Word.Application')
    logging.info('MS Word API connection succeeded')
    logging.info(os.getcwd())
    doc = word.Documents.Open(os.getcwd().decode(SYSENC) + r'\template.dot')
    logging.info('Template open succeeded. Adding contents.')

    ##### Add contents #####

    ## Cover page
    rng = doc.Content
    rng.Find.Execute(FindText='[COVERIMAGE]', ReplaceWith='')
    #TODO
    logging.info('coverpage processed')

    ## Editor's Remarks
    rng = doc.Content
    rng.Find.Execute(FindText='[EDITORREMARK]', ReplaceWith='')
    rng.InsertAfter(issue.ediRemark)
    logging.info("editor's remark processed")

    ## Header
    year, month, day = _getPublishDate()
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
    logging.info("Header processed")

    # Copy teaser
    docTeaser = word.Documents.Open(os.getcwd() + r'\teaser.dot')
    docTeaser.Tables(1).Range.Copy()
    docTeaser.Close()
    logging.info("Teaser table copied. Adding articles")

    ## Add articles
    rng = doc.Content
    rng.Find.Execute(FindText='[ARTICLES]', ReplaceWith='')
    rng.Collapse( win32.constants.wdCollapseEnd )
    category = ''
    articleCount = len(issue.articleList)
    count = 1
    for article in issue:

        logging.info("Adding article %s" % article.title)
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
        logging.info('Title "%s" inserted' % article.title)

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
        logging.info('Teaser inserted, length=%s' % str(len(article.text)))

        # Main text
        for line in article.text.splitlines():
            rng.Collapse( win32.constants.wdCollapseEnd )
            rng.InsertAfter(line + '\r\n')
            rng.Style = win32.constants.wdStyleNormal
            if line in article.subheadLines:
                rng.Style = win32.constants.wdStyleHeading3
        rng.InsertAfter('\r\n')
        rng.Collapse( win32.constants.wdCollapseEnd )
        logging.info('Main text inserted, length=%s' % str(len(article.text)))

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
        logging.info('links added')

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
        logging.info('portrait and bio inserted')

    ### Table of Contents
    rng = doc.Content
    rng.Find.Execute(FindText='[TOC]', ReplaceWith='')
    try:
        doc.TablesOfContents.Add(doc.Range(rng.End, rng.End), True, 1, 2)
	logging.info('TOC inserted')
    except:
	logging.debug('TOC creation failed')

    # Finalizing
    doc.SaveAs(FileName=(os.getcwd().decode(SYSENC) + u'\\' + fullTitle),
               FileFormat=win32.constants.wdFormatDocument)
    logging.info('File saved')
    word.Visible = True
    logging.info('Word made visible')
    #word.Application.Quit()

##### XML Reader and Writer modules #####

def issue2xml(issue):
    logging.info('issue2xml running '+str(datetime.now()))

    root = etree.Element('issue')
    root.append(etree.Comment("Generated by AEP version "+__version__))
    issueNum = etree.SubElement(root, "issueNum")
    issueNum.text = issue.issueNum
    grandTitle = etree.SubElement(root, "grandTitle")
    grandTitle.text = issue.grandTitle
    ediRemark = etree.SubElement(root, "ediRemark")
    ediRemark.text = issue.ediRemark

    for article in issue:
        articleElement = etree.SubElement(root, "article")
        realAttrs = [s for s in dir(article)
                         if (not s.startswith(r'__') and
                         isinstance(getattr(article, s), basestring))]
        for attr in realAttrs:
            item = etree.SubElement(articleElement, attr)
            item.text = getattr(article, attr)
        subheadsElement = etree.SubElement(articleElement, "subheadLines")
        for sub in article.subheadLines:
            subElement = etree.SubElement(subheadsElement, 'sub')
            subElement.text = sub

    logging.info('issue2xml about to return')
    return etree.tostring(root, encoding='UTF-8' ,xml_declaration=True,
                          pretty_print=True)

def xml2issue(xmlString):
    logging.info('xml2issue running '+str(datetime.now()))
    issue = Issue()

    root = etree.fromstring(xmlString)
    for item in root:
        if type(item) == etree._Comment:
            continue
        if item.tag != 'article':
            if item.text is None:
                item.text = ''
            setattr(issue, item.tag, unicode(item.text))
        else:
            article = Article()
            for attr in item:
                if attr.tag != 'subheadLines':
                    if attr.text is None:
                        attr.text = ''
                    setattr(article, attr.tag, unicode(attr.text))
                else:
                    article.subheadLines = []
                    for sub in attr:
                        article.subheadLines.append(sub.text)
            issue.addArticle(article)

    logging.info('xml2issue about to return')
    return issue


if __name__ == '__main__':
    from test import test
    test()
