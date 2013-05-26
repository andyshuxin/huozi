# -*- coding: utf-8 -*-

# AEP, Automatic E-magazine Preprocessor, a set of modules that simulate
# human action in the following procedures:
#   1. fetching webpages;
#   2. extracting main text;
#   3. removing unnecessary characters; and
#   4. guessing meta information such as title, author, and subtitles.

# Currenly, the modules are customized for production of 1510 Weekly.

# Copyright (C) 2013 Shu Xin

__version__ = '0.94'
__author__ = "Andy Shu Xin (andy@shux.in)"
__copyright__ = "(C) 2013 Shu Xin. GNU GPL 3."

import sys
import logging
import urllib2
from copy import deepcopy
import wx
from lxml import etree
from datetime import date, datetime, timedelta
from ExtMainText import extMainText
from ExtMainText import get_text
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
    with open('DEBUG'):
        DEBUG = True
except IOError:
    DEBUG = False

SYSENC = sys.getfilesystemencoding()

BRA_L, BRA_R = u'【', u'】'

p = sys.platform
if p.startswith('linux'):
    OS = 'linux'
elif p.startswith('win'):
    OS = 'win'
elif p.startswith('darwin'):
    OS = 'mac'

MAXSUBLEN = 12        # Any line longer is assumed not subheadline
SUBTHREDSOLD = 0.4    # How relatively short a line must be to be a sub

CLEANER_BOOK = (
               # Garbages
               (u'■',         ''),
               (u'\ue5f1',    ''),           #Some private-use unicode

               # White spaces
               (u'\u3000',    ' '),          #Full-with spaces
               (u'\u00A0',    ' '),          #&nbsp;
               (u'\t',        ' '),

               # New lines
               ('\r\n',       '\n'),
               ('\n ',        '\n'),
               ('\n\n',       '\n'),         #duplicate paragraph breaks

               # Punctuations
               ('......',     u'……'),
               ('...',        u'……'),
               (u'。。。。。。',  u'……'),
               (u'。。。',    u'……'),
               (u'--',        u'——'),
               (u'－－',      u'——'),
               (u'「',        u'“'),
               (u'」',        u'”'),
               (u'『',        u'‘'),
               (u'』',        u'’'),
              )

CJK_PUNCTUATION_REPLACEMENT = (
               (',', u'，'),
               ('.', u'。'),
               ('(', u'（'),
               (')', u'）'),
              )

AUTHOR_MARKERS = (u'作者:', u'文:', u'作者：', u'文：')

PUNCTUATIONS = (',', '.', ':', ')', u'，', u'。', u'：', u'）')

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
        Use analyseHTML to extract main text and guess author and subheads,
        implicitly calling cleanText to clean title and main text.

        Input: url, str or unicode;
               issue: the issue the article is in, for duplicate check;
               ratio: the thresold ratio for main text extraction.
        """

        def _guessFileType(url):
            extDict = {
                    'pdf': 'pdf',
                    'docx': 'docx',
                    'doc': 'doc',
                    }
            ext = url.split('.')[-1]
            if ext[-1] == '/':
                ext = ext[:-1]
            return extDict.get(ext, 'html')

        if len(url) <= 2:
            return None

        url = urlClean(url)
        if detectDuplicate:
            if issue.has_url(url):
                raise RuntimeError(url, "Duplicated website!")

        fileType = _guessFileType(url)

        if fileType == 'html':
            htmlText = _grabHTML(url)
            if not ratio:
                ratio = 0.5
            analysis = _analyseHTML(htmlText, ratio)
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

        elif fileType == 'pdf':
            analysis = _analysePDF(url)
            self.title = analysis[0]
            self.author = analysis[1]
            self.text = analysis[2]
            self.subheadLines = analysis[3]
            self.url = url


    def copy(self):
        return deepcopy(self)

class Issue(object):

    def __init__(self, issueNum='999', grandTitle='', ediRemark='',
                 coverImagePath='', publishDate= ('', '', '')):
        self.issueNum = issueNum
        self.grandTitle = grandTitle
        self.ediRemark = ediRemark
        self.coverImagePath = coverImagePath
        self.publishDate = publishDate
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

    def toXML(self):
        root = etree.Element('issue')
        root.append(etree.Comment("Generated by AEP version "+__version__))
        issueNum = etree.SubElement(root, "issueNum")
        issueNum.text = self.issueNum
        grandTitle = etree.SubElement(root, "grandTitle")
        grandTitle.text = self.grandTitle
        ediRemark = etree.SubElement(root, "ediRemark")
        ediRemark.text = self.ediRemark
        coverImagePath = etree.SubElement(root, "coverImagePath")
        coverImagePath.text = self.coverImagePath
        publishDate = etree.SubElement(root, "publishDate")
        publishDate.text = ','.join(self.publishDate)

        for article in self:
            articleElement = etree.SubElement(root, "article")
            realAttrs = [attr for attr in dir(article)
                             if (not attr.startswith(r'__') and
                             isinstance(getattr(article, attr), basestring))]
            for attr in realAttrs:
                item = etree.SubElement(articleElement, attr)
                item.text = getattr(article, attr)
            subheadsElement = etree.SubElement(articleElement, "subheadLines")
            for sub in article.subheadLines:
                subElement = etree.SubElement(subheadsElement, 'sub')
                subElement.text = sub

        return etree.tostring(root, encoding='UTF-8' ,xml_declaration=True,
                              pretty_print=True)

    def fromXML(self, xmlString):
        self.clear()
        root = etree.fromstring(xmlString)
        for item in root:
            if type(item) == etree._Comment:
                continue
            if item.tag != 'article':
                if item.text is None:
                    item.text = ''
                if item.tag == 'publishDate':
                    self.publishDate = item.text.split(',')
                else:
                    setattr(self, item.tag, unicode(item.text))
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
                self.addArticle(article)

    def saveToDoc(self, savePath=None, templatePath=None):
        try:
            from bride import createDoc
        except ImportError:
            raise RuntimeError("The Bride not found. Doc creation failed")
        savePath = createDoc(self, savePath, templatePath)
        return savePath

    def clear(self):
        self.__init__()

    def has_url(self, url):
        for article in self.articleList:
            if url == article.url:
                return True
        return False

    def __iter__(self):
        for article in self.articleList:
            yield article
        # So that (for article in issue: ...) works.

#####  Clearner module  #####

def _isCJKHan(char):
    """ Rough approximation. Produces false negatives. """
    return 0x4E00 <= ord(char) <= 0x9FCC

def cleanText(text, patternBook=CLEANER_BOOK):
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
            if _isCJKHan(text[i-1]) or _isCJKHan(text[i+1]):
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
    elif _markerPos(htmlText, AUTHOR_MARKERS) is not None:
        marker, pos = _markerPos(htmlText, AUTHOR_MARKERS)
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

def _analyseHTML(htmlText, ratio=None):

    """
    Input: htmlText, a string, which is a html file;
           ratio, the thresold ratio to be used in main text extraction.
           If ratio is not given, try 0.5, then if there are too
           few contents, try 0.4, then 0.3...

    Return: a tuple (maintext, metaInfo) -
                the first element is the content part of the html, and
                the second element is a dictionary mapping meta labels
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

def _makeOpener(url):

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

    url = url.encode(SYSENC)
    userAgent = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; Huozi)'
    req = urllib2.Request(url, headers={'User-Agent': userAgent})
    opener = urllib2.build_opener(SmartRedirectHandler(),
                                  DefaultErrorHandler())
    f = opener.open(req)
    return f

def _grabHTML(url):

    """
    Input: a URL to a webpage. (doc and pdf support to be done)
    Output: the webpage.
    Will extract charset declaration, if specified, and decode. If not,
    try to call chardet to detect. If that fails (either chardet is absent or
    chardet can't determine), assume UTF-8.
    """

    def _isLegit(char):
        """ Return true if char can be part of a charset statement """
        if (char in ASCII_LETTERS or
            char in DIGITS or
            char == '-'):
           return True
        return False

    logging.info('grab running '+str(datetime.now()))

    try:
        html = _makeOpener(url).read()
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

def _analysePDF(url):

    """
    url: URL to an pdf file
    return: a tuple:
        (title, author, main_text, [subheading1, subheading2, ...])
    """

    from pdfminer.pdfinterp import PDFResourceManager, process_pdf
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from StringIO import StringIO

    def convert_pdf(pdfFile):

        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

        fp = pdfFile
        process_pdf(rsrcmgr, device, fp)
        fp.close()
        device.close()

        str = retstr.getvalue()
        retstr.close()
        return str

    pdfFile = StringIO()
    pdfFile.write(_makeOpener(url).read())

    text = convert_pdf(pdfFile)

    # TODO: Meta info extraction
    title = ''
    author = ''
    subheading = []

    return (title, author, text, subheading)
