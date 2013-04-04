# -*- coding: utf-8 -*-

# The Bride, a Microsoft Word template adapter.

# Currenly, the module is customized for production of 1510 Weekly.

# Copyright (C) 2013 Shu Xin

__version__ = '0.80'
__author__ = "Andy Shu Xin (andy@shux.in)"
__copyright__ = "(C) 2013 Shu Xin. GNU GPL 3."

import os
import logging
from PIL import Image
from datetime import date, datetime, timedelta
try:
    import win32com.client as win32
    import win32clipboard
    hasPyWin = True
except ImportError:
    hasPyWin = False

from aep import SYSENC, BRA_L, BRA_R
MAGIC_WIDTH = 120.0 # roughly equals to left page margin

logging.basicConfig(filename='bride.log', level=logging.DEBUG)
logging.info('\r\n' + '='*30)
logging.info('The Bride running '+str(datetime.now()))

def createDocx(issue):
    pass

def createDoc(issue):
    """Create a doc based on template.dot and fill in the contents of issue."""
    _createDoc(issue)
    # createDoc screws clipboard. Better to clear it afterwards.
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.CloseClipboard()

def _createDoc(issue):
    word, doc = _initialize(issue)
    _setCoverPage(doc.Content, issue)
    _addEditorRemark(doc.Content, issue)
    _setHeaders(doc, issue)
    _copyTeaser(word)
    _addArticles(doc, issue)
    _addPortraitAndBio(doc, issue)
    _setTOC(doc.Content)
    _finalize(word)

def _getPublishDate():
    """ Return (year, month, day) of the coming Friday.
        If today is Friday, return date of today.  """
    today = date.today()
    for offset in range(7):
        pubDay = today + timedelta(days=offset)
        if pubDay.weekday() == 4:  #Friday
            break
    return pubDay.timetuple()[:3]

def _getFullTitle(issue):
    return u'第' + issue.issueNum + u'期' + ' ' + issue.grandTitle

def _initialize(issue):
    logging.info('Doc creation module running %s' % str(datetime.now()))
    logging.info('Connecting MS Word')

    word = win32.gencache.EnsureDispatch('Word.Application')

    logging.info('MS Word API connection succeeded')

    doc = word.Documents.Open(os.getcwd().decode(SYSENC) + r'\template.dot')

    logging.info('Template open succeeded. Adding contents.')

    fullTitle = _getFullTitle(issue)
    doc.SaveAs(FileName=(os.getcwd().decode(SYSENC) + u'\\' + fullTitle),
               FileFormat=win32.constants.wdFormatDocument)
    logging.info('File saved')

    return word, doc

def _setCoverPage(rng, issue):
    rng.Find.Execute(FindText='[COVERIMAGE]', ReplaceWith='')
    #TODO
    logging.info('coverpage processed')

def _addEditorRemark(rng, issue):
    rng.Find.Execute(FindText='[EDITORREMARK]', ReplaceWith='')
    rng.InsertAfter(issue.ediRemark)
    logging.info("editor's remark processed")

def _setHeaders(doc, issue):
    year, month, day = _getPublishDate()
    pubDayS = str(year) + u'年' + str(month) + u'月' + str(day) + u'日'
    fullTitle = _getFullTitle(issue)
    C = win32.constants.wdHeaderFooterPrimary
    doc.Sections(1).Headers(C).Range.InsertAfter(pubDayS + ' ' + fullTitle +
                                                 '\r\n' * 2)
    doc.Sections(1).PageSetup.DifferentFirstPageHeaderFooter = True
    # No title for contents page
    doc.Sections(3).Headers(C).Range.InsertAfter(pubDayS + ' ' + fullTitle +
                                                 '\r\n' * 2)
    logging.info("Header processed")

def _copyTeaser(word):
    docTeaser = word.Documents.Open(os.getcwd() + r'\teaser.dot')
    docTeaser.Tables(1).Range.Copy()
    docTeaser.Close()
    logging.info("Teaser table copied. Adding articles")

def _addArticles(doc, issue):
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
        rng.InsertAfter(article.teaser)
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

def _addPortraitAndBio(doc, issue):
    for article in issue:
        anchor = doc.Range()
        anchor.Find.Execute(FindText=article.title)
            #TODO: Add format condition to avoid accidental match
        anchor.Collapse( win32.constants.wdCollapseEnd )
        anchor = doc.Range(anchor.End+2, anchor.End+2)

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

def _setTOC(rng):
    rng.Find.Execute(FindText='[TOC]', ReplaceWith='')
    try:
        doc.TablesOfContents.Add(doc.Range(rng.End, rng.End), True, 1, 2)
        logging.info('TOC inserted')
    except:
        logging.debug('TOC creation failed')

def _finalize(word):
    word.Visible = True
    logging.info('Word made visible')
