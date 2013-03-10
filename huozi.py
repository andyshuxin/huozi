#!/usr/bin/env python
#coding=utf-8

# Huozi, GUI for AEP module; currently customized for production
# of 1510 Weekly.
__VERSION__ = 'Build 0001'
from aep import __VERSION__ as __AEPVERSION__
__AUTHOR__ = "Andy Shu Xin (andy@shux.in)"
__COPYRIGHT__ = "(C) 2013 Shu Xin. GNU GPL 3."

import os
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
       'graberror':     "Something is wrong grabbing:",
       'graberrorCap':  "Grabber Error",
       }

#####  UI  #####

class HuoziMainFrame(wx.Frame):

    """
    Main interactive window of Huozi
    """

    def __init__(self, currentIssue, *args, **kwargs):
        super(HuoziMainFrame, self).__init__(*args, **kwargs)
        self.issue = currentIssue   #issue of magazine
        self.InitUI()

    def InitUI(self):


        #Panel, sole and only
        self.panel = wx.Panel(self, wx.ID_ANY)

        #Box sizers
        hBox = wx.BoxSizer(wx.HORIZONTAL)
        vBoxLeft = wx.BoxSizer(wx.VERTICAL)
        vBoxRight = wx.BoxSizer(wx.VERTICAL)
        gridBox = wx.GridSizer(2, 2)
        hBox.Add(vBoxLeft, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        hBox.Add(vBoxRight, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        vBoxLeft.Add(gridBox, proportion=0, flag=wx.EXPAND)
        self.panel.SetSizerAndFit(hBox)

        #Information bars
        ##TODO: modulize
        self.infoBar1 = wx.StaticText(self.panel, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_TOP)
        self.infoBar2 = wx.StaticText(self.panel, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_TOP)
        self.infoBar3 = wx.StaticText(self.panel, wx.ID_ANY, '',
                                wx.DefaultPosition, wx.DefaultSize,
                                style=wx.ALIGN_LEFT|wx.ALIGN_TOP)
        vBoxRight.Add(self.infoBar1, 0, flag=wx.TOP|wx.EXPAND)
        vBoxRight.Add(self.infoBar2, 0, flag=wx.TOP|wx.EXPAND)
        vBoxRight.Add(self.infoBar3, 0, flag=wx.TOP|wx.EXPAND)

        #Article List
        self.articleList = wx.ListBox(self.panel, wx.ID_ANY, wx.DefaultPosition,
                                      wx.DefaultSize, self.issue.articleList)
        vBoxLeft.Add(self.articleList, proportion=1, flag=wx.EXPAND)
        self.Bind(wx.EVT_LISTBOX, self.OnArticleListClick,
                  self.articleList)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnArticleListDclick,
                  self.articleList)

        #Buttons
        self.btnUp = wx.Button(self.panel, wx.ID_UP, txt['btnUp'])
        self.btnDn = wx.Button(self.panel, wx.ID_DOWN, txt['btnDn'])
        self.btnMdf = wx.Button(self.panel, wx.ID_ANY, txt['btnMdf'])
        self.btnDel = wx.Button(self.panel, wx.ID_DELETE, txt['btnDel'])
        for button in (self.btnUp, self.btnDn, self.btnMdf, self.btnDel):
            gridBox.Add(button, 0, flag=wx.EXPAND)
            button.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnUp, self.btnUp)
        self.Bind(wx.EVT_BUTTON, self.OnDown, self.btnDn)
        self.Bind(wx.EVT_BUTTON, self.OnModify, self.btnMdf)
        self.Bind(wx.EVT_BUTTON, self.OnDelete, self.btnDel)

        #Maintext Window
        self.textBox = wx.TextCtrl(self.panel,
                                   value='Select articles to view content',
                                   style=wx.TE_MULTILINE|wx.TE_RICH2)
        vBoxRight.Add(self.textBox, 1, flag=wx.EXPAND|wx.BOTTOM|wx.TE_BESTWRAP)
        self.Layout()
        self.Bind(wx.EVT_TEXT, self.OnTextBoxChanged, self.textBox)

        #Maintext Buttons 
        btnSubhead = wx.Button(self.panel, -1, 'Toggle sub&headline')
        hBoxBottom = wx.BoxSizer(wx.HORIZONTAL)
        hBoxBottom.Add(btnSubhead, 0)
        vBoxRight.Add(hBoxBottom, 0)
        self.Bind(wx.EVT_BUTTON, self.OnToggleSubhead, btnSubhead)

        if DEBUG:
            btnDev = wx.Button(self.panel, -1, '[DEV]Print issue to CLI')
            hBoxBottom.Add(btnDev, 0)
            self.Bind(wx.EVT_BUTTON, self.printIssue, btnDev)

        #Toolbar
        self.toolbar = self.CreateToolBar()
        configIssueTool = self.toolbar.AddLabelTool(wx.ID_SETUP, 'ConfigureIssue', wx.Bitmap('img/configissue.png'))
        addArticleTool = self.toolbar.AddLabelTool(wx.ID_ADD, 'AddArticle', wx.Bitmap('img/addarticle.png'))
        getDocTool = self.toolbar.AddLabelTool(wx.ID_ANY, 'Generate MS Word', wx.Bitmap('img/spare.png'))
        quitTool = self.toolbar.AddLabelTool(wx.ID_EXIT, 'Quit', wx.Bitmap('img/exit.png'))

        self.Bind(wx.EVT_TOOL, self.OnConfigIssue, configIssueTool)
        self.Bind(wx.EVT_TOOL, self.OnAddArticles, addArticleTool)
        self.Bind(wx.EVT_TOOL, self.OnGetDoc, getDocTool)
        self.Bind(wx.EVT_TOOL, self.OnQuit, quitTool)
        if not DEBUG:
            self.toolbar.EnableTool(wx.ID_ADD, False)        #Enable after issue configured
        if os.name != 'nt':  #Is not Windows
            self.toolbar.EnableTool(getDocTool.Id, False)

        self.toolbar.Realize()


        #Main window
        self.SetSize((800, 600))
        self.basicTitle = u'活字 ' + __VERSION__ + \
                          ' (on AEP ' + __AEPVERSION__ + ')'
        self.SetTitle(self.basicTitle)
        self.Centre()
        self.Show(True)

        self.firstConfig = True

    def OnConfigIssue(self, e):

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
        self.SetTitle(self.basicTitle + ': ' + \
                      'Issue ' + self.issue.issueNum + \
                      self.issue.grandTitle)

    def OnAddArticles(self, e):
        urlText = self.askInfo(txt['AddArticleQ'],
                               txt['AddArticleT'],
                               multiline=True)
        if urlText == None:
            return
        urlList = urlText.split('\n')
        articleToUpdate = []
        for url in urlList:
            if url == '\n':
                break
            try:
                htmlText = grab(url)
                parsed = parseHtml(htmlText)
                mainText = cleanText(parsed[0])
                meta = parsed[1]
                currentArticle = Article(cleanText(meta['title']), meta['author'],
                                         mainText, meta['sub'])
                self.issue.addArticle(currentArticle)
                articleToUpdate.append(currentArticle)
            except:
                dlg = wx.MessageDialog(self.panel,
                                       txt['graberror'] + url,
                                       txt['graberrorCap'],
                                       wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

        #Update articleList box
        pos = self.articleList.GetCount()
        for article in articleToUpdate:
            self.articleList.Insert(article.title, pos)
            pos += 1

    def OnGetDoc(self, e):
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

        for article in self.issue.articleList:
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

        for article in self.issue.articleList:
            if article.title == selectedTitle:
                articleNumA = self.issue.articleList.index(article)
            elif article.title == swappedTitle:
                articleNumB = self.issue.articleList.index(article)
        self.issue.articleList[articleNumA], self.issue.articleList[articleNumB] =\
        self.issue.articleList[articleNumB], self.issue.articleList[articleNumA]
        self.updateInfoBar(itemIndex+1)


    def OnModify(self, e):
        itemIndex = self.articleList.GetSelection()
        selectedTitle = self.articleList.GetString(itemIndex)   #TODO Modulize this
        for article in self.issue.articleList:
            if article.title == selectedTitle:
                chosenArticle = article
                break
        chosenArticle.title = self.askInfo(txt['MdfTitleQ'], txt['MdfTitleT'],
                                           chosenArticle.title,
                                           False, True)
        chosenArticle.author = self.askInfo(txt['MdfAuthorQ'], txt['MdfAuthorT'],
                                            chosenArticle.author,
                                            False, True)
        self.articleList.Delete(itemIndex)
        self.articleList.Insert(chosenArticle.title, itemIndex)
        self.articleList.Select(itemIndex)
        self.updateInfoBar(itemIndex)

    def OnDelete(self, e):
        itemIndex = self.articleList.GetSelection()
        selectedTitle = self.articleList.GetString(itemIndex)
        dlgYesNo = wx.MessageDialog(None, txt['DelArticle']+selectedTitle+" ?", style=wx.YES|wx.NO)
        if dlgYesNo.ShowModal() != wx.ID_YES:
            return
        for article in self.issue.articleList:
            if article.title == selectedTitle:
                chosenArticle = article
                break
        self.articleList.Delete(itemIndex)
        self.issue.deleteArticle(chosenArticle)
        for button in (self.btnUp, self.btnDn, self.btnMdf, self.btnDel):
            button.Enable(False)
        self.infoBar2.SetLabel('')
        self.infoBar3.SetLabel('')
        self.textBox.SetValue('')

    def OnArticleListClick(self, e):
        self.btnMdf.Enable(True)
        self.btnDel.Enable(True)
        self.btnUp.Enable(True)
        self.btnDn.Enable(True)
        if e.GetSelection() == 0:
            self.btnUp.Enable(False)
        if e.GetSelection() == self.articleList.GetCount() - 1:
            self.btnDn.Enable(False)
        self.updateInfoBar(e.GetSelection())
        self.updateTextBox(e.GetSelection())

    def OnArticleListDclick(self, e):
        self.OnModify(e)

    def OnTextBoxChanged(self, e):
        if self.articleList.GetSelection() != -1:   #TODO: modulize
            selectedTitle = self.articleList.GetStringSelection()
            for article in self.issue.articleList:
                if article.title == selectedTitle:
                    article.text = self.textBox.GetValue()
                    break

    def OnToggleSubhead(self, e):

        """
        If ToggleHighlight is clicked:
            1. if the current line is not highlighted, highlight it,
               and add info to Article instance, or
            2. if the current line is already highlighted, do the opposite.
        """

        #XXX For some weird reason, textBox.GetInsertionPoint is never -1.
        #    When nothing is selected, it's 0. Obviously This is a compromise,
        #    because when the user points the cursor to the begginning of
        #    the file, togglesubhead is still disabled.
        if self.textBox.GetInsertionPoint() == 0:
            return

        lineNo = len(self.textBox.GetRange(0, self.textBox.GetInsertionPoint()).split("\n"))
        if self.articleList.GetSelection() != -1:   #TODO: modulize
            selectedTitle = self.articleList.GetStringSelection()
            for art in self.issue.articleList:
                if art.title == selectedTitle:
                    article = art
                    break

        if lineNo in article.subheadLines:
            #UI action dehighlight the line
            pos = self.textBox.GetInsertionPoint()
            fulltext = self.textBox.GetRange(0, self.textBox.GetLastPosition())
            try:
                leftMargin = fulltext.rindex('\n', 0, pos)
            except ValueError:
                leftMargin = 0
            try:
                rightMargin = fulltext.find('\n', pos)
            except ValueError:
                rightMargin = self.textBox.GetLastPosition()
            self.textBox.SetStyle(leftMargin, rightMargin, wx.TextAttr("black", "white"))

            #Backend action: remove subhead info 
            article.subheadLines.remove(lineNo)

        else: #if lineNo not in article.sbuheadLines
            #UI action: highlight the line
            pos = self.textBox.GetInsertionPoint()
            fulltext = self.textBox.GetRange(0, self.textBox.GetLastPosition())
            try:
                leftMargin = fulltext.rindex('\n', 0, pos)
            except ValueError:
                leftMargin = 0
            try:
                rightMargin = fulltext.find('\n', pos)
            except ValueError:
                rightMargin = self.textBox.GetLastPosition()
            self.textBox.SetStyle(leftMargin, rightMargin, wx.TextAttr("black", "yellow"))
            #Backend action: add subhead info 
            article.subheadLines.append(lineNo)

    def updateInfoBar(self, index):
        if self.issue.articleList == []:
            return

        display1 = 'Issue no.'+str(self.issue.issueNum)+' '+self.issue.grandTitle+\
                  ' Total number of articles:'+str(len(self.issue.articleList))
        self.infoBar1.SetLabel(display1)
        if index == -1:
            return
        selectedTitle = self.articleList.GetString(index)
        for article in self.issue.articleList:
            if article.title == selectedTitle:
                chosenArticle = article
                break
        title = chosenArticle.title
        author = chosenArticle.author
        self.infoBar2.SetLabel('Article title: '+title)
        self.infoBar3.SetLabel('Author: '+author)

    def updateTextBox(self, index):
        if self.articleList.GetSelection() == -1:
            return
        title = self.articleList.GetStringSelection()
        for article in self.issue.articleList:
            if article.title == title:
                text = article.text
                break
        self.textBox.SetValue(text)

        selectedTitle = self.articleList.GetString(index)
        for article in self.issue.articleList:
            if article.title == selectedTitle:
                chosenArticle = article
                break

        for subhead in chosenArticle.subheadLines:
            text = self.textBox.GetValue()
            if subhead == 1:
                leftMargin = 0
                rightMargin = text.find('\n')
            else:
                count = 0
                leftMargin = 0
                while count < subhead-1:
                    leftMargin = text.find('\n', leftMargin+1)
                    count += 1
                rightMargin = text.find('\n', leftMargin+1)
            self.textBox.SetStyle(leftMargin, rightMargin, wx.TextAttr('black', 'yellow'))


    def askInfo(self, prompt, dialogTitle, defaultVal='', multiline=False, noCancel=False):

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

    def printIssue(self, event):
        print self.issue.issueNum
        print self.issue.grandTitle
        print self.issue.ediRemark
        for article in self.issue.articleList:
            print article.title
            print article.text
            print '*'*20


def main():
    currentIssue = Issue()
    app = wx.App()
    HuoziMainFrame(currentIssue, None)
    app.MainLoop()

if __name__ == '__main__':
    main()
