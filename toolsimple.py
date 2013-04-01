#!python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Shu Xin

# Tool Simple, a simplistic DTP GUI

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# ==== Works by others ====

# ExtMainText.py:
#   Copyright (c) 2009, Elias Soong, all rights reserved.

# Redirect and Error handler in aep.py:
#   taken from Dive into Python,
#   Copyright (c) 2000, 2001, 2002, 2003, 2004 Mark Pilgrim

# In-app icons:
#   taken from Default Icon. Credit to interactivemania
#   (http://www.interactivemania.com). Except:

# Saveas icon:
#   Downloaded from
#   http://thenounproject.com/noun/save-file/#icon-No10092
#   Designed by iconoci(http://thenounproject.com/iconoci/)
#   from The Noun Project

# Applicaion icon: 
#   Downloaded from http://thenounproject.com/noun/keyboard/#icon-No3041
#   Designed by Jose Manuel Rodriguez(http://thenounproject.com/fivecity_5c),
#   from The Noun Project

# Template.dot:
#   Layout designed by Pan Wenyi, Co-China Forum. Text by Co-China Forum.
#   Copyrighted and not distributed under GPL.

__version__ = 'M/S H'
from aep import __version__ as __aepversion__
__author__ = "Andy Shu Xin (andy@shux.in)"
__copyright__ = "(C) 2013 Shu Xin. GNU GPL 3."
__language__ = "English"

import os
import sys
import wx
from aep import (Article, Issue,
                 urlClean, cleanText, createDoc,
                 xml2issue, issue2xml,
                 BRA_L, BRA_R,
                )
if __language__ == "English":
    from text_en import txt

try:
    with open('DEBUG'):
        DEBUG = True
except IOError:
    DEBUG = False

#####  UI  #####

#ATTR_NORMAL = wx.TextAttr("black", "white")      #Doesn't work on Win
#ATTR_HIGHLIGHT = wx.TextAttr('black', 'yellow')
MAGIC_HEIGHT = 90.0   # used in AddArticlesFrame, for portrait display

##### Window of Adding one Article #####

class SetArticleFrame(wx.Frame):

    """ Either add a new article with greater control over details,
        or edit an existing article """

    def __init__(self, articleArgv=None, *args, **kwargs):
        super(SetArticleFrame, self).__init__(*args, **kwargs)

        self.targetArticle = articleArgv
        if articleArgv is None:
            self.articleCandidate = Article()
        else:
            self.articleCandidate = articleArgv.copy()

        self.drawSizersAndPanel()
        self.drawLeftSide()
        self.drawRightSide()

        self.SetSize((600, 600))
        self.SetTitle(txt['AddArticleT'])
        self.Centre()
        self.urlText.SetFocus()
        self.Show(True)

    def askPortraitPath(self):
        dlgPortrait = wx.FileDialog(None, message=txt['PortraitT'],
            wildcard="Images|*.jpg;*.jpeg;*.gif;*.png;*.bmp")
        if dlgPortrait.ShowModal() == wx.ID_OK:
            portraitPath = dlgPortrait.GetPath()
            dlgPortrait.Destroy()
        else:
            portraitPath = None
        return portraitPath

    def drawSizersAndPanel(self):
        self.hBox = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxLeft = wx.BoxSizer(wx.VERTICAL)
        self.vBoxRight = wx.BoxSizer(wx.VERTICAL)
        self.hBox.Add(self.vBoxLeft, 1, flag=wx.ALL|wx.EXPAND, border=15)
        self.hBox.Add(self.vBoxRight, 0, flag=wx.ALL, border=15)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetSizerAndFit(self.hBox)

    def drawLeftSide(self):

        url = self.articleCandidate.url
        title = self.articleCandidate.title
        text = self.articleCandidate.text
        teaser = self.articleCandidate.teaser
        ratio = self.articleCandidate.ratio
        author = self.articleCandidate.author
        authorBio = self.articleCandidate.authorBio

        if self.targetArticle is None:
            ratio = '0.5'
        else:  # New article
            ratio = self.articleCandidate.ratio

        hintURL = wx.StaticText(self.panel, wx.ID_ANY, txt['URL'])
        self.vBoxLeft.Add(hintURL, 0)

        # URL block
        urlSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.urlText = wx.TextCtrl(self.panel, value=url)
        self.hintRatio = wx.StaticText(self.panel, wx.ID_ANY, txt['ratioH'])
        self.ratioText = wx.TextCtrl(self.panel, value=ratio,
                                     size=(40,10))
        self.btnAutoRetrieve = wx.Button(self.panel, label=txt['btnAutoRet'])
        urlSizer.Add(self.urlText, 1, flag=wx.EXPAND)
        urlSizer.Add(self.hintRatio, 0, flag=wx.EXPAND)
        urlSizer.Add(self.ratioText, 0, flag=wx.EXPAND)
        urlSizer.Add(self.btnAutoRetrieve, 0)
        self.vBoxLeft.Add(urlSizer, 0, flag=wx.EXPAND)
        self.btnAutoRetrieve.Bind(wx.EVT_BUTTON, self.onAutoRetrieve)

        # Main text block
        hintTitle = wx.StaticText(self.panel, wx.ID_ANY,
                                  txt['MdfTitleT'])
        self.titleText = wx.TextCtrl(self.panel, value=title,)
        self.titleText.Bind(wx.EVT_TEXT, self.onTitleTextChange)

        self.hintMainText = wx.StaticText(self.panel, wx.ID_ANY,
                                     txt['MainTextH'])
        self.mainText = wx.TextCtrl(self.panel, value=text,
                                    style=wx.TE_BESTWRAP|wx.TE_MULTILINE)
        self.hintTeaserText = wx.StaticText(self.panel, wx.ID_ANY,
                                          txt['TeaserTextH'])
        self.teaserText = wx.TextCtrl(self.panel, value=teaser,
                                      style=wx.TE_BESTWRAP|wx.TE_MULTILINE)
        self.vBoxLeft.Add(hintTitle, 0, wx.TOP, border=10)
        self.vBoxLeft.Add(self.titleText, 0, wx.BOTTOM|wx.EXPAND,
                     border=10)
        self.vBoxLeft.Add(self.hintMainText, 0, wx.TOP, border=10)
        self.vBoxLeft.Add(self.mainText, 1, flag=wx.TOP|wx.EXPAND, border=10)
        self.vBoxLeft.Add(self.hintTeaserText, 0, wx.TOP, border=10)
        self.vBoxLeft.Add(self.teaserText, 0, wx.TOP|wx.EXPAND, border=10)

        # Author block
        self.authorInfoSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxLeft.Add(self.authorInfoSizer, 0,
                          flag=wx.EXPAND|wx.TOP, border=10)
        self.hintAuthor = wx.StaticText(self.panel, wx.ID_ANY, 'Author:')
        self.authorText = wx.TextCtrl(self.panel, value=author)
        self.hintAuthorBio = wx.StaticText(self.panel, wx.ID_ANY, 'Author bio:')
        self.authorBioText = wx.TextCtrl(self.panel, value=authorBio)
        self.authorInfoSizer.Add(self.hintAuthor, 0)
        self.authorInfoSizer.Add(self.authorText, 0)
        self.authorInfoSizer.Add(self.hintAuthorBio, 0)
        self.authorInfoSizer.Add(self.authorBioText, 1, flag=wx.EXPAND)

        #Portrait block
        self.portraitBox = wx.StaticBitmap(self.panel, wx.ID_ANY,
                                           size=(100, 100))
        self.btnSetPortrait = wx.Button(self.panel, label='Set &Portrait')
        self.btnClearPortrait = wx.Button(self.panel, label='Clear P&ortrait')
        self.btnSetPortrait.Bind(wx.EVT_BUTTON, self.onSetPortrait)
        self.btnClearPortrait.Bind(wx.EVT_BUTTON, self.onClearPortrait)
        self.vBoxLeft.Add(self.portraitBox, 0, flag=wx.TOP, border=10)
        self.hBoxPortraitTools = wx.BoxSizer(wx.HORIZONTAL)
        self.hBoxPortraitTools.Add(self.btnSetPortrait, 0)
        self.hBoxPortraitTools.Add(self.btnClearPortrait, 0)
        self.vBoxLeft.Add(self.hBoxPortraitTools, 0, flag=wx.EXPAND)
        if self.targetArticle is not None:
            if self.articleCandidate.portraitPath:
                # TODO: modulize
                path = self.articleCandidate.portraitPath
                img = wx.Image(path, wx.BITMAP_TYPE_ANY)
                w, h = img.GetSize()
                if h > MAGIC_HEIGHT:
                    w = w * MAGIC_HEIGHT / h
                    h = MAGIC_HEIGHT
                    img.Rescale(w, h)
                img = img.ConvertToBitmap()
                self.portraitBox.SetBitmap(img)
                self.portraitPath = path
        else:
            self.portraitPath = ''


    def drawRightSide(self):
        self.btnOK = wx.Button(self.panel, label='&OK!')
        self.btnCancel = wx.Button(self.panel, label='&Cancel')
        self.vBoxRight.Add(self.btnOK, 0)
        self.vBoxRight.Add(self.btnCancel, 0, flag=wx.TOP, border=5)
        self.btnOK.Bind(wx.EVT_BUTTON, self.onOK)
        self.btnCancel.Bind(wx.EVT_BUTTON, self.onCancel)

        if self.targetArticle is None:
            self.btnOK.Disable()

    def onAutoRetrieve(self, e):
        mainFrame = self.GetParent()
        try:
            ratio = self.ratioText.GetValue()
            if ratio == '0.5':
                self.articleCandidate.loadURL(url=self.urlText.GetValue(),
                                              issue=mainFrame.issue,
                                              detectDuplicate=False)
            else:
                self.articleCandidate.loadURL(url=self.urlText.GetValue(),
                                              issue=mainFrame.issue,
                                              ratio=float(ratio),
                                              detectDuplicate=False)

        except RuntimeError as err:
            try:
                dlg = wx.MessageDialog(self.panel,
                                       txt['graberror'] +
                                       err[0] + ': ' + err[1],
                                       txt['graberrorCap'],
                                       wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
            except IndexError: # exception not raised by me
                raise err
            finally:
                return

        except ValueError:
            dlg = wx.MessageDialog(self.panel,
                                   'Bad threshold ratio!',
                                   'Bad threshold',
                                   wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.titleText.SetValue(self.articleCandidate.title)
        self.mainText.SetValue(self.articleCandidate.text)
        self.authorText.SetValue(self.articleCandidate.author)
        self.currentRatio = ratio

    def onOK(self, e):
        mainFrame = self.GetParent()
        index = mainFrame.articleList.GetSelection()

        url = self.urlText.GetValue()
        self.urlText.SetValue(urlClean(url))

        article = self.articleCandidate   # shorthand
        article.title = self.titleText.GetValue()
        article.author = self.authorText.GetValue()
        article.authorBio = self.authorBioText.GetValue()
        article.text = self.mainText.GetValue()
        article.teaser = self.teaserText.GetValue()
        article.url = self.urlText.GetValue()
        if hasattr(self, 'currentRatio'):
            article.ratio = self.currentRatio
        if hasattr(self, 'portraitPath'):
            article.portraitPath = self.portraitPath

        # Inner data structure
        if self.targetArticle is None:
            mainFrame.issue.addArticle(article, index)
        else:
            mainFrame.issue.replaceArticle(self.targetArticle,
                                           article)

        # Interface article list
        #TODO stop telling your parent what to do!
        if self.targetArticle is not None:
            mainFrame.articleList.SetString(index, article.title)
        else:
            if index != -1:
                mainFrame.articleList.Insert(article.title, index+1)
            else:
                mainFrame.articleList.Append(article.title)
        mainFrame.updateInfoBar(index)
        mainFrame.updateTextBox()
        mainFrame.updateCatInfo()
        mainFrame.Enable()
        self.Destroy()

    def onCancel(self, e):
        self.Destroy()
        self.GetParent().Enable()
        self.GetParent().Raise()

    def onSetPortrait(self, e):
        path = self.askPortraitPath()
        if path:
            img = wx.Image(path, wx.BITMAP_TYPE_ANY)
            w, h = img.GetSize()
            if h > MAGIC_HEIGHT:
                w = w * MAGIC_HEIGHT / h
                h = MAGIC_HEIGHT
                img.Rescale(w, h)
            img = img.ConvertToBitmap()
            self.portraitBox.SetBitmap(img)
            self.portraitPath = path
        self.Raise()

    def onClearPortrait(self, e):
        self.portraitPath = None
        self.portraitBox.SetBitmap(wx.EmptyImage(1, 1).ConvertToBitmap())

    def onTitleTextChange(self, e):
        if self.titleText.GetValue():
            self.btnOK.Enable()
        else:
            self.btnOK.Disable()


class AddArticlesFrame(wx.Frame):
    """Window where user inputs a list of urls for downloading"""

    def __init__(self, *args, **kwargs):
        super(AddArticlesFrame, self).__init__(*args, **kwargs)
        self.hBox = wx.BoxSizer(wx.HORIZONTAL)
        self.vBox1 = wx.BoxSizer(wx.VERTICAL)
        self.vBox2 = wx.BoxSizer(wx.VERTICAL)
        self.hBox.Add(self.vBox1, 1, flag=wx.EXPAND|wx.ALL, border=15)
        self.hBox.Add(self.vBox2, 0, flag=wx.EXPAND|wx.ALL, border=15)

        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetSizerAndFit(self.hBox)

        self.hintText = wx.StaticText(self.panel, wx.ID_ANY, txt['AddArticlesQ'])
        self.urlText = wx.TextCtrl(self.panel, value='', style=wx.TE_MULTILINE)
        self.vBox1.Add(self.hintText, 0, wx.EXPAND)
        self.vBox1.Add(self.urlText, 1, wx.EXPAND|wx.TOP, border=5)

        btnOK = wx.Button(self.panel, label='&Import!')
        btnCancel = wx.Button(self.panel, label='&Cancel')
        self.vBox2.Add(btnOK)
        self.vBox2.Add(btnCancel, flag=wx.TOP, border=5)
        btnOK.Bind(wx.EVT_BUTTON, self.onOK)
        btnCancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self.SetSize((400, 400))
        self.SetTitle(txt['AddArticlesT'])
        self.Centre()
        self.urlText.SetFocus()
        self.Show(True)

    def onOK(self, e):
        urls = self.urlText.GetValue().splitlines()
        if not urls:
            return
        articleList = []
        mainFrame = self.GetParent()

        for url in urls:
            try:
                article = Article()
                article.loadURL(url, mainFrame.issue,
                                detectDuplicate=True)
                articleList.append(article)
            except RuntimeError as err:
                try:
                    errorMsg = (txt['graberror']+ err[0] + ': ' + err[1])
                    dlg = wx.MessageDialog(self.panel, errorMsg,
                                           txt['graberrorCap'],
                                           wx.OK|wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                except IndexError: # exception is not tuple: not raised by me
                    raise err

        for article in articleList:
            mainFrame.issue.addArticle(article)
            mainFrame.articleList.Append(article.title)

            count = mainFrame.articleList.GetCount()
            pos = mainFrame.articleList.GetSelection()
            if (count >= 2) and (pos != -1):
                if pos != 0:
                    mainFrame.btnUp.Enable(True)
                if pos != count - 1:
                    mainFrame.btnDn.Enable(True)

        mainFrame.updateCatInfo()
        mainFrame.Enable()
        self.Destroy()

    def onCancel(self, e):
        self.GetParent().Enable()
        self.Destroy()

class TutorialFrame(object):
    pass


class MainFrame(wx.Frame):

    """ Main interactive window """

    def __init__(self, currentIssue, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.issue = currentIssue
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))
        self.drawUI()

    def drawPanels(self):
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panelInfoBar = wx.Panel(self.panel, wx.ID_ANY,
                                     style=wx.SUNKEN_BORDER)
        self.panelInfoBar.SetBackgroundColour(wx.Colour(202, 237, 218))
        self.panelInfoBar.Bind(wx.EVT_LEFT_DOWN, self.onModifyItemInfo)

    def drawBoxSizers(self):
        self.vBoxGeneral = wx.BoxSizer(wx.VERTICAL)
        self.toolbarBox = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxGeneral.Add(self.toolbarBox, 0,
                flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=5)
        self.hBox = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxGeneral.Add(self.hBox, 1, flag=wx.EXPAND)
        self.vBoxLeft = wx.BoxSizer(wx.VERTICAL)
        self.vBoxRight = wx.BoxSizer(wx.VERTICAL)
        self.hBox.Add(self.vBoxLeft, proportion=1,
                      flag=wx.EXPAND|wx.ALL, border=5)
        self.hBox.Add(self.vBoxRight, proportion=3,
                      flag=wx.EXPAND|wx.ALL, border=5)
        self.panel.SetSizerAndFit(self.vBoxGeneral)
        self.gridBox = wx.GridSizer(2, 4)   #self.gridBoxer scales better
        self.vBoxLeft.Add(self.gridBox, proportion=0, flag=wx.EXPAND)
        self.vBoxRight.Add(self.panelInfoBar, 0, flag=wx.EXPAND)

    def regToolbarBtn(self, bmPath, bmdPath):
        btn = wx.BitmapButton(self.panel, wx.ID_ANY,
                              wx.Bitmap(bmPath))
        icon = wx.Bitmap(bmdPath)
        btn.SetBitmapDisabled(icon)
        self.toolbarBox.Add(btn)
        return btn

    def regBmBtn(self, bmPath, bmdPath):
        btn = wx.BitmapButton(self.panel, wx.ID_ANY,
                              wx.Bitmap(bmPath))
        icon = wx.Bitmap(bmdPath)
        btn.SetBitmapDisabled(icon)
        return btn

    def drawMainToolbar(self):
        #self.btnNewIssue = wx.BitmapButton(self.panel, wx.ID_ANY,
                                           #wx.Bitmap('img/newissue.png'))
        #icon = wx.Bitmap('img/newissue-d.png')
        #self.btnNewIssue.SetBitmapDisabled(icon)
        #self.toolbarBox.Add(self.btnNewIssue)
        self.btnNewIssue = self.regToolbarBtn('img/newissue.png',
                                              'img/newissue-d.png')

        self.btnOpenIssue = self.regToolbarBtn('img/openissue.png',
                                               'img/openissue-d.png')

        self.btnSaveIssue = self.regToolbarBtn('img/saveissue.png',
                                               'img/saveissue-d.png')

        self.btnSaveasIssue = self.regToolbarBtn('img/saveas.png',
                                                 'img/saveas-d.png')

        self.toolbarBox.AddSpacer(10)

        self.btnConfigIssue = self.regToolbarBtn('img/configissue.png',
                                                 'img/configissue-d.png')

        self.btnGetDoc = self.regToolbarBtn('img/getdoc.png',
                                            'img/getdoc-d.png')

        self.btnPublish = self.regToolbarBtn('img/publish.png',
                                             'img/publish-d.png')

        self.toolbarBox.AddSpacer(10)

        self.btnTutorial = self.regToolbarBtn('img/tutorial.png',
                                              'img/tutorial-d.png')

        self.btnAbout = self.regToolbarBtn('img/about.png',
                                           'img/about-d.png')

        self.btnQuit = self.regToolbarBtn('img/quit.png',
                                          'img/quit-d.png')

        self.btnNewIssue.Bind(wx.EVT_BUTTON, self.onNewIssue)
        self.btnOpenIssue.Bind(wx.EVT_BUTTON, self.onOpenIssue)
        self.btnSaveIssue.Bind(wx.EVT_BUTTON, self.onSaveIssue)
        self.btnSaveasIssue.Bind(wx.EVT_BUTTON, self.onSaveAsIssue)
        self.btnConfigIssue.Bind(wx.EVT_BUTTON, self.onConfigIssue)
        self.btnGetDoc.Bind(wx.EVT_BUTTON, self.onCreateDoc)
        self.btnTutorial.Bind(wx.EVT_BUTTON, self.onTutorial)
        self.btnAbout.Bind(wx.EVT_BUTTON, self.onAbout)
        self.btnQuit.Bind(wx.EVT_BUTTON, self.onQuit)

        for btn in (self.btnSaveIssue, self.btnSaveasIssue, self.btnPublish,
                    self.btnGetDoc, self.btnConfigIssue):
            btn.Disable()

        # Not implemented
        for btn in (self.btnTutorial, self.btnAbout):
            btn.Disable()

    def drawInfoBars(self):
        # TODO: better formatting and add direct editability
        infoBarBox = wx.BoxSizer(wx.VERTICAL)
        self.infoBar1 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT)
        self.infoBar2 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT)
        self.infoBar3 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT)
        self.infoBar4 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT)

        infoBarBox.Add(self.infoBar1, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar2, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar3, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar4, 0,
                       flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)

        self.infoBar1.Bind(wx.EVT_LEFT_DOWN, self.onConfigIssue)
        self.infoBar2.Bind(wx.EVT_LEFT_DOWN, self.onModifyItemInfo)
        self.infoBar3.Bind(wx.EVT_LEFT_DOWN, self.onModifyItemInfo)
        self.infoBar4.Bind(wx.EVT_LEFT_DOWN, self.onModifyItemInfo)

        if sys.platform != 'darwin':
            boldFont = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.BOLD)
            self.infoBar1.SetFont(boldFont)

        self.panelInfoBar.SetSizerAndFit(infoBarBox)

    def drawArticleListAndButtons(self):
        self.articleList = wx.ListBox(self.panel, wx.ID_ANY,
                                      wx.DefaultPosition, wx.DefaultSize,
                                      self.issue.articleList)
        self.vBoxLeft.Add(self.articleList, proportion=1, flag=wx.EXPAND)
        self.Bind(wx.EVT_LISTBOX, self.onArticleListClick,
                  self.articleList)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.onArticleListDclick,
                  self.articleList)

        # Toolbox
        self.btnAddArticle = wx.BitmapButton(self.panel, wx.ID_ANY,
                                             wx.Bitmap('img/addarticle.png'))
        icon = wx.Bitmap('img/addarticle-d.png')
        self.btnAddArticle.SetBitmapDisabled(icon)

        self.btnAddArticles = wx.BitmapButton(self.panel, wx.ID_ANY,
                                              wx.Bitmap('img/addmany.png'))
        icon = wx.Bitmap('img/addmany-d.png')
        self.btnAddArticles.SetBitmapDisabled(icon)

        self.btnAddCategory = wx.BitmapButton(self.panel, wx.ID_ANY,
                                              wx.Bitmap('img/addcategory.png'))
        icon = wx.Bitmap('img/addcategory-d.png')
        self.btnAddCategory.SetBitmapDisabled(icon)

        self.btnDel = wx.BitmapButton(self.panel, wx.ID_DELETE,
                                     wx.Bitmap('img/delete.png'))
        icon = wx.Bitmap('img/delete-d.png')
        self.btnDel.SetBitmapDisabled(icon)

        self.btnUp = wx.BitmapButton(self.panel, wx.ID_UP,
                                     wx.Bitmap('img/up.png'))
        icon = wx.Bitmap('img/up-d.png')
        self.btnUp.SetBitmapDisabled(icon)

        self.btnDn = wx.BitmapButton(self.panel, wx.ID_DOWN,
                                     wx.Bitmap('img/down.png'))
        icon = wx.Bitmap('img/down-d.png')
        self.btnDn.SetBitmapDisabled(icon)

        self.btnMdf = wx.BitmapButton(self.panel, wx.ID_ANY,
                                     wx.Bitmap('img/modify.png'))
        icon = wx.Bitmap('img/modify-d.png')
        self.btnMdf.SetBitmapDisabled(icon)


        for button in (self.btnAddArticle, self.btnAddArticles,
                       self.btnAddCategory):
            self.gridBox.Add(button, flag=wx.EXPAND)
            button.Enable(False)
        self.gridBox.AddSpacer(0)
        for button in (self.btnUp, self.btnDn, self.btnMdf, self.btnDel):
            self.gridBox.Add(button, flag=wx.EXPAND)
            button.Enable(False)

        self.btnUp.Bind(wx.EVT_BUTTON, self.onUp)
        self.btnDn.Bind(wx.EVT_BUTTON, self.onDown)
        self.btnMdf.Bind(wx.EVT_BUTTON, self.onModifyItemInfo)
        self.btnDel.Bind(wx.EVT_BUTTON, self.onDelete)
        self.btnAddArticle.Bind(wx.EVT_BUTTON, self.onAddArticle)
        self.btnAddArticles.Bind(wx.EVT_BUTTON, self.onAddArticles)
        self.btnAddCategory.Bind(wx.EVT_BUTTON, self.onAddCategory)

    def drawTextboxAndButtons(self):
        # Maintext display and editing 
        self.textBox = wx.TextCtrl(self.panel,
                                   value='',
                                   style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.textBox.SetEditable(False)
        self.vBoxRight.Add(self.textBox, 6,
                           flag=wx.EXPAND|wx.TOP|wx.TE_BESTWRAP, border=5)
        self.textBox.SetFont(wx.Font(11, wx.ROMAN, wx.NORMAL, wx.NORMAL))

        # Buttons to manipulate the text
        self.hBoxBottom = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxRight.Add(self.hBoxBottom, 0)

        self.btnEdit = self.regBmBtn('img/edit.png',
                                     'img/edit-d.png')

        self.btnSubhead = self.regBmBtn('img/highlight.png',
                                        'img/highlight-d.png')

        self.btnComment = self.regBmBtn('img/comment.png',
                                        'img/comment-d.png')

        self.btnSave = self.regBmBtn('img/save.png',
                                     'img/save-d.png')

        for btn in (self.btnEdit, self.btnSubhead,
                    self.btnComment, self.btnSave):
            btn.Disable()
            self.hBoxBottom.Add(btn, 0)

        self.Bind(wx.EVT_BUTTON, self.onToggleSubhead, self.btnSubhead)
        self.Bind(wx.EVT_BUTTON, self.onToggleComment, self.btnComment)
        self.Bind(wx.EVT_BUTTON, self.onEditText, self.btnEdit)
        self.Bind(wx.EVT_BUTTON, self.onSaveEdit, self.btnSave)

        if DEBUG:
            btnDev = wx.Button(self.panel, -1, '[DEV]')
            self.hBoxBottom.Add(btnDev, 0)
            self.Bind(wx.EVT_BUTTON, self.printIssue, btnDev)


    def drawUI(self):

        self.drawPanels()
        self.drawBoxSizers()
        self.drawMainToolbar()
        self.drawInfoBars()
        self.drawArticleListAndButtons()
        self.drawTextboxAndButtons()

        if DEBUG:
            self.btnAddArticle.Enable(True)
            self.btnAddArticles.Enable(True)
            self.btnAddCategory.Enable(True)
            self.btnGetDoc.Enable()
            self.btnConfigIssue.Enable()

        self.Layout()
        self.SetSize((800, 600))
        self.basicTitle = (u'Tool Simple ' + __version__ +
                          ' (AEP: ' + __aepversion__ + ')')
        self.SetTitle(self.basicTitle)
        self.Centre()
        self.Show(True)

        self.currentSavePath = ''

    def onNewIssue(self, e):
        dlgYesNo = wx.MessageDialog(None,
                                    txt['ConfirmNewQ'],
                                    style=wx.YES|wx.NO)
        if dlgYesNo.ShowModal() == wx.ID_YES:
            self.issue = Issue()
            self.onConfigIssue(e)
            for btn in (self.btnSaveIssue, self.btnSaveasIssue,
                        self.btnConfigIssue):
               btn.Enable()
            self.articleList.Clear()
            self.textBox.SetValue('')
            self.currentSavePath = ''

    def onOpenIssue(self, e):
        dlgOpenPath = wx.FileDialog(None, message=txt['OpenIssueT'],
            wildcard="*.hif")
        if dlgOpenPath.ShowModal() == wx.ID_OK:
            self.articleList.Clear()
            openPath = dlgOpenPath.GetPath()
            dlgOpenPath.Destroy()
        else:
            return

        f = open(openPath, 'r')
        content = f.read()
        f.close()

        self.issue = xml2issue(content)
        self.updateInfoBar(-1)
        self.updateTextBox()
        self.updateCatInfo()
        self.refreshArticleListBox()

        self.btnAddArticle.Enable(True)
        self.btnAddArticles.Enable(True)
        self.btnAddCategory.Enable(True)
        for btn in (self.btnSaveIssue, self.btnSaveasIssue,
                    self.btnConfigIssue):
           btn.Enable()
        if os.name == 'nt':
            # TODO: Registry checking for Word
            self.btnGetDoc.Enable()

        self.currentSavePath = openPath

    def onSaveIssue(self, e):
        if not self.currentSavePath:
            self.onSaveAsIssue(e)
            if self.currentSavePath:
                self.btnSaveasIssue.Enable()
            return

        f = open(self.currentSavePath, 'w')
        content = issue2xml(self.issue)
        f.write(content)
        f.close()

    def onSaveAsIssue(self, e):
        defaultDir, defaultFile = os.path.split(self.currentSavePath)

        dlgSaveIssue = wx.FileDialog(None, message=txt['SaveIssueT'],
                defaultDir=defaultDir,
                defaultFile=defaultFile,
                style=wx.FD_SAVE|wx.OVERWRITE_PROMPT, wildcard='*.hif')
        if dlgSaveIssue.ShowModal() == wx.ID_OK:
            savePath = dlgSaveIssue.GetPath()
            dlgSaveIssue.Destroy()
            self.currentSavePath = savePath
        else:
            return
        f = open(savePath, 'w')
        content = issue2xml(self.issue)
        f.write(content)
        f.close()

    def onConfigIssue(self, e):

        """
        Set the basic information of the current issue.
        """

        issueNum = self.askInfo(txt['issueNumQ'],
                                txt['issueNumT'],
                                defaultVal=self.issue.issueNum)
        grandTitle = self.askInfo(txt['grandTitleQ'],
                                  txt['grandTitleT'],
                                  defaultVal=self.issue.grandTitle)

        ediRemark = self.askInfo(txt['ediRemarkQ'],
                                 txt['issueNumT'],
                                 defaultVal=self.issue.ediRemark,
                                 multiline=True)

        if issueNum is not None:
            self.issue.issueNum = issueNum
        if grandTitle is not None:
            self.issue.grandTitle = grandTitle
        if ediRemark is not None:
            self.issue.ediRemark = ediRemark

        self.btnAddArticle.Enable(True)
        self.btnAddArticles.Enable(True)
        self.btnAddCategory.Enable(True)
        if os.name == 'nt':
            # TODO: Registry checking for Word
            self.btnGetDoc.Enable()

        self.updateInfoBar(-1)
        self.SetTitle(self.basicTitle + ': ' +
                      'Issue ' + self.issue.issueNum +
                      self.issue.grandTitle)
        self.Enable()

    def onAddArticle(self, e):
        self.Disable()
        SetArticleFrame(articleArgv=None, parent=self)

    def onAddArticles(self, e):
        """ Ask for a list of URLs and retrieve and process them, and update
        the article list.  """
        self.Disable()
        AddArticlesFrame(self)

    def onAddCategory(self, e):
        cat = self.askInfo(txt['AddCategoryQ'],
                           txt['AddCategoryT'])
        if cat is None:
            return

        # Update articleList box
        cat = BRA_L + cat + BRA_R
        pos = self.articleList.GetSelection()
        if pos == -1:
            self.articleList.Insert(cat, 0)
        else:
            self.articleList.Insert(cat, pos)
        self.updateCatInfo()

    def onCreateDoc(self, e):
        # Backup clipboard
        if not wx.TheClipboard.IsOpened():
            wx.TheClipboard.Open()
            cp = wx.TextDataObject()
            hasCP = wx.TheClipboard.GetData(cp)
            wx.TheClipboard.Close()
        createDoc(self.issue)
        # Restore clipboard
        if hasCP and not wx.TheClipboard.IsOpened():
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(cp)
            wx.TheClipboard.Close()

    def onQuit(self, e):
        self.Close()

    def onUp(self, e):
        index = self.articleList.GetSelection()

        # Swap display
        if index != 0:
            selectedTitle = self.articleList.GetString(index)
            swappedTitle = self.articleList.GetString(index-1)
            self.articleList.Delete(index)
            self.articleList.Insert(selectedTitle, index-1)
            self.articleList.Select(index-1)
            if index == 1:
                self.btnUp.Enable(False)

        # Swap storage order
        if not (_isCat(selectedTitle) or
                _isCat(swappedTitle)):
            for article in self.issue:
                if article.title == selectedTitle:
                    artNo1 = self.issue.articleList.index(article)
                elif article.title == swappedTitle:
                    artNo2 = self.issue.articleList.index(article)
            al = self.issue.articleList
            al[artNo1], al[artNo2] = al[artNo2], al[artNo1]

        self.updateInfoBar(index-1)
        self.updateCatInfo()

        # Incorporate this with onModifyItemInfo? It break when moving
        # a category.
        self.btnUp.Enable(True)
        self.btnDn.Enable(True)
        if index - 1 == 0:
            self.btnUp.Enable(False)
        if index - 1 == self.articleList.GetCount() - 1:
            self.btnDn.Enable(False)

    def onDown(self, e):
        index = self.articleList.GetSelection()

        # Swap display
        if index != self.articleList.GetCount() - 1:
            selectedTitle = self.articleList.GetString(index)
            swappedTitle = self.articleList.GetString(index+1)
            self.articleList.Delete(index)
            self.articleList.Insert(selectedTitle, index+1)
            self.articleList.Select(index+1)
            if index == self.articleList.GetCount() - 2:
                self.btnDn.Enable(False)

        # Swap storage order
        if not (_isCat(selectedTitle) or
                _isCat(swappedTitle)):
            for article in self.issue:
                if article.title == selectedTitle:
                    artNo1 = self.issue.articleList.index(article)
                elif article.title == swappedTitle:
                    artNo2 = self.issue.articleList.index(article)
            al = self.issue.articleList
            al[artNo1], al[artNo2] = al[artNo2], al[artNo1]

        self.updateInfoBar(index+1)
        self.updateCatInfo()
        self.btnUp.Enable(True)
        self.btnDn.Enable(True)
        if index+1 == 0:
            self.btnUp.Enable(False)
        if index+1 == self.articleList.GetCount() - 1:
            self.btnDn.Enable(False)

    def onModifyItemInfo(self, e):
        index = self.articleList.GetSelection()
        if index == -1:
            return
        item = self.articleList.GetStringSelection()
        if _isCat(item):
            cat = self.askInfo(txt['MdfCategoryQ'],
                               txt['MdfCategoryT'],
                               defaultVal=item[1:-1])
            if cat is None:
                return

            # Update articleList box
            cat = BRA_L + cat + BRA_R
            self.articleList.SetString(index, cat)
            self.updateCatInfo()
        else:
            article = self.getSelectedArticle()
            SetArticleFrame(articleArgv=article,
                            parent=self)
            self.articleList.SetString(index, article.title)

    def onDelete(self, e):
        index = self.articleList.GetSelection()
        if index == -1:
            return
        selectedTitle = self.articleList.GetString(index)

        if not _isCat(selectedTitle):
            dlgYesNo = wx.MessageDialog(None,
                                        txt['DelArticle']+selectedTitle+" ?",
                                        style=wx.YES|wx.NO)
            if dlgYesNo.ShowModal() != wx.ID_YES:
                return
            selectedArticle = self.getSelectedArticle()
            self.issue.deleteArticle(selectedArticle)

        self.articleList.Delete(index)

        for button in (self.btnUp, self.btnDn, self.btnMdf, self.btnDel,
                       self.btnSubhead, self.btnComment, self.btnEdit,
                       self.btnSave):
            button.Enable(False)
        self.updateInfoBar(-1)
        self.textBox.SetValue('')
        self.updateCatInfo()

    def onEditText(self, e):

        for tool in (self.articleList, self.btnAddArticle, self.btnAddArticles,
                     self.btnAddCategory, self.btnDel, self.btnUp, self.btnDn,
                     self.btnMdf):
            tool.wasEnabled = tool.IsEnabled()
            tool.Enable(False)

        article = self.getSelectedArticle()
        self.textPre = self.textBox.GetValue()
        self.subPre = article.subheadLines

        self.textBox.SetEditable(True)

        self.btnSubhead.Enable(True)
        #self.btnComment.Enable(True)
        self.btnEdit.Enable(False)
        self.btnSave.Enable(True)

    def onSaveEdit(self, e):
        for tool in (self.articleList, self.btnAddArticle, self.btnAddArticles,
                     self.btnAddCategory, self.btnDel, self.btnUp, self.btnDn,
                     self.btnMdf):
            if tool.wasEnabled:
                tool.Enable(True)

        article = self.getSelectedArticle()
        text = self.textBox.GetValue()
        text = cleanText(text)
        article.text = text
        self.textBox.SetValue(text)
        self.updateTextBox()

        for sub in article.subheadLines:
            if sub not in text:
                article.delSub(sub)

        self.textBox.SetEditable(False)
        self.btnSubhead.Enable(False)
        self.btnComment.Enable(False)
        self.btnEdit.Enable(True)
        self.btnSave.Enable(False)

    def onArticleListClick(self, e):

        if e.GetSelection() == -1:
            return
        self.btnMdf.Enable(True)
        self.btnDel.Enable(True)
        self.btnUp.Enable(True)
        self.btnDn.Enable(True)
        self.btnEdit.Enable(True)
        if e.GetSelection() == 0:
            self.btnUp.Enable(False)
        if e.GetSelection() == self.articleList.GetCount() - 1:
            self.btnDn.Enable(False)
        if _isCat(e.GetString()):
            self.btnEdit.Enable(False)
        self.updateInfoBar(e.GetSelection())
        self.updateTextBox()

    def onArticleListDclick(self, e):
        self.onModifyItemInfo(e)

    def onToggleSubhead(self, e):

        """
        Toggles highlight of the current line and
        updates subheadLines information of the selected article.
        """

        #XXX For some reason, textBox.GetInsertionPoint is never -1, as
        #    I would expect. When the focus is off, it's 0. 

        if ((self.textBox.GetInsertionPoint() == 0) or
            (self.articleList.GetSelection() == -1)):
            return

        #Get selected article
        pos = self.textBox.GetInsertionPoint()
        text = self.textBox.GetValue()
        leftMargin = text.rfind('\n', 0, pos) + 1
        rightMargin = text.find('\n', pos)
        rightMargin = len(text) if rightMargin == -1 else rightMargin
        line = text[leftMargin:rightMargin]
        article = self.getSelectedArticle()

        # Duct tape
        if leftMargin == 0 or rightMargin == len(text):
            return
        # End Ducttap

        if line in article.subheadLines:
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr("black", "white"))
            article.subheadLines.remove(line)

        else:
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr('black', 'yellow'))
            article.subheadLines.append(line)

    def onToggleComment(self, e):
        pass

    def onAbout(self, e):
        pass

    def onTutorial(self, e):
        self.Tutorial(e)

    def showTutorial(self, e):
        TutorialFrame()

    def updateInfoBar(self, index):

        # Issue info
        issueInfo = (txt['issueNoH'] + str(self.issue.issueNum) + ' ' +
                     self.issue.grandTitle + ' ' +
                     txt['articleNo'] + str(len(self.issue.articleList))
                    )
        self.infoBar1.SetLabel(issueInfo)

        # Article info
        if index == -1 or _isCat(self.articleList.GetString(index)):
            self.infoBar2.SetLabel('')
            self.infoBar3.SetLabel('')
            self.infoBar4.SetLabel('')
            return

        selectedArticle = self.getSelectedArticle()
        if selectedArticle is None:
            return
        title = selectedArticle.title
        author = selectedArticle.author
        authorBio = selectedArticle.authorBio
        self.infoBar2.SetLabel("Article title: " + title)
        self.infoBar3.SetLabel("Author: " + author)
        self.infoBar4.SetLabel("Author's bio: " + authorBio)

    def updateTextBox(self):

        if self.articleList.GetSelection() == -1:
            return
        elif _isCat(self.articleList.GetStringSelection()):
            self.textBox.SetValue('')
            return

        index = self.articleList.GetSelection()
        selectedArticle = self.getSelectedArticle()
        self.textBox.SetValue(selectedArticle.text)

        selectedTitle = self.articleList.GetString(index)

        # Highlight subs
        text = self.textBox.GetValue()
        for subhead in selectedArticle.subheadLines:
            leftMargin = text.find(subhead)
            rightMargin = leftMargin + len(subhead)
            #XXX Duct tape for text similar to one of the subs
            while (text[leftMargin-1] != '\n' or
                   text[rightMargin] != '\n'):    # not a standalone line 
                if (leftMargin == 0 or rightMargin == len(text) or
                    leftMargin == -1 or rightMargin == -1):
                       return
                leftMargin = text.find(subhead, rightMargin)
                rightMargin = leftMargin + len(subhead)
            # End duct tape
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr('black', 'yellow'))

    def updateCatInfo(self):
        cat = ''
        for i in range(0, self.articleList.GetCount()):
            item = self.articleList.GetString(i)
            if _isCat(item):
                cat = item[1:-1]
            else:
                for article in self.issue.articleList:
                    if article.title == item:
                        article.category = cat
                        break

    def refreshArticleListBox(self):
        self.articleList.Clear()
        cat = ''
        for article in self.issue:
            if article.category != cat:
                self.articleList.Append(BRA_L + article.category + BRA_R)
                cat = article.category
            self.articleList.Append(article.title)

    def askInfo(self, prompt, dialogTitle, defaultVal='',
                multiline=False, noCancel=False):
        """ Open a dialog and ask the user for information.
            Being replaced by separate frames.  """

        style = wx.OK
        if multiline:
            style = style|wx.TE_MULTILINE
        if not noCancel:
            style = style|wx.CANCEL

        infoDialog = wx.TextEntryDialog(None, prompt, dialogTitle,
                                       defaultVal, style)

        res = None
        if infoDialog.ShowModal() == wx.ID_OK:
            res = unicode(infoDialog.GetValue())
        else:
            res = None
        infoDialog.Destroy()
        return res

    def getSelectedArticle(self):
        selectedTitle = self.articleList.GetStringSelection()
        for article in self.issue:
            if article.title == selectedTitle:
                return article
        return None

    def printIssue(self, e=None):
        s = issue2xml(self.issue).splitlines()
        for line in s:
            try:
                posA = line.index('>')
                posB = line.index('<', posA)
            except ValueError:
                continue
            if (posA + 1 != posB) or ('article' in line):
                print line

def _isCat(title):
    """Return if title is surrounded by square brackets"""
    return title.startswith(BRA_L) and title.endswith(BRA_R)

def _main():
    currentIssue = Issue()
    app = wx.App()
    MainFrame(currentIssue, None)
    app.MainLoop()

if __name__ == '__main__':
    _main()
