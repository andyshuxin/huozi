#!/usr/bin/env python
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

__version__ = 'M/S F'
from aep import __version__ as __AEPVERSION__
__author__ = "Andy Shu Xin (andy@shux.in)"
__copyright__ = "(C) 2013 Shu Xin. GNU GPL 3."

import os
import sys
import wx
from aep import Article, Issue
from aep import grab, analyseHTML, cleanText, createDoc, urlClean

try:
    with open('DEBUG'): pass
    DEBUG = True
except IOError:
    DEBUG = False


####  text  ####

txt = {
       'issueNumT':     "Issue Number",
       'issueNumQ':     "What's the number of issue?",
       'grandTitleT':   "General Title",
       'grandTitleQ':   "What's the general title of the issue?",
       'ediRemarkT':    "Editor's Remarks",
       'ediRemarkQ':    "What are the editor's remarks?",
       'AddArticleT':   "Add Articles",
       'AddArticleQ':   "URLs to the articles (one each line):",
       'AddCategoryT':  "Add Category",
       'AddCategoryQ':  "Name of the category:",
       'MdfTitleT':     "Article Title",
       'MdfTitleQ':     "What's the article's title?",
       'MdfCategoryT':  "Category",
       'MdfCategoryQ':  "Name of the category:",
       'MdfAuthorT':    "Author",
       'MdfAuthorQ':    "What's the article's author?",
       'MdfAuthorBioT': "Author Bio",
       'MdfAuthorBioQ': "What's the introduction to the author?",
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
       'emptyContent':  "The webpage has too little textual content",
       }

#####  UI  #####


class EmptyContentError(Exception):
    def __init__(self, url):
        self.text = txt['emptyContent']
    def __str__(self):
        return self.text

class MainFrame(wx.Frame):

    """
    Main interactive window
    """

    def __init__(self, currentIssue, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.issue = currentIssue   #issue of magazine
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))
        self.DrawUI()

    def DrawPanel(self):
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panelInfoBar = wx.Panel(self.panel, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.panelInfoBar.SetBackgroundColour(wx.Colour(202, 237, 218))
        self.panelInfoBar.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)

    def DrawBoxSizers(self):
        self.hBox = wx.BoxSizer(wx.HORIZONTAL)
        self.vBoxLeft = wx.BoxSizer(wx.VERTICAL)
        self.vBoxRight = wx.BoxSizer(wx.VERTICAL)
        self.hBox.Add(self.vBoxLeft, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        self.hBox.Add(self.vBoxRight, proportion=3, flag=wx.EXPAND|wx.ALL, border=5)
        self.panel.SetSizerAndFit(self.hBox)
        self.gridBox = wx.GridSizer(2, 3)   #self.gridBoxer scales better
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

        infoBarBox.Add(self.infoBar1, 0, flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar2, 0, flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar3, 0, flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar4, 0, flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)

        self.infoBar1.Bind(wx.EVT_LEFT_DOWN, self.OnConfigIssue)
        self.infoBar2.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)
        self.infoBar3.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)
        self.infoBar4.Bind(wx.EVT_LEFT_DOWN, self.OnModifyItemInfo)

        boldFont = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.BOLD)
        self.infoBar1.SetFont(boldFont)

        self.panelInfoBar.SetSizerAndFit(infoBarBox)

    def DrawArticleListAndButtons(self):
        self.articleList = wx.ListBox(self.panel, wx.ID_ANY, wx.DefaultPosition,
                                      wx.DefaultSize, self.issue.articleList)
        self.vBoxLeft.Add(self.articleList, proportion=1, flag=wx.EXPAND)
        self.Bind(wx.EVT_LISTBOX, self.OnArticleListClick,
                  self.articleList)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnArticleListDclick,
                  self.articleList)

        # Toolbar
        self.btnAddArticle = wx.BitmapButton(self.panel, wx.ID_ANY,
                                             wx.Bitmap('img/addarticle.png'),)

        self.btnAddCategory = wx.BitmapButton(self.panel, wx.ID_ANY,
                                              wx.Bitmap('img/addcategory.png'),)

        self.btnDel = wx.BitmapButton(self.panel, wx.ID_DELETE,
                                     wx.Bitmap('img/delete.png'),)

        self.btnUp = wx.BitmapButton(self.panel, wx.ID_UP,
                                     wx.Bitmap('img/up.png'),)

        self.btnDn = wx.BitmapButton(self.panel, wx.ID_DOWN,
                                     wx.Bitmap('img/down.png'),)

        self.btnMdf = wx.BitmapButton(self.panel, wx.ID_ANY,
                                     wx.Bitmap('img/modify.png'),)


        for button in (self.btnAddArticle, self.btnAddCategory, self.btnDel,
                       self.btnUp, self.btnDn, self.btnMdf):
            self.gridBox.Add(button, flag=wx.EXPAND)
            button.Enable(False)

        self.btnUp.Bind(wx.EVT_BUTTON, self.OnUp)
        self.btnDn.Bind(wx.EVT_BUTTON, self.OnDown)
        self.btnMdf.Bind(wx.EVT_BUTTON, self.OnModifyItemInfo)
        self.btnDel.Bind(wx.EVT_BUTTON, self.OnDelete)
        self.btnAddArticle.Bind(wx.EVT_BUTTON, self.OnAddArticles)
        self.btnAddCategory.Bind(wx.EVT_BUTTON, self.OnAddCategory)

    def DrawTextboxAndButtons(self):
        # Maintext display and editing 
        self.textBox = wx.TextCtrl(self.panel,
                                   value='',
                                   style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.textBox.SetEditable(False)
        self.vBoxRight.Add(self.textBox, 6, flag=wx.EXPAND|wx.TOP|wx.TE_BESTWRAP, border=5)
        self.textBox.SetFont(wx.Font(11, wx.ROMAN, wx.NORMAL, wx.NORMAL))
        self.Layout()

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
        self.DrawPanel()
        self.DrawBoxSizers()
        self.DrawMainToolbar()
        self.DrawInfoBars()
        self.DrawArticleListAndButtons()
        self.DrawTextboxAndButtons()

        if DEBUG:
            self.btnAddArticle.Enable(True)
            self.btnAddCategory.Enable(True)
            self.toolbar.EnableTool(self.getDocTool.Id, True)

        # Set up main frame
        self.SetSize((800, 600))
        self.basicTitle = (u'活字 ' + __version__ +
                          ' (AEP: ' + __AEPVERSION__ + ')')
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
        self.btnAddCategory.Enable(True)
        if os.name == 'nt':
            # TODO: Registry checking for Word
            self.toolbar.EnableTool(self.getDocTool.Id, True)

        self.updateInfoBar(-1)
        self.SetTitle(self.basicTitle + ': ' +
                      'Issue ' + self.issue.issueNum +
                      self.issue.grandTitle)

    def OnAddArticles(self, e):

        """
        Ask for a list of URLs and retrieve and process them, and update
        the article list.
        """

        urlText = self.askInfo(txt['AddArticleQ'],
                               txt['AddArticleT'],
                               multiline=True)
        if urlText is None:
            return
        urlList = urlText.split('\n')
        articlesToUpdate = []

        for url in urlList:
            if len(url) <= 2:
                continue

            # Deal with duplicated articles
            url = urlClean(url)
            try:
                for article in self.issue:
                    if article.url == url:
                        dlg = wx.MessageDialog(self.panel,
                                               txt['duplicate'] + url,
                                               txt['duplicateCap'],
                                               wx.OK|wx.ICON_INFORMATION)
                        dlg.ShowModal()
                        dlg.Destroy()
                        raise ValueError
            except ValueError:
                continue

            try:
                htmlText = grab(url)
                analysis = analyseHTML(htmlText)
                mainText = cleanText(analysis[0])
                if len(mainText) <= 1:
                    raise EmptyContentError(url)
                meta = analysis[1]
                currentArticle = Article(title=meta['title'], author=meta['author'],
                                         text=mainText, subheadLines=meta['sub'], url=url)
                self.issue.addArticle(currentArticle)
                articlesToUpdate.append(currentArticle)


            except EmptyContentError, err:
                dlg = wx.MessageDialog(self.panel,
                                       txt['graberror']+ url +': '+str(err),
                                       txt['graberrorCap'],
                                       wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue

            except (TypeError, RuntimeError) as err:
                dlg = wx.MessageDialog(self.panel,
                                       txt['graberror']+ url +': '+str(err),
                                       txt['graberrorCap'],
                                       wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                continue

        #Update articleList box
        pos = self.articleList.GetCount()
        for article in articlesToUpdate:
            self.articleList.Insert(article.title, pos)
            pos += 1

        count = self.articleList.GetCount()
        pos = self.articleList.GetSelection()
        if (count >= 2) and (pos != -1):
            if pos != 0:
                self.btnUp.Enable(True)
            if pos != count - 1:
                self.btnDn.Enable(True)

        self.updateCatInfo()

    def OnAddCategory(self, e):
        cat = self.askInfo(txt['AddCategoryQ'],
                           txt['AddCategoryT'])
        if cat is None:
            return

        #Update articleList box
        cat = u'【' + cat + u'】'
        pos = self.articleList.GetSelection()
        if pos == -1:
            self.articleList.Insert(cat, 0)
        else:
            self.articleList.Insert(cat, pos+1)
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
                    articleNumA = self.issue.articleList.index(article)
                elif article.title == swappedTitle:
                    articleNumB = self.issue.articleList.index(article)
            self.issue.articleList[articleNumA], self.issue.articleList[articleNumB] =\
            self.issue.articleList[articleNumB], self.issue.articleList[articleNumA]
        self.updateInfoBar(itemIndex-1)
        self.updateCatInfo()
        # On Windows, moving items does not trigger EVT_LISTBOX, which means
        # OnArticleListClick would not run, leaving buttons inproperly
        # enabled or disabled.
        if os.name == 'nt':
            self.btnUp.Enable(True)
            self.btnDn.Enable(True)
            if itemIndex-1 == 0:
                self.btnUp.Enable(False)
            if itemIndex-1 == self.articleList.GetCount() - 1:
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
                    articleNumA = self.issue.articleList.index(article)
                elif article.title == swappedTitle:
                    articleNumB = self.issue.articleList.index(article)
            self.issue.articleList[articleNumA], self.issue.articleList[articleNumB] =\
            self.issue.articleList[articleNumB], self.issue.articleList[articleNumA]
        self.updateInfoBar(itemIndex+1)
        self.updateCatInfo()
        if os.name == 'nt':
            self.btnUp.Enable(True)
            self.btnDn.Enable(True)
            if itemIndex+1 == 0:
                self.btnUp.Enable(False)
            if itemIndex+1 == self.articleList.GetCount() - 1:
                self.btnDn.Enable(False)

    def OnModifyItemInfo(self, e):
        itemIndex = self.articleList.GetSelection()
        if self.articleList.GetStringSelection()[0] == u'【':   # item is category
            cat = self.askInfo(txt['MdfCategoryQ'], txt['MdfCategoryT'],
                               self.articleList.GetStringSelection()[1:-1],
                               False, True)
            cat = u'【' + cat + u'】'
            if cat is not None:
                self.articleList.SetString(itemIndex, cat)
        else:       #item is article
            if itemIndex == -1:
                return
            selectedArticle = self.getSelectedArticle()
            title = self.askInfo(txt['MdfTitleQ'], txt['MdfTitleT'],
                                 selectedArticle.title,
                                 False, True)
            author = self.askInfo(txt['MdfAuthorQ'], txt['MdfAuthorT'],
                                  selectedArticle.author,
                                  False, True)
            authorBio = self.askInfo(txt['MdfAuthorBioQ'], txt['MdfAuthorBioT'],
                                     selectedArticle.authorBio,
                                     False, True)
            if title is not None:
                selectedArticle.title = title
            if author is not None:
                selectedArticle.author = author
            if authorBio is not None:
                selectedArticle.authorBio = authorBio

            self.articleList.SetString(itemIndex, selectedArticle.title)
            self.updateInfoBar(itemIndex)

        self.updateCatInfo()

    def OnDelete(self, e):
        itemIndex = self.articleList.GetSelection()
        selectedTitle = self.articleList.GetString(itemIndex)

        if not _isCat(selectedTitle):
            dlgYesNo = wx.MessageDialog(None, txt['DelArticle']+selectedTitle+" ?", style=wx.YES|wx.NO)
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

        for tool in (self.articleList, self.btnAddArticle, self.btnAddCategory,
                    self.btnDel, self.btnUp, self.btnDn, self.btnMdf):
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

        for tool in (self.articleList, self.btnAddArticle, self.btnAddCategory,
                    self.btnDel, self.btnUp, self.btnDn, self.btnMdf):
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

        #XXX For some weird reason, textBox.GetInsertionPoint is never -1.
        #    When the focus is off, it's 0. 

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
            #UI action: dehighlight the line
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr("black", "white"))

            #Backend action: remove subhead info 
            article.subheadLines.remove(line)

        #line not in article.sbuheadLines, add info
        else:
            #UI action: highlight the line
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr('black', 'yellow'))
            #Backend action: add subhead info 
            article.subheadLines.append(line)

    def OnToggleComment(self, e):
        pass

    def OnAbout(self,e):
        pass

    def updateInfoBar(self, index):

        issueInfo = (
                    txt['issueNo'] + str(self.issue.issueNum) + ' ' +
                    self.issue.grandTitle + ' ' +
                    txt['articleNo'] + str(len(self.issue.articleList))
                    )
        self.infoBar1.SetLabel(issueInfo)

        if index == -1:
            self.infoBar2.SetLabel('')
            self.infoBar3.SetLabel('')
            self.infoBar4.SetLabel('')
            return
        selectedTitle = self.articleList.GetString(index)
        if selectedTitle[0] == u'【':
            return
        selectedArticle = self.getSelectedArticle()
        if os.name == 'nt':
            if selectedArticle is None:
                return
        title = selectedArticle.title
        author = selectedArticle.author
        authorBio = selectedArticle.authorBio
        self.infoBar2.SetLabel("Article title: " + title)
        self.infoBar3.SetLabel("Author: " + author)
        self.infoBar4.SetLabel("Author's bio: " + authorBio)

    def updateTextBox(self):

        if ((self.articleList.GetSelection() == -1) or
            (self.articleList.GetStringSelection()[0] == u'【')):
            return
        index = self.articleList.GetSelection()

        title = self.articleList.GetStringSelection()
        #TODO replace with getSelectedArticle()
        for article in self.issue:
            if article.title == title:
                text = article.text
                break
        self.textBox.SetValue(text)

        selectedTitle = self.articleList.GetString(index)
        selectedArticle = self.getSelectedArticle()

        text = self.textBox.GetValue()
        for subhead in selectedArticle.subheadLines:
            leftMargin = text.find(subhead)
            rightMargin = leftMargin + len(subhead)
            self.textBox.SetStyle(leftMargin, rightMargin, wx.TextAttr('black', 'yellow'))


    def updateCatInfo(self):
        cat = ''
        for i in range(0, self.articleList.GetCount()):
            s = self.articleList.GetString(i)
            if _isCat(s):
                cat = s[1:-1]
            else:
                for article in self.issue.articleList:
                    if article.title == s:
                        break
                article.category = cat
        pass

    def askInfo(self, prompt, dialogTitle, defaultVal='', multiline=False, noCancel=False):

        """
        Open a dialog and ask the user for information.
        """

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
        for article in self.issue:
            print article.title
            print article.subheadLines
            print article.category

def _isCat(title):
    return title.startswith(u'【')

def _main():
    currentIssue = Issue()
    app = wx.App()
    MainFrame(currentIssue, None)
    app.MainLoop()

if __name__ == '__main__':
    _main()
