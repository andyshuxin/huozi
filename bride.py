# -*- coding: utf-8 -*-

# The Bride, a Microsoft Word document formatter.

# Currently, the module is customized for production of 1510 Weekly.

# Copyright (C) 2013 Shu Xin

__version__ = '0.81'
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

logging.info('\r\n' + '*'*3)
logging.info('The Bride running '+str(datetime.now()))

def createDocx(issue):
    pass #TODO

def createDoc(issue, savePath=None, templatePath=None, quitWord=False):
    """Create a doc based on template.dot and fill in the contents of issue."""
    if savePath is None:
        savePath = os.getcwd().decode(SYSENC) + '\\' + _getFullTitle(issue)
    if templatePath is None:
        templatePath = os.getcwd().decode(SYSENC) + r'\template.dot'
    _createDoc(issue, savePath, templatePath, quitWord)

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.CloseClipboard()

    return savePath + '.doc'  #TODO: what if savePath is specified?

def _createDoc(issue, savePath, templatePath, quitWord):
    word, doc = _initialize(issue, savePath, templatePath)
    try:
        _setCoverPage(doc, issue)
        _addEditorRemark(doc.Content, issue)
        _setHeaders(doc, issue)
        _copyTeaser(word)
        _addArticles(doc, issue)
        _addPortraitAndBio(doc, issue)
        _setTOC(doc.Content)
    except:
        word.Visible = True
    finally:
        _SeparateLongTitles(doc, issue)
        _finalize(word, doc, quitWord)

def _getFullTitle(issue):
    return u'第' + issue.issueNum + u'期' + ' ' + issue.grandTitle

def _initialize(issue, savePath, templatePath):
    logging.info('Doc creation module running %s' % str(datetime.now()))
    logging.info('Connecting MS Word')

    word = win32.gencache.EnsureDispatch('Word.Application')

    logging.info('MS Word API connection succeeded')

    doc = word.Documents.Open(templatePath)

    logging.info('Template open succeeded. Adding contents.')

    fullTitle = _getFullTitle(issue)
    try:
        doc.SaveAs(FileName=savePath.encode(SYSENC),
                   FileFormat=win32.constants.wdFormatDocument)
    except:
        raise RuntimeError("Fail to save file.")
    logging.info('File saved')

    return word, doc

def _setCoverPage(doc, issue):
    rng = doc.Content
    rng.Find.Execute(FindText='[COVERIMAGE]', ReplaceWith='')
    rng.Collapse( win32.constants.wdCollapseEnd )
    A4_WIDTH = 595.35
    A4_HEIGHT = 841.95
    if issue.coverImagePath:
        w, h = Image.open(issue.coverImagePath).size
        doc.Shapes.AddPicture(FileName=issue.coverImagePath,
                              LinkToFile=False,
                              SaveWithDocument=True,
                              Left=0,
                              Top=-12,
                              Width=A4_WIDTH,
                              Height=A4_HEIGHT,
                              Anchor=rng)
    logging.info('coverpage processed')

def _addEditorRemark(rng, issue):
    rng.Find.Execute(FindText='[EDITORREMARK]', ReplaceWith='')
    rng.InsertAfter(issue.ediRemark)
    logging.info("editor's remark processed")

def _setHeaders(doc, issue):
    year, month, day = issue.publishDate
    pubDateS = str(year) + u'年' + str(month) + u'月' + str(day) + u'日'
    fullTitle = _getFullTitle(issue)
    C = win32.constants.wdHeaderFooterPrimary
    doc.Sections(1).Headers(C).Range.InsertAfter(pubDateS + ' ' + fullTitle +
                                                 '\r\n' * 2)
    doc.Sections(1).PageSetup.DifferentFirstPageHeaderFooter = True
    # No title for contents page
    doc.Sections(3).Headers(C).Range.InsertAfter(pubDateS + ' ' + fullTitle +
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
        article.finalTitle = (str(articleCount) + '-' + str(count-1) + ' ' +
                              article.author + u'：' + article.title)
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
                rng.Style = win32.constants.wdStyleSubtitle
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

def _SeparateLongTitles(doc, issue):
    """ Find titles that are too long and separate at colon, if any.
        It's more efficient to combine the steps in _addArticle(),
        but a separate procedure has the advantage that if something
        screws up here, more critical steps would have been finished already.
    """

    def _isFullWidth(char):
        #TODO: write a more precise one
        from aep import _isCJKHan
        return _isCJKHan(char)

    for article in issue:
        wordCount = 0.0
        for char in article.finalTitle:
            if _isFullWidth(char):
                wordCount += 1
            else:
                wordCount += 0.5
        logging.info(u'weighted length: %s' % str(wordCount))
        logging.info('checking %s' % article.finalTitle)
        if wordCount > 21:
            try:
                rng = doc.Range()
                rng.Find.Execute(FindText=article.finalTitle)
                pos = article.finalTitle.rindex(u'：')
                rng = doc.Range(rng.Start+pos+1, rng.Start+pos+1)
                rng.InsertBreak(win32.constants.wdLineBreak)
            except ValueError:
                #No u'：', something is wrong.
                continue

def _setTOC(rng):
    rng.Find.Execute(FindText='[TOC]', ReplaceWith='')
    try:
        doc.TablesOfContents.Add(doc.Range(rng.End, rng.End), True, 1, 2)
        logging.info('TOC inserted')
    except:
        logging.debug('TOC creation failed')

def _finalize(word, doc, quitWord):
    doc.Save()
    if quitWord:
        word.Quit()

def openDoc(path):
    word = win32.gencache.EnsureDispatch('Word.Application')
    doc = word.Documents.Open(path)
    word.Visible = True
