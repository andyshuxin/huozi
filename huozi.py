#!/usr/bin/env python
#coding=utf-8

#Copyright (C) 2013 Shu Xin

#Huozi, a simplistic DTP

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#==== Works by others ====
#ExtMainText.py:
#  Copyright (c) 2009, Elias Soong, all rights reserved.
#In-app icons:
#  taken from Default Icon. Credit to interactivemania
#  (http://www.interactivemania.com).
#Applicaion icon: 
#  Downloaded from http://thenounproject.com/noun/keyboard/#icon-No3041
#  Designed by Jose Manuel Rodriguez(http://thenounproject.com/fivecity_5c),
#  from The Noun Project

__VERSION__ = 'Build 0312'
from aep import __VERSION__ as __AEPVERSION__
__AUTHOR__ = "Andy Shu Xin (andy@shux.in)"
__COPYRIGHT__ = "(C) 2013 Shu Xin. GNU GPL 3."

import os, sys
import wx
from aep import Article, Issue
from aep import grab, parseHtml, cleanText
from doc import createDoc
from urllib import urlopen

from aep import DEBUG  #Debug flag

####  text  ####

txt = {
       'issueNumT':     "Set Issue Number",
       'issueNumQ':     "What's the number of issue?",
       'grandTitleT':   "Set Grand Title for the Issue",
       'grandTitleQ':   "What's the grand title?",
       'ediRemarkQ':    "What's the editor's remark?",
       'ediRemarkT':    "Set editor's remark",
       'AddArticleQ':   "A list of wanted articles please.",
       'AddArticleT':   "Article url list",
       'MdfTitleQ':     "What's the article's title?",
       'MdfTitleT':     "Article title",
       'MdfAuthorQ':    "What's the article's author?",
       'MdfAuthorT':    "Article author",
       'DelArticle':    "Delete ",
       'btnUp':         "&Up",
       'btnDn':         "&Down",
       'btnMdf':        "&Modify",
       'btnDel':        "D&elete",
       'graberror':     "Something is wrong grabbing: ",
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
       }

#####  UI  #####

class MainFrame(wx.Frame):

    """
    Main interactive window
    """

    def __init__(self, currentIssue, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.issue = currentIssue   #issue of magazine
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))
        self.DrawUI()

    def DrawUI(self):

        # Panels
        self.panel = wx.Panel(self, wx.ID_ANY)
        panelInfoBar = wx.Panel(self.panel, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        panelInfoBar.SetBackgroundColour(wx.Colour(202, 237, 218))
        panelInfoBar.Bind(wx.EVT_LEFT_DOWN, self.OnModifyArticleInfo)

        # Box sizers
        hBox = wx.BoxSizer(wx.HORIZONTAL)
        vBoxLeft = wx.BoxSizer(wx.VERTICAL)
        vBoxRight = wx.BoxSizer(wx.VERTICAL)
        hBox.Add(vBoxLeft, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        hBox.Add(vBoxRight, proportion=3, flag=wx.EXPAND|wx.ALL, border=5)
        self.panel.SetSizerAndFit(hBox)
        gridBox = wx.GridSizer(1, 4)   #gridBoxer scales better
        vBoxLeft.Add(gridBox, proportion=0, flag=wx.EXPAND)
        vBoxRight.Add(panelInfoBar, 0, flag=wx.EXPAND)

        # Main toolbar
        self.toolbar = self.CreateToolBar()
        configIssueTool = self.toolbar.AddLabelTool(wx.ID_SETUP,
                                                    label='ConfigureIssue',
                                                    bitmap=wx.Bitmap('img/configissue.png'),
                                                    shortHelp=txt['configIssueH'],
                                                    )

        addArticleTool = self.toolbar.AddLabelTool(wx.ID_ADD,
                                                   label='AddArticle',
                                                   bitmap=wx.Bitmap('img/addarticle.png'),
                                                   shortHelp=txt['addArticleH'],
                                                   )

        getDocTool = self.toolbar.AddLabelTool(wx.ID_ANY,
                                               label='GetDoc',
                                               bitmap=wx.Bitmap('img/getdoc.png'),
                                               shortHelp=txt['getDocH'],
                                               )

        AboutTool = self.toolbar.AddLabelTool(wx.ID_ABOUT,
                                              label='About',
                                              bitmap=wx.Bitmap('img/about.png'),
                                              shortHelp=txt['AboutH'],
                                              )

        quitTool = self.toolbar.AddLabelTool(wx.ID_EXIT,
                                             label='Quit',
                                             bitmap=wx.Bitmap('img/quit.png'),
                                             shortHelp=txt['quitH'],
                                             )

        self.Bind(wx.EVT_TOOL, self.OnConfigIssue, configIssueTool)
        self.Bind(wx.EVT_TOOL, self.OnAddArticles, addArticleTool)
        self.Bind(wx.EVT_TOOL, self.OnCreateDoc, getDocTool)
        self.Bind(wx.EVT_TOOL, self.OnAbout, AboutTool)
        self.Bind(wx.EVT_TOOL, self.OnQuit, quitTool)

        if not DEBUG:
            self.toolbar.EnableTool(wx.ID_ADD, False)        #Enable after issue configured
        if os.name != 'nt':  #Is not Windows
            self.toolbar.EnableTool(getDocTool.Id, False)
        self.toolbar.Realize()

        # Information bars
        # TODO: better formatting and add direct editability
        infoBarBox = wx.BoxSizer(wx.VERTICAL)
        self.infoBar1 = wx.StaticText(panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER)
        self.infoBar2 = wx.StaticText(panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER)
        self.infoBar3 = wx.StaticText(panelInfoBar, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_CENTER)
        infoBarBox.Add(self.infoBar1, 0, flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar2, 0, flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        infoBarBox.Add(self.infoBar3, 0, flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)
        self.infoBar1.Bind(wx.EVT_LEFT_DOWN, self.OnConfigIssue)
        self.infoBar2.Bind(wx.EVT_LEFT_DOWN, self.OnModifyArticleInfo)
        self.infoBar3.Bind(wx.EVT_LEFT_DOWN, self.OnModifyArticleInfo)
        panelInfoBar.SetSizerAndFit(infoBarBox)

        # Article List
        self.articleList = wx.ListBox(self.panel, wx.ID_ANY, wx.DefaultPosition,
                                      wx.DefaultSize, self.issue.articleList)
        vBoxLeft.Add(self.articleList, proportion=1, flag=wx.EXPAND)
        self.Bind(wx.EVT_LISTBOX, self.OnArticleListClick,
                  self.articleList)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnArticleListDclick,
                  self.articleList)

        # Article list toolbox
        self.btnUp = wx.BitmapButton(self.panel, wx.ID_UP,
                                     wx.Bitmap('img/up.png'),
                                     style=wx.NO_BORDER|wx.BU_EXACTFIT)

        self.btnDn = wx.BitmapButton(self.panel, wx.ID_DOWN,
                                     wx.Bitmap('img/down.png'),
                                     style=wx.NO_BORDER|wx.BU_EXACTFIT)

        self.btnMdf = wx.BitmapButton(self.panel, wx.ID_ANY,
                                     wx.Bitmap('img/modify.png'),
                                     style=wx.NO_BORDER|wx.BU_EXACTFIT)

        self.btnDel = wx.BitmapButton(self.panel, wx.ID_DELETE,
                                     wx.Bitmap('img/delete.png'),
                                     style=wx.NO_BORDER|wx.BU_EXACTFIT)

        for button in (self.btnUp, self.btnDn, self.btnMdf, self.btnDel):
            gridBox.Add(button, flag=wx.EXPAND)
            button.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnUp, self.btnUp)
        self.Bind(wx.EVT_BUTTON, self.OnDown, self.btnDn)
        self.Bind(wx.EVT_BUTTON, self.OnModifyArticleInfo, self.btnMdf)
        self.Bind(wx.EVT_BUTTON, self.OnDelete, self.btnDel)

        # Maintext display and editing 
        self.textBox = wx.TextCtrl(self.panel,
                                   value='',
                                   style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.textBox.SetEditable(False)
        vBoxRight.Add(self.textBox, 6, flag=wx.EXPAND|wx.TOP|wx.TE_BESTWRAP, border=5)
        self.textBox.SetFont(wx.Font(11, wx.ROMAN, wx.NORMAL, wx.NORMAL))
        self.Layout()
        self.Bind(wx.EVT_TEXT, self.OnTextChange, self.textBox)

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

        hBoxBottom = wx.BoxSizer(wx.HORIZONTAL)
        hBoxBottom.Add(self.btnEdit, 0)
        hBoxBottom.Add(self.btnSubhead, 0)
        hBoxBottom.Add(self.btnComment, 0)
        hBoxBottom.Add(self.btnSave, 0)
        vBoxRight.Add(hBoxBottom, 0)
        self.Bind(wx.EVT_BUTTON, self.OnToggleSubhead, self.btnSubhead)
        self.Bind(wx.EVT_BUTTON, self.OnToggleComment, self.btnComment)
        self.Bind(wx.EVT_BUTTON, self.OnEditText, self.btnEdit)
        self.Bind(wx.EVT_BUTTON, self.OnSaveEdit, self.btnSave)

        if DEBUG:
            btnDev = wx.Button(self.panel, -1, '[DEV]')
            hBoxBottom.Add(btnDev, 0)
            self.Bind(wx.EVT_BUTTON, self.printIssue, btnDev)

        #Main window
        self.SetSize((800, 600))
        self.basicTitle = (u'畢昇 ' + __VERSION__ + 
                          ' (on AEP ' + __AEPVERSION__ + ')')
        self.SetTitle(self.basicTitle)
        self.Centre()
        self.Show(True)

        self.firstConfig = True

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

        if issueNum != None:
            self.issue.issueNum = issueNum
        if grandTitle != None:
            self.issue.grandTitle = grandTitle
        if ediRemark != None:
            self.issue.ediRemark = ediRemark

        if self.firstConfig:
            self.OnAddArticles(None)
            self.firstConfig = False

        self.toolbar.EnableTool(wx.ID_ADD, True)

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
        if urlText == None:
            return
        urlList = urlText.split('\n')
        articlesToUpdate = []
        for url in urlList:
            if url == '\n':
                break
            try:
                for article in self.issue:
                    duplicate = False
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
                parsed = parseHtml(htmlText)
                mainText = cleanText(parsed[0])
                meta = parsed[1]
                currentArticle = Article(meta['title'], meta['author'],
                                         mainText, meta['sub'], url=url)
                self.issue.addArticle(currentArticle)
                articlesToUpdate.append(currentArticle)
            except TypeError, err:
                dlg = wx.MessageDialog(self.panel,
                                       txt['graberror']+ url +': '+str(err),
                                       txt['graberrorCap'],
                                       wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

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


    def OnCreateDoc(self, e):
        createDoc(self.issue)

    def OnQuit(self, e):
        self.Close()

    def OnUp(self, e):
        itemIndex = self.articleList.GetSelection()
        if itemIndex != 0:
            selectedTitle = self.articleList.GetString(itemIndex)
            swappedTitle = self.articleList.GetString(itemIndex-1)
            self.articleList.Delete(itemIndex)
            self.articleList.Insert(selectedTitle, itemIndex-1)
            self.articleList.Select(itemIndex-1)
            if itemIndex == 1:
                self.btnUp.Enable(False)

        for article in self.issue:
            if article.title == selectedTitle:
                articleNumA = self.issue.articleList.index(article)
            elif article.title == swappedTitle:
                articleNumB = self.issue.articleList.index(article)
        self.issue.articleList[articleNumA], self.issue.articleList[articleNumB] =\
        self.issue.articleList[articleNumB], self.issue.articleList[articleNumA]
        self.updateInfoBar(itemIndex-1)

    def OnDown(self, e):
        itemIndex = self.articleList.GetSelection()
        if itemIndex != self.articleList.GetCount() - 1:
            selectedTitle = self.articleList.GetString(itemIndex)
            swappedTitle = self.articleList.GetString(itemIndex+1)
            self.articleList.Delete(itemIndex)
            self.articleList.Insert(selectedTitle, itemIndex+1)
            self.articleList.Select(itemIndex+1)
            if itemIndex == self.articleList.GetCount() - 2:
                self.btnDn.Enable(False)

        for article in self.issue:
            if article.title == selectedTitle:
                articleNumA = self.issue.articleList.index(article)
            elif article.title == swappedTitle:
                articleNumB = self.issue.articleList.index(article)
        self.issue.articleList[articleNumA], self.issue.articleList[articleNumB] =\
        self.issue.articleList[articleNumB], self.issue.articleList[articleNumA]
        self.updateInfoBar(itemIndex+1)


    def OnModifyArticleInfo(self, e):
        itemIndex = self.articleList.GetSelection()
        if itemIndex == -1:
            return
        selectedArticle = self.getSelectedArticle()
        title = self.askInfo(txt['MdfTitleQ'], txt['MdfTitleT'],
                             selectedArticle.title,
                             False, True)
        author = self.askInfo(txt['MdfAuthorQ'], txt['MdfAuthorT'],
                              selectedArticle.author,
                              False, True)
        selectedArticle.title = title
        selectedArticle.author = author

        self.articleList.SetString(itemIndex, selectedArticle.title)
        self.updateInfoBar(itemIndex)

    def OnDelete(self, e):
        itemIndex = self.articleList.GetSelection()
        selectedTitle = self.articleList.GetString(itemIndex)
        dlgYesNo = wx.MessageDialog(None, txt['DelArticle']+selectedTitle+" ?", style=wx.YES|wx.NO)
        if dlgYesNo.ShowModal() != wx.ID_YES:
            return
        selectedArticle = self.getSelectedArticle()
        self.articleList.Delete(itemIndex)
        self.issue.deleteArticle(selectedArticle)
        for button in (self.btnUp, self.btnDn, self.btnMdf, self.btnDel,
                       self.btnSubhead, self.btnComment, self.btnEdit,
                       self.btnSave):
            button.Enable(False)
        self.updateInfoBar(-1)
        self.textBox.SetValue('')

    def OnEditText(self, e):
        article = self.getSelectedArticle()
        self.textPre = self.textBox.GetValue()
        self.subPre = article.subheadLines

        self.textBox.SetEditable(True)

        self.btnSubhead.Enable(True)
        self.btnComment.Enable(True)
        self.btnEdit.Enable(False)
        self.btnSave.Enable(True)

    def OnSaveEdit(self, e):
        article = self.getSelectedArticle()
        text = self.textBox.GetValue()
        text = cleanText(text)
        article.text = text
        self.textBox.SetValue(text)
        self.updateTextBox(-1)

        self.ProcessChange()

        self.textBox.SetEditable(False)
        self.btnSubhead.Enable(False)
        self.btnComment.Enable(False)
        self.btnEdit.Enable(True)
        self.btnSave.Enable(False)
        pass

    def OnTextChange(self, e):
        pass

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
        self.updateInfoBar(e.GetSelection())
        self.updateTextBox(e.GetSelection())

    def OnArticleListDclick(self, e):
        self.OnModifyArticleInfo(e)

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
        fulltext = self.textBox.GetValue()
        leftMargin = fulltext.rfind('\n', 0, pos)
        rightMargin = fulltext.find('\n', pos)
        line = fulltext[leftMargin:rightMargin]
        print leftMargin, rightMargin
        print line
        article = self.getSelectedArticle()
        print line in article.subheadLines

        #line already in subheads, remove it 
        if line in article.subheadLines:
            #UI action: dehighlight the line
            try:
                leftMargin = fulltext.rindex('\n', 0, pos)
            except ValueError:
                leftMargin = 0
            try:
                rightMargin = fulltext.find('\n', pos)
            except ValueError:
                rightMargin = self.textBox.GetLastPosition()
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr("black", "white"))

            #Backend action: remove subhead info 
            article.subheadLines.remove(line)
            print article.subheadLines

        #lineNo not in article.sbuheadLines, add info
        else:
            #UI action: highlight the line
            try:
                leftMargin = fulltext.rindex('\n', 0, pos)
            except ValueError:
                leftMargin = 0
            try:
                rightMargin = fulltext.find('\n', pos)
            except ValueError:
                rightMargin = self.textBox.GetLastPosition()
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr('black', 'yellow'))
            #Backend action: add subhead info 
            article.subheadLines.append(line)
            print article.subheadLines

    def OnToggleComment(self, e):
        pass

    def OnAbout(self,e):
        pass

    def updateInfoBar(self, index):

        #if self.issue.articleList == []:
            #return

        issueInfo = (
                    txt['issueNo'] + str(self.issue.issueNum) + ' ' +
                    self.issue.grandTitle +
                    txt['articleNo'] + str(len(self.issue.articleList))
                    )
        self.infoBar1.SetLabel(issueInfo)

        if index == -1:
            self.infoBar2.SetLabel('')
            self.infoBar3.SetLabel('')
            return
        selectedTitle = self.articleList.GetString(index)
        selectedArticle = self.getSelectedArticle()
        title = selectedArticle.title
        author = selectedArticle.author
        self.infoBar2.SetLabel('Article title: ' + title)
        self.infoBar3.SetLabel('Author: ' + author)

    def updateTextBox(self, index):

        if self.articleList.GetSelection() == -1:
            return

        title = self.articleList.GetStringSelection()
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
            rightMargin = leftMargin + len(subhead) + 1
            self.textBox.SetStyle(leftMargin, rightMargin, wx.TextAttr('black', 'yellow'))

    def ProcessChange(self):

        """
        Update article.subheadLines after main text is changed by user.
        """
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
        if infoDialog.ShowModal() == wx.ID_OK:  #TODO Scrutize input
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


def main():
    currentIssue = Issue()
    app = wx.App()
    MainFrame(currentIssue, None)
    app.MainLoop()

if __name__ == '__main__':
    main()
