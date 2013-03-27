#!python
#coding=utf-8

# Copyright (C) 2013 Shu Xin

# Huozi, a simplistic DTP

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
#   (http://www.interactivemania.com).

# Applicaion icon: 
#   Downloaded from http://thenounproject.com/noun/keyboard/#icon-No3041
#   Designed by Jose Manuel Rodriguez(http://thenounproject.com/fivecity_5c),
#   from The Noun Project

# Template.dot:
#   Layout designed by Pan Wenyi, Co-China Forum. Text by Co-China Forum.
#   Copyrighted and not distributed under GPL.

__version__ = 'M/S G'
from aep import __version__ as __aepversion__
__author__ = "Andy Shu Xin (andy@shux.in)"
__copyright__ = "(C) 2013 Shu Xin. GNU GPL 3."

import os
import sys
import wx
from aep import (Article, Issue,
                 urlClean, grab, analyseHTML, cleanText, createDoc,
                 BRA_L, BRA_R
                )

try:
    with open('DEBUG'): pass
    DEBUG = True
except IOError:
    DEBUG = False


####  text  ####

txt = {'issueNumT':     "Issue Number",
       'issueNumQ':     "What's the number of issue?",
       'grandTitleT':   "General Title",
       'grandTitleQ':   "What's the general title of the issue?",
       'ediRemarkT':    "Editor's Remarks",
       'ediRemarkQ':    "What are the editor's remarks?",
       'AddArticlesT':  "Add Articles",
       'AddArticlesQ':  "URLs to the articles (one each line):",
       'URL':           "Set the URL to the article",
       'AddArticleT':   "Add Article",
       'AddCategoryT':  "Add Category",
       'AddCategoryQ':  "Name of the category:",
       'MdfCategoryT':  "Change Category",
       'MdfCategoryQ':  "Name of the category:",
       'MdfTitleT':     "Article Title",
       'MdfTitleQ':     "What's the article's title?",
       'MainTextHint':  "Preview of the main text(please avoid editing here):",
       'MdfCategoryT':  "Category",
       'MdfCategoryQ':  "Name of the category:",
       'MdfAuthorT':    "Author",
       'MdfAuthorQ':    "What's the article's author?",
       'MdfAuthorBioT': "Author Bio",
       'MdfAuthorBioQ': "What's the introduction to the author?",
       'PortraitT':     "Select Portrait File for the Author.",
       'DelArticle':    "Delete ",
       'graberror':     "Something is wrong grabbing ",
       'graberrorCap':  "Grabber Error",
       'duplicate':     "Already added the article: ",
       'duplicateCap':  "Duplicate article",
       'tglSubhead':    "Toggle sub&headline",
       'configIssueH':  "Configure the issue",
       'addArticleH':   "Add a set of articles",
       'getDocH':       "Produce doc file",
       'quitH':         "Quit",
       'AboutH':        "About",
       'issueNo':       "Issue no.",
       'articleNo':     "Total number of articles: ",
       'emptyContent':  "The webpage has too little textual content.",
       }

#####  UI  #####

ATTR_NORMAL = wx.TextAttr("black", "white")
ATTR_HIGHLIGHT = wx.TextAttr('black', 'yellow')

class BaseFrame(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(BaseFrame, self).__init__(*args, **kwargs)

    def url2Article(self, url, issue, clean=True, ratio=None,
                    detectDuplicate=False):
        """Adding one article, giving the user more control.
        If ratio is not given, try 0.5, then if there are too few contents,
        try 0.4, then 0.3...
        """

        if len(url) <= 2:
            return None

        url = urlClean(url)
        if detectDuplicate:
            for article in issue:
                if article.url == url:
                    raise RuntimeError(url, "Duplicated website!")

        htmlText = grab(url)
        if not ratio:
            ratio = 0.5
        analysis = analyseHTML(htmlText, ratio)
        mainText = cleanText(analysis[0])
        if len(mainText) <= 1:
            raise RuntimeError(url, "Can't extract content!")
        meta = analysis[1]
        currentArticle = Article(title=meta['title'],
                                 author=meta['author'],
                                 text=mainText,
                                 subheadLines=meta['sub'],
                                 url=url)
        currentArticle.ratio = unicode(ratio)
        if clean:
            currentArticle.noClean = False
        else:
            currentArticle.noClean = True
        return currentArticle

##### Window of Adding One Article #####

class SetArticleFrame(BaseFrame):

    def __init__(self, articleArgv=None, *args, **kwargs):
        super(SetArticleFrame, self).__init__(style=wx.STAY_ON_TOP,
                                               *args, **kwargs)

        self.DrawSizersAndPanel()
        self.DrawLeftSide(articleArgv)
        self.DrawRightSide(articleArgv)

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

    def DrawSizersAndPanel(self):
        self.hBox = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxLeft = wx.BoxSizer(wx.VERTICAL)
        self.vBoxRight = wx.BoxSizer(wx.VERTICAL)
        self.hBox.Add(self.vBoxLeft, 1, flag=wx.ALL|wx.EXPAND, border=15)
        self.hBox.Add(self.vBoxRight, 0, flag=wx.ALL, border=15)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetSizerAndFit(self.hBox)

    def DrawLeftSide(self, articleArgv):

        if articleArgv:
            self.articleArgv = articleArgv
            url = articleArgv.url
            title = articleArgv.title
            text = articleArgv.text
            ratio = articleArgv.ratio
            author = articleArgv.author
        else:  # New article
            self.article = Article()
            self.articleArgv = None
            url = ''
            title = ''
            text = ''
            ratio = '0.5'
            author = ''

        hintURL = wx.StaticText(self.panel, wx.ID_ANY, txt['URL'])
        self.vBoxLeft.Add(hintURL, 0)

        # URL block
        urlSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.urlText = wx.TextCtrl(self.panel, value=url)
        self.hintRatio = wx.StaticText(self.panel, wx.ID_ANY, u'Threshold:',)
        self.ratioText = wx.TextCtrl(self.panel, value=ratio,
                                     size=(40,10))
        self.btnAutoRetrieve = wx.Button(self.panel, label='&Auto retrieve')
        urlSizer.Add(self.urlText, 1, flag=wx.EXPAND)
        urlSizer.Add(self.hintRatio, 0, flag=wx.EXPAND)
        urlSizer.Add(self.ratioText, 0, flag=wx.EXPAND)
        urlSizer.Add(self.btnAutoRetrieve, 0)
        self.vBoxLeft.Add(urlSizer, 0, flag=wx.EXPAND)
        self.btnAutoRetrieve.Bind(wx.EVT_BUTTON, self.OnAutoRetrieve)

        # Main text block
        hintTitle = wx.StaticText(self.panel, wx.ID_ANY,
                                  txt['MdfTitleT'])
        self.titleText = wx.TextCtrl(self.panel, value=title,)
        self.titleText.Bind(wx.EVT_TEXT, self.OnTitleTextChange)

        hintMainText = wx.StaticText(self.panel, wx.ID_ANY,
                                     txt['MainTextHint'])
        self.mainText = wx.TextCtrl(self.panel, value=text,
                                    style=wx.TE_BESTWRAP|wx.TE_MULTILINE)
        self.vBoxLeft.Add(hintTitle, 0, wx.TOP, border=10)
        self.vBoxLeft.Add(self.titleText, 0, wx.BOTTOM|wx.EXPAND,
                     border=10)
        self.vBoxLeft.Add(hintMainText, 0, wx.TOP, border=10)
        self.vBoxLeft.Add(self.mainText, 1, flag=wx.EXPAND)

        # Author block
        self.authorInfoSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxLeft.Add(self.authorInfoSizer, 0,
                          flag=wx.EXPAND|wx.TOP, border=10)
        self.hintAuthor = wx.StaticText(self.panel, wx.ID_ANY, 'Author:')
        self.authorText = wx.TextCtrl(self.panel, value=author)
        self.authorInfoSizer.Add(self.hintAuthor, 0)
        self.authorInfoSizer.Add(self.authorText, 0)

        #Portrait block
        self.portraitBox = wx.StaticBitmap(self.panel, wx.ID_ANY,
                                           size=(100, 100))
        self.btnSetPortrait = wx.Button(self.panel, label='Set &Portrait')
        self.btnSetPortrait.Bind(wx.EVT_BUTTON, self.OnSetPortrait)
        self.vBoxLeft.Add(self.portraitBox, 0, flag=wx.TOP, border=10)
        self.vBoxLeft.Add(self.btnSetPortrait, 0)
        self.portraitPath = ''

        #self.panel.Layout()

    def DrawRightSide(self, articleArgv):
        self.btnOK = wx.Button(self.panel, label='&OK!')
        self.btnCancel = wx.Button(self.panel, label='&Cancel')
        self.vBoxRight.Add(self.btnOK, 0)
        self.vBoxRight.Add(self.btnCancel, 0, flag=wx.TOP, border=5)
        self.btnOK.Bind(wx.EVT_BUTTON, self.OnOK)
        self.btnCancel.Bind(wx.EVT_BUTTON, self.OnCancel)

        if not articleArgv:
            self.btnOK.Disable()

    def OnAutoRetrieve(self, e):
        mainFrame = self.GetParent()
        try:
            ratio =self.ratioText.GetValue()
            if ratio == '0.5':
                self.article = self.url2Article(url=self.urlText.GetValue(),
                                                issue=mainFrame.issue,
                                                clean=False,
                                                detectDuplicate=False)
            else:
                self.article = self.url2Article(url=self.urlText.GetValue(),
                                                issue=mainFrame.issue,
                                                ratio=float(ratio),
                                                clean=False,
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

        if not self.article:
            return

        self.titleText.SetValue(self.article.title)
        self.mainText.SetValue(self.article.text)
        self.authorText.SetValue(self.article.author)

    def OnOK(self, e):
        mainFrame = self.GetParent()
        if self.articleArgv:
            self.articleArgv.title = self.titleText.GetValue()
            self.articleArgv.text = self.mainText.GetValue()
            self.articleArgv.url = self.urlText.GetValue()
            self.articleArgv.ratio = self.ratioText.GetValue()  #TODO: clean up for in- and out- flow
            self.articleArgv.portraitPath = self.portraitPath
            self.article = self.articleArgv  #Delete after parenting issues solved
        else:
            self.article.title = self.titleText.GetValue()
            self.article.text = self.mainText.GetValue()
            self.article.portraitPath = self.portraitPath
            self.article.ratio = self.ratioText.GetValue()  #TODO: clean up for in- and out- flow
            mainFrame.issue.addArticle(self.article)

        #TODO stop telling your parent what to do!
        itemIndex = mainFrame.articleList.GetSelection()
        if self.articleArgv:
            mainFrame.articleList.SetString(itemIndex, self.article.title)
        else:
            mainFrame.articleList.Append(self.article.title)
        mainFrame.updateInfoBar(itemIndex)
        mainFrame.updateTextBox()
        mainFrame.updateCatInfo()
        mainFrame.Enable()
        self.Destroy()

    def OnCancel(self, e):
        self.Destroy()
        self.GetParent().Enable()

    def OnSetPortrait(self, e):
        MAGIC_HEIGHT = 90.0
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

    def OnTitleTextChange(self, e):
        if self.titleText.GetValue():
            self.btnOK.Enable()
        else:
            self.btnOK.Disable()


class AddArticlesFrame(BaseFrame):
    """Window where user inputs a list of urls for downloading"""

    def __init__(self, *args, **kwargs):
        super(AddArticlesFrame, self).__init__(style=wx.STAY_ON_TOP,
                                               *args, **kwargs)
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
        btnOK.Bind(wx.EVT_BUTTON, self.OnOK)
        btnCancel.Bind(wx.EVT_BUTTON, self.OnCancel)

        self.SetSize((400, 400))
        self.SetTitle(txt['AddArticlesT'])
        self.Centre()
        self.urlText.SetFocus()
        self.Show(True)

    def OnOK(self, e):
        urls = self.urlText.GetValue().splitlines()
        if not urls:
            return
        articleList = []
        mainFrame = self.GetParent()

        for url in urls:
            try:
                article = self.url2Article(url, mainFrame.issue)
                articleList.append(article)
            except RuntimeError as err:
                try:
                    dlg = wx.MessageDialog(self.panel,
                                           txt['graberror']+
                                           err[0] + ': ' + err[1],
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

    def OnCancel(self, e):
        self.GetParent().Enable()
        self.Destroy()


class MainFrame(wx.Frame):

    """ Main interactive window """

    def __init__(self, currentIssue, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.issue = currentIssue
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))
        self.DrawUI()

    def DrawPanels(self):
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panelInfoBar = wx.Panel(self.panel, wx.ID_ANY,
                                     style=wx.SUNKEN_BORDER)
        self.panelInfoBar.SetBackgroundColour(wx.Colour(202, 237, 218))
        self.panelInfoBar.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)

    def DrawBoxSizers(self):
        self.hBox = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxLeft = wx.BoxSizer(wx.VERTICAL)
        self.vBoxRight = wx.BoxSizer(wx.VERTICAL)
        self.hBox.Add(self.vBoxLeft, proportion=1,
                      flag=wx.EXPAND|wx.ALL, border=5)
        self.hBox.Add(self.vBoxRight, proportion=3,
                      flag=wx.EXPAND|wx.ALL, border=5)
        self.panel.SetSizerAndFit(self.hBox)
        self.gridBox = wx.GridSizer(2, 4)   #self.gridBoxer scales better
        self.vBoxLeft.Add(self.gridBox, proportion=0, flag=wx.EXPAND)
        self.vBoxRight.Add(self.panelInfoBar, 0, flag=wx.EXPAND)

    def DrawMainToolbar(self):
        self.toolbar = self.CreateToolBar()
        newIssueTool = self.toolbar.AddLabelTool(wx.ID_ANY,
                label='NewIssue',
                bitmap=wx.Bitmap('img/newissue.png'),
                shortHelp='',
                )

        openIssueTool = self.toolbar.AddLabelTool(wx.ID_ANY,
                label='OpenIssue',
                bitmap=wx.Bitmap('img/openissue.png'),
                shortHelp='',
                )

        saveIssueTool = self.toolbar.AddLabelTool(wx.ID_ANY,
                label='SaveIssue',
                bitmap=wx.Bitmap('img/saveissue.png'),
                shortHelp='',
                )

        self.toolbar.AddSeparator()

        configIssueTool = self.toolbar.AddLabelTool(wx.ID_SETUP,
                label='ConfigureIssue',
                bitmap=wx.Bitmap('img/configissue.png'),
                shortHelp=txt['configIssueH'],
                )


        self.getDocTool = self.toolbar.AddLabelTool(wx.ID_ANY,
                label='GetDoc',
                bitmap=wx.Bitmap('img/getdoc.png'),
                shortHelp=txt['getDocH'],
                )

        publishTool = self.toolbar.AddLabelTool(wx.ID_ANY,
                label='Publish',
                bitmap=wx.Bitmap('img/publish.png'),
                shortHelp='',
                )

        self.toolbar.AddSeparator()

        aboutTool = self.toolbar.AddLabelTool(wx.ID_ABOUT,
                label='About',
                bitmap=wx.Bitmap('img/about.png'),
                shortHelp=txt['AboutH'],
                )

        quitTool = self.toolbar.AddLabelTool(wx.ID_EXIT,
                label='Quit',
                bitmap=wx.Bitmap('img/quit.png'),
                shortHelp=txt['quitH'],
                )

        self.Bind(wx.EVT_TOOL, self.OnNewIssue, newIssueTool)
        self.Bind(wx.EVT_TOOL, self.OnOpenIssue, openIssueTool)
        self.Bind(wx.EVT_TOOL, self.OnSaveIssue, saveIssueTool)
        self.Bind(wx.EVT_TOOL, self.OnConfigIssue, configIssueTool)
        self.Bind(wx.EVT_TOOL, self.OnCreateDoc, self.getDocTool)
        self.Bind(wx.EVT_TOOL, self.OnAbout, aboutTool)
        self.Bind(wx.EVT_TOOL, self.OnQuit, quitTool)

        for tool in (saveIssueTool, publishTool, self.getDocTool):
            self.toolbar.EnableTool(tool.Id, False)

        #Disabled because not implemented
        for tool in (newIssueTool, openIssueTool, aboutTool):
            self.toolbar.EnableTool(tool.Id, False)

        self.toolbar.Realize()

    def DrawInfoBars(self):
        # TODO: better formatting and add direct editability
        infoBarBox = wx.BoxSizer(wx.VERTICAL)
        self.infoBar1 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER)
        self.infoBar2 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER)
        self.infoBar3 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER)
        self.infoBar4 = wx.StaticText(self.panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER)

        infoBarBox.Add(self.infoBar1, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar2, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar3, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar4, 0,
                       flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)

        self.infoBar1.Bind(wx.EVT_LEFT_DOWN, self.OnConfigIssue)
        self.infoBar2.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)
        self.infoBar3.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)
        self.infoBar4.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)

        boldFont = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.BOLD)
        self.infoBar1.SetFont(boldFont)

        self.panelInfoBar.SetSizerAndFit(infoBarBox)

    def DrawArticleListAndButtons(self):
        self.articleList = wx.ListBox(self.panel, wx.ID_ANY,
                                      wx.DefaultPosition, wx.DefaultSize,
                                      self.issue.articleList)
        self.vBoxLeft.Add(self.articleList, proportion=1, flag=wx.EXPAND)
        self.Bind(wx.EVT_LISTBOX, self.OnArticleListClick,
                  self.articleList)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnArticleListDclick,
                  self.articleList)

        # Toolbar
        self.btnAddArticle = wx.BitmapButton(self.panel, wx.ID_ANY,
                                             wx.Bitmap('img/addarticle.png'))

        self.btnAddArticles = wx.BitmapButton(self.panel, wx.ID_ANY,
                                              wx.Bitmap('img/addmany.png'))

        self.btnAddCategory = wx.BitmapButton(self.panel, wx.ID_ANY,
                                              wx.Bitmap('img/addcategory.png'))

        self.btnDel = wx.BitmapButton(self.panel, wx.ID_DELETE,
                                     wx.Bitmap('img/delete.png'))

        self.btnUp = wx.BitmapButton(self.panel, wx.ID_UP,
                                     wx.Bitmap('img/up.png'))

        self.btnDn = wx.BitmapButton(self.panel, wx.ID_DOWN,
                                     wx.Bitmap('img/down.png'))

        self.btnMdf = wx.BitmapButton(self.panel, wx.ID_ANY,
                                     wx.Bitmap('img/modify.png'))


        for button in (self.btnAddArticle, self.btnAddArticles,
                       self.btnAddCategory, self.btnDel,
                       self.btnUp, self.btnDn, self.btnMdf):
            self.gridBox.Add(button, flag=wx.EXPAND)
            button.Enable(False)

        self.btnUp.Bind(wx.EVT_BUTTON, self.OnUp)
        self.btnDn.Bind(wx.EVT_BUTTON, self.OnDown)
        self.btnMdf.Bind(wx.EVT_BUTTON, self.OnModifyItemInfo)
        self.btnDel.Bind(wx.EVT_BUTTON, self.OnDelete)
        self.btnAddArticle.Bind(wx.EVT_BUTTON, self.OnAddArticle)
        self.btnAddArticles.Bind(wx.EVT_BUTTON, self.OnAddArticles)
        self.btnAddCategory.Bind(wx.EVT_BUTTON, self.OnAddCategory)

    def DrawTextboxAndButtons(self):
        # Maintext display and editing 
        self.textBox = wx.TextCtrl(self.panel,
                                   value='',
                                   style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.textBox.SetEditable(False)
        self.vBoxRight.Add(self.textBox, 6,
                           flag=wx.EXPAND|wx.TOP|wx.TE_BESTWRAP, border=5)
        self.textBox.SetFont(wx.Font(11, wx.ROMAN, wx.NORMAL, wx.NORMAL))

        # Buttons to manipulate the text
        self.btnSubhead = wx.BitmapButton(self.panel,
                                     wx.ID_ANY,
                                     wx.Bitmap('img/highlight.png'))

        self.btnEdit = wx.BitmapButton(self.panel,
                                       wx.ID_ANY,
                                       wx.Bitmap('img/edit.png'))

        self.btnComment = wx.BitmapButton(self.panel,
                                          wx.ID_ANY,
                                          wx.Bitmap('img/comment.png'))

        self.btnSave = wx.BitmapButton(self.panel,
                                       wx.ID_ANY,
                                       wx.Bitmap('img/save.png'))
        self.btnSubhead.Enable(False)
        self.btnComment.Enable(False)
        self.btnEdit.Enable(False)
        self.btnSave.Enable(False)

        self.hBoxBottom = wx.BoxSizer(wx.HORIZONTAL)
        self.hBoxBottom.Add(self.btnEdit, 0)
        self.hBoxBottom.Add(self.btnSubhead, 0)
        self.hBoxBottom.Add(self.btnComment, 0)
        self.hBoxBottom.Add(self.btnSave, 0)
        self.vBoxRight.Add(self.hBoxBottom, 0)
        self.Bind(wx.EVT_BUTTON, self.OnToggleSubhead, self.btnSubhead)
        self.Bind(wx.EVT_BUTTON, self.OnToggleComment, self.btnComment)
        self.Bind(wx.EVT_BUTTON, self.OnEditText, self.btnEdit)
        self.Bind(wx.EVT_BUTTON, self.OnSaveEdit, self.btnSave)

        if DEBUG:
            btnDev = wx.Button(self.panel, -1, '[DEV]')
            self.hBoxBottom.Add(btnDev, 0)
            self.Bind(wx.EVT_BUTTON, self.printIssue, btnDev)


    def DrawUI(self):

        # Add components
        self.DrawPanels()
        self.DrawBoxSizers()
        self.DrawMainToolbar()
        self.DrawInfoBars()
        self.DrawArticleListAndButtons()
        self.DrawTextboxAndButtons()

        if DEBUG:
            self.btnAddArticle.Enable(True)
            self.btnAddArticles.Enable(True)
            self.btnAddCategory.Enable(True)
            self.toolbar.EnableTool(self.getDocTool.Id, True)

        # Set up main frame
        self.Layout()
        self.SetSize((800, 600))
        self.basicTitle = (u'活字 ' + __version__ +
                          ' (AEP: ' + __aepversion__ + ')')
        self.SetTitle(self.basicTitle)
        self.Centre()
        self.Show(True)

        self.firstConfig = True

    def OnNewIssue(self, e):
        pass

    def OnOpenIssue(self, e):
        pass

    def OnSaveIssue(self, e):
        pass

    def OnConfigIssue(self, e):

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

        if self.firstConfig:
            self.OnAddArticles(e)
            self.firstConfig = False

        self.btnAddArticle.Enable(True)
        self.btnAddArticles.Enable(True)
        self.btnAddCategory.Enable(True)
        if os.name == 'nt':
            # TODO: Registry checking for Word
            self.toolbar.EnableTool(self.getDocTool.Id, True)

        self.updateInfoBar(-1)
        self.SetTitle(self.basicTitle + ': ' +
                      'Issue ' + self.issue.issueNum +
                      self.issue.grandTitle)

    def OnAddArticle(self, e):
        self.Disable()
        SetArticleFrame(articleArgv=None, parent=self)

    def OnAddArticles(self, e):
        """ Ask for a list of URLs and retrieve and process them, and update
        the article list.  """
        self.Disable()
        AddArticlesFrame(self)

    def OnAddCategory(self, e):
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

    def OnCreateDoc(self, e):
        createDoc(self.issue)

    def OnQuit(self, e):
        self.Close()

    def OnUp(self, e):
        itemIndex = self.articleList.GetSelection()

        # Swap display
        if itemIndex != 0:
            selectedTitle = self.articleList.GetString(itemIndex)
            swappedTitle = self.articleList.GetString(itemIndex-1)
            self.articleList.Delete(itemIndex)
            self.articleList.Insert(selectedTitle, itemIndex-1)
            self.articleList.Select(itemIndex-1)
            if itemIndex == 1:
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

        self.updateInfoBar(itemIndex-1)
        self.updateCatInfo()

        # Incorporate this with OnModifyItemInfo? It break when moving
        # a category.
        self.btnUp.Enable(True)
        self.btnDn.Enable(True)
        if itemIndex - 1 == 0:
            self.btnUp.Enable(False)
        if itemIndex - 1 == self.articleList.GetCount() - 1:
            self.btnDn.Enable(False)

    def OnDown(self, e):
        itemIndex = self.articleList.GetSelection()

        # Swap display
        if itemIndex != self.articleList.GetCount() - 1:
            selectedTitle = self.articleList.GetString(itemIndex)
            swappedTitle = self.articleList.GetString(itemIndex+1)
            self.articleList.Delete(itemIndex)
            self.articleList.Insert(selectedTitle, itemIndex+1)
            self.articleList.Select(itemIndex+1)
            if itemIndex == self.articleList.GetCount() - 2:
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

        self.updateInfoBar(itemIndex+1)
        self.updateCatInfo()
        self.btnUp.Enable(True)
        self.btnDn.Enable(True)
        if itemIndex+1 == 0:
            self.btnUp.Enable(False)
        if itemIndex+1 == self.articleList.GetCount() - 1:
            self.btnDn.Enable(False)

    def OnModifyItemInfo(self, e):
        itemIndex = self.articleList.GetSelection()
        item = self.articleList.GetStringSelection()
        if _isCat(item):
            cat = self.askInfo(txt['MdfCategoryQ'],
                               txt['MdfCategoryT'],
                               defaultVal=item[1:-1])
            if cat is None:
                return

            # Update articleList box
            cat = BRA_L + cat + BRA_R
            self.articleList.SetString(itemIndex, cat)
            self.updateCatInfo()
        else:
            article = self.getSelectedArticle()
            SetArticleFrame(articleArgv=article,
                            parent=self)
            self.articleList.SetString(itemIndex, article.title)

    def OnDelete(self, e):
        itemIndex = self.articleList.GetSelection()
        selectedTitle = self.articleList.GetString(itemIndex)

        if not _isCat(selectedTitle):
            dlgYesNo = wx.MessageDialog(None,
                                        txt['DelArticle']+selectedTitle+" ?",
                                        style=wx.YES|wx.NO)
            if dlgYesNo.ShowModal() != wx.ID_YES:
                return
            selectedArticle = self.getSelectedArticle()
            self.issue.deleteArticle(selectedArticle)

        self.articleList.Delete(itemIndex)

        for button in (self.btnUp, self.btnDn, self.btnMdf, self.btnDel,
                       self.btnSubhead, self.btnComment, self.btnEdit,
                       self.btnSave):
            button.Enable(False)
        self.updateInfoBar(-1)
        self.textBox.SetValue('')
        self.updateCatInfo()

    def OnEditText(self, e):

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

    def OnSaveEdit(self, e):

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

    def OnArticleListClick(self, e):

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

    def OnArticleListDclick(self, e):
        self.OnModifyItemInfo(e)

    def OnToggleSubhead(self, e):

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

        if line in article.subheadLines:
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  ATTR_NORMAL)
            article.subheadLines.remove(line)

        else:
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  ATTR_HIGHLIGHT)
            article.subheadLines.append(line)

    def OnToggleComment(self, e):
        pass

    def OnAbout(self,e):
        pass

    def updateInfoBar(self, index):

        # Issue info
        issueInfo = (txt['issueNo'] + str(self.issue.issueNum) + ' ' +
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

        # Hilight subs
        text = self.textBox.GetValue()
        for subhead in selectedArticle.subheadLines:
            leftMargin = text.find(subhead)
            rightMargin = leftMargin + len(subhead)
            #XXX Duct tape for text similar to one of the subs
            while (text[leftMargin-1] != '\n' or
                   text[rightMargin] != '\n'):    # not a standalone line 
                leftMargin = text.find(subhead, rightMargin)
                rightMargin = leftMargin + len(subhead)
            # End duct tape
            self.textBox.SetStyle(leftMargin, rightMargin, ATTR_HIGHLIGHT)


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

    def printIssue(self, e):
        print self.issue.issueNum
        print self.issue.grandTitle
        print self.issue.ediRemark
        count = 1
        for article in self.issue:
            print 'Aritlce No.' + str(count)
            count += 1
            print article.title
            for sub in article.subheadLines:
                print sub.encode('utf-8')
            print article.category
            print article.portraitPath
            print article.text
            try:
                print article.ratio
            except:
                print 'No ratio'

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
