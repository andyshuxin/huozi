#!python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Shu Xin

# Tool Simple, a simplistic DTP GUI, frontend of AEP and The Bride.

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
#   Layout designed by Pan Wenyi, Co-China Forum.
#   Images and text by Co-China Forum.
#   Copyrighted and not distributed under GPL.

__version__ = 'H'
__author__ = "Andy Shu Xin (andy@shux.in)"
__copyright__ = "(C) 2013 Shu Xin. GNU GPL 3."
__language__ = "English"

import os
import sys
import wx
from aep import (Article, Issue,
                 urlClean, cleanText,
                 BRA_L, BRA_R,)
from datetime import date, datetime, timedelta
if __language__ == "English":
    from text_en import txt
    from text_en import weekdays
import bride

##### Constants #####

try:
    with open('DEBUG'):
        DEBUG = True
except IOError:
    DEBUG = False

#####  UI  #####

MAGIC_HEIGHT = 90.0   # used in AddArticlesFrame, for portrait display

##### Window of Adding one Article #####

class BaseFrame(wx.Frame):

    def __init__(self, parent, title='', size=(800, 600), *args, **kwargs):
        wx.Frame.__init__(self, parent=parent, *args, **kwargs)
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))
        self.SetTitle(title)
        self.SetSize(size)
        self.Centre()

class SetArticleFrame(wx.Frame):

    """ Add a new article with greater control over details than batch
        downloading. Also used for editing an existing article """

    def __init__(self, articleArgv=None, *args, **kwargs):
        super(SetArticleFrame, self).__init__(*args, **kwargs)
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))

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
            wildcard="Images|*.jpg;*.jpeg;*.gif;*.png;*.bmp",
            style=wx.FD_OPEN|wx.FD_PREVIEW)
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

        except ValueError as err:
            dlg = wx.MessageDialog(self.panel,
                                   str(err),
                                   'Problem occurred',
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
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))
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

class ConfigIssueFrame(BaseFrame):

    def __init__(self, parent, currentIssue):
        self.targetIssue = currentIssue
        super(ConfigIssueFrame, self).__init__(parent=parent,
                                               title=txt['ConfigIssueT'],
                                               size=(450, 600))
        self.drawUI()
        self.Show(True)

    def askPortraitPath(self, *args):   #TODO: Combine with duplicates
        dlgPortrait = wx.FileDialog(None, message=txt['PortraitT'],
            wildcard="Images|*.jpg;*.jpeg;*.gif;*.png;*.bmp",
            style=wx.FD_OPEN|wx.FD_PREVIEW)
        if dlgPortrait.ShowModal() == wx.ID_OK:
            portraitPath = dlgPortrait.GetPath()
            dlgPortrait.Destroy()
        else:
            portraitPath = None
        return portraitPath

    def _getPublishDate(self):
        """ Return (year, month, day) of the coming Friday.
            If today is Friday, return date of today.  """
        today = date.today()
        for offset in range(7):
            pubDay = today + timedelta(days=offset)
            if pubDay.weekday() == 4:  #Friday
                break
        return (str(i) for i in pubDay.timetuple()[:3])

    def drawUI(self):
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.vBox = wx.BoxSizer(wx.VERTICAL)

        # Grand title block
        self.hintGrandTitle = wx.StaticText(self.panel, wx.ID_ANY,
                              txt['hintGrandTitle'],
                              style=wx.ALIGN_LEFT)
        self.textGrandTitle = wx.TextCtrl(self.panel,
                                          value=self.targetIssue.grandTitle)
        self.vBox.Add(self.hintGrandTitle, 0,
                      flag=wx.EXPAND|wx.LEFT|wx.TOP|wx.RIGHT, border=10)
        self.vBox.Add(self.textGrandTitle, 0,
                      flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,
                      border=10)

        # Publish date block
        self.hintPublishDate = wx.StaticText(self.panel, wx.ID_ANY,
                                             txt['hintPublishDate'])
        self.vBox.Add(self.hintPublishDate, 0,
                      flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,
                      border=10)
        year, month, day = self.targetIssue.publishDate
        if year == '' and month == '' and day == '':
            year, month, day = self._getPublishDate()
        self.textYear = wx.TextCtrl(self.panel, value=year,
                                    size=(50,20))
        self.textMonth = wx.TextCtrl(self.panel, value=month,
                                     size=(50,20))
        self.textDay = wx.TextCtrl(self.panel, value=day,
                                   size=(50,20))
        self.hintYear = wx.StaticText(self.panel, wx.ID_ANY,
                                      ' '*5 + txt['hintYear'],)
        self.hintMonth = wx.StaticText(self.panel, wx.ID_ANY,
                                       txt['hintMonth'],)
        self.hintDay = wx.StaticText(self.panel, wx.ID_ANY,
                                     txt['hintDay'],)
        self.hintWeekday = wx.StaticText(self.panel, wx.ID_ANY,
                                         '',)
        self.onDateChange(None)
        self.hBoxDate = wx.BoxSizer(wx.HORIZONTAL)
        for ctrl in (self.hintYear, self.textYear,
                     self.hintMonth, self.textMonth,
                     self.hintDay, self.textDay,):
            self.hBoxDate.Add(ctrl, 0, flag=wx.LEFT, border=5)
        self.hBoxDate.Add(self.hintWeekday, 1,
                          flag=wx.EXPAND|wx.LEFT, border=5)

        for text in (self.textYear, self.textMonth, self.textDay):
            text.Bind(wx.EVT_TEXT, self.onDateChange)
        self.vBox.Add(self.hBoxDate, 0,
                      flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,
                      border=10)

        # Issue number block
        self.hBoxIssueNum = wx.BoxSizer(wx.HORIZONTAL)
        self.hintIssueNum = wx.StaticText(self.panel, wx.ID_ANY,
                                          txt['hintIssueNum'],)
        self.textIssueNum = wx.TextCtrl(self.panel,
                                        value=self.targetIssue.issueNum,
                                        size=(80, 25))
        self.btnGuessIssueNum = wx.Button(self.panel, -1,
                                          txt['btnGuessIssueNum'],
                                          size=(80, 25))
        self.hBoxIssueNum.Add(self.hintIssueNum)
        self.hBoxIssueNum.Add(self.textIssueNum, 0,
                              flag=wx.LEFT, border=5)
        self.hBoxIssueNum.Add(self.btnGuessIssueNum, 0,
                              flag=wx.LEFT, border=5)
        self.vBox.Add(self.hBoxIssueNum, 0,
                      flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT|wx.BOTTOM,
                      border=10)

        # Editor's remark block
        self.hintEdiRemark = wx.StaticText(self.panel, wx.ID_ANY,
                                           txt['hintEdiRemark'])
        self.textEdiRemark = wx.TextCtrl(self.panel, wx.ID_ANY,
                                         value=self.targetIssue.ediRemark,
                                         style=wx.TE_MULTILINE)
        self.vBox.Add(self.hintEdiRemark, 0,
                      flag=wx.EXPAND|wx.LEFT|wx.RIGHT,
                      border=10)
        self.vBox.Add(self.textEdiRemark, 1,
                      flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,
                      border=10)
        # Cover Image
        self.hintPath = wx.StaticText(self.panel, wx.ID_ANY,
                                      txt['hintCoverImgPath'],
                                      wx.DefaultPosition, wx.DefaultSize,
                                      style=wx.ALIGN_LEFT)
        imgFilename = os.path.split(self.targetIssue.coverImagePath)[1]
        self.textImgPath = wx.StaticText(self.panel, wx.ID_ANY,
                                         imgFilename,
                                         wx.DefaultPosition, wx.DefaultSize,
                                         style=wx.ALIGN_LEFT)
        self.btnSetCoverImage = wx.Button(self.panel, label='&Set Cover')
        self.btnClearCoverImage = wx.Button(self.panel, label='&Clear Cover')
        self.hBoxCoverImage = wx.BoxSizer(wx.HORIZONTAL)
        self.hBoxCoverImage.Add(self.hintPath, 0,
                      flag=wx.EXPAND|wx.LEFT|wx.BOTTOM,
                      border=10)
        self.hBoxCoverImage.Add(self.textImgPath, 1,
                      flag=wx.EXPAND|wx.LEFT|wx.BOTTOM,
                      border=10)
        self.hBoxCoverImage.Add(self.btnSetCoverImage, 0,
                      flag=wx.EXPAND|wx.BOTTOM,
                      border=10)
        self.hBoxCoverImage.Add(self.btnClearCoverImage, 0,
                      flag=wx.EXPAND|wx.RIGHT|wx.BOTTOM,
                      border=10)
        self.vBox.Add(self.hBoxCoverImage, 0, flag=wx.EXPAND)

        self.btnSetCoverImage.Bind(wx.EVT_BUTTON, self.onChangeCoverImage)
        self.btnClearCoverImage.Bind(wx.EVT_BUTTON, self.onClearCoverImage)

        # OK and Cancel buttons
        self.hBoxBtns = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOK = wx.Button(self.panel, label='&OK!')
        self.btnCancel = wx.Button(self.panel, label='&Cancel')
        self.hBoxBtns.Add(self.btnOK, 0)
        self.hBoxBtns.Add(self.btnCancel, 0,
                          flag=wx.LEFT, border=5)
        self.btnOK.Bind(wx.EVT_BUTTON, self.onOK)
        self.btnCancel.Bind(wx.EVT_BUTTON, self.onCancel)
        self.vBox.Add(self.hBoxBtns, 0,
                      flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,
                      border=10)

        self.panel.SetSizerAndFit(self.vBox)
        self.Layout()

    def onOK(self, event):
        self.targetIssue.grandTitle = self.textGrandTitle.GetValue()
        self.targetIssue.issueNum = self.textIssueNum.GetValue()
        self.targetIssue.ediRemark = self.textEdiRemark.GetValue()
        year = self.textYear.GetValue()
        month = self.textMonth.GetValue()
        day = self.textDay.GetValue()
        self.targetIssue.publishDate = (year, month, day)
        self.GetParent().Enable()
        self.GetParent().updateInfoBar(-1)
        self.Destroy()

    def onCancel(self, event):
        self.GetParent().Enable()
        self.Destroy()

    def onDateChange(self, event):
        try:
            year = int(self.textYear.GetValue())
            if year < 2000:
                raise ValueError
            month = int(self.textMonth.GetValue())
            day = int(self.textDay.GetValue())
            pubDay = date(year, month, day)
        except ValueError:
            self.hintWeekday.SetLabel('Date invalid!')
        else:
            weekday = weekdays[pubDay.weekday()]
            self.hintWeekday.SetLabel(weekday)

    def onChangeCoverImage(self, e):
        path = self.askPortraitPath(self)   #TODO: Combine with duplicates
        if path:
            self.targetIssue.coverImagePath = path
            self.textImgPath.SetLabel(os.path.split(path)[1])
        self.Raise()

    def onClearCoverImage(self, e):
        dlgYesNo = wx.MessageDialog(None,
                                    txt['ClearCover'],
                                    style=wx.YES|wx.NO)
        if dlgYesNo.ShowModal() == wx.ID_YES:
            self.targetIssue.coverImagePath = ''
            self.textImgPath.SetLabel('')

class TutorialFrame(wx.Frame):
    pass


class MainFrame(wx.Frame):

    """ Main interactive window """

    def __init__(self, currentIssue, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)
        self.issue = currentIssue
        self.SetIcon(wx.Icon('img/icon.ico', wx.BITMAP_TYPE_ICO))
        self.drawUI()

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
            self.btnExport.Enable()
            self.btnConfigIssue.Enable()

        self.Layout()
        self.SetSize((800, 600))
        self.basicTitle = u'Tool Simple'
        self.SetTitle(self.basicTitle)
        self.Centre()
        self.Show(True)

        self.currentSavePath = ''

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

        self.btnExport = self.regToolbarBtn('img/getdoc.png',
                                            'img/getdoc-d.png')

        self.btnPublish = self.regToolbarBtn('img/publish.png',
                                             'img/publish-d.png')

        self.toolbarBox.AddSpacer(10)

        self.btnSettings = self.regToolbarBtn('img/settings.png',
                                              'img/settings-d.png')

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
        self.btnExport.Bind(wx.EVT_BUTTON, self.onExport)
        self.btnSettings.Bind(wx.EVT_BUTTON, self.onSettings)
        self.btnTutorial.Bind(wx.EVT_BUTTON, self.onTutorial)
        self.btnPublish.Bind(wx.EVT_BUTTON, self.onPublish)
        self.btnAbout.Bind(wx.EVT_BUTTON, self.onAbout)
        self.btnQuit.Bind(wx.EVT_BUTTON, self.onQuit)

        for btn in (self.btnSaveIssue, self.btnSaveasIssue, self.btnPublish,
                    self.btnExport, self.btnConfigIssue):
            btn.Disable()

        # Not implemented
        for btn in (self.btnSettings, self.btnTutorial,
                    self.btnAbout):
            btn.Disable()

    def drawInfoBars(self):
        # TODO: better formatting and add direct editability
        self.infobarBox = wx.BoxSizer(wx.VERTICAL)
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
                                style=wx.ALIGN_LEFT|wx.TE_WORDWRAP)

        self.infobarBox.Add(self.infoBar1, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        self.infobarBox.Add(self.infoBar2, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        self.infobarBox.Add(self.infoBar3, 0,
                       flag=wx.TOP|wx.LEFT|wx.EXPAND, border=5)
        self.infobarBox.Add(self.infoBar4, 0,
                       flag=wx.TOP|wx.LEFT|wx.BOTTOM|wx.EXPAND, border=5)

        self.infoBar1.Bind(wx.EVT_LEFT_DOWN, self.onConfigIssue)
        self.infoBar2.Bind(wx.EVT_LEFT_DOWN, self.onModifyItemInfo)
        self.infoBar3.Bind(wx.EVT_LEFT_DOWN, self.onModifyItemInfo)
        self.infoBar4.Bind(wx.EVT_LEFT_DOWN, self.onModifyItemInfo)

        if sys.platform != 'darwin':
            boldFont = wx.Font(11, wx.NORMAL, wx.NORMAL, wx.BOLD)
            self.infoBar1.SetFont(boldFont)

        self.panelInfoBar.SetSizerAndFit(self.infobarBox)

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
        self.textBox = wx.TextCtrl(self.panel, value='',
                           style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_RICH2)
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

        self.btnSave = self.regBmBtn('img/saveedit.png',
                                     'img/saveedit-d.png')

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

## ------------- Toolbar methods -------------------- ##

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
        dlgYesNo = wx.MessageDialog(None,
                                    txt['ConfirmOpenQ'],
                                    style=wx.YES|wx.NO)
        if dlgYesNo.ShowModal() != wx.ID_YES:
            return

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

        self.issue.fromXML(content)
        self.updateInfoBar(-1)
        self.clearTextBox()
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
            self.btnExport.Enable()

        self.currentSavePath = openPath

    def onSaveIssue(self, e):
        if not self.currentSavePath:
            self.onSaveAsIssue(e)
            if self.currentSavePath:
                self.btnSaveasIssue.Enable()
            return

        f = open(self.currentSavePath, 'w')
        content = self.issue.toXML()
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
        content = self.issue.toXML()
        f.write(content)
        f.close()

    def onConfigIssue(self, e):

        """
        Set the basic information of the current issue.
        """


        self.Disable()
        ConfigIssueFrame(self, self.issue)

        self.btnAddArticle.Enable(True)
        self.btnAddArticles.Enable(True)
        self.btnAddCategory.Enable(True)
        if os.name == 'nt':
            # TODO: Registry checking for Word
            self.btnExport.Enable()

        self.updateInfoBar(-1)
        self.SetTitle(self.basicTitle + ': ' +
                      'Issue ' + self.issue.issueNum +
                      self.issue.grandTitle)

    def onExport(self, e):
        path = self.issue.saveToDoc()
        bride.openDoc(path)

    def onPublish(self, e):
        pass

    def onSettings(self, e):
        pass

    def onTutorial(self, e):
        self.Tutorial(e)

    def showTutorial(self, e):
        TutorialFrame()

    def onAbout(self, e):
        pass

    def onQuit(self, e):
        dlgYesNo = wx.MessageDialog(None,
                                    txt['ConfirmQuitQ'],
                                    style=wx.YES|wx.NO)
        if dlgYesNo.ShowModal() == wx.ID_YES:
            self.Close()


## ------------- ArticleList tool methods -------------------- ##

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
        catInBracket = BRA_L + cat + BRA_R
        pos = self.articleList.GetSelection()
        if pos == -1:
            self.articleList.Insert(catInBracket, 0)
        else:
            self.articleList.Insert(catInBracket, pos)
        self.updateCatInfo()

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
            self.articleList.SetString(index, BRA_L+cat+BRA_R)
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
        self.clearTextBox()
        self.updateCatInfo()

## ------------- Article tool methods -------------------- ##

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
        #if leftMargin == 0 or rightMargin == len(text):
            #return
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
        if len(authorBio) <= 33:
            self.infoBar4.SetLabel("Author's bio: " + authorBio)
        else:
            self.infoBar4.SetLabel("Author's bio: " + authorBio[:33] + u' ……')

    def updateTextBox(self):

        if self.articleList.GetSelection() == -1:
            return
        elif _isCat(self.articleList.GetStringSelection()):
            self.clearTextBox()
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
            if leftMargin == -1:
                continue
            def isStandalone(leftMargin, rightMargin, text):
                if leftMargin > 0 and rightMargin < len(text):
                    return (text[leftMargin-1] == '\n' and
                            text[rightMargin] == '\n')
                elif leftMargin == 0 and rightMargin < len(text):
                    return text[rightMargin] == '\n'
                elif leftMargin > 0 and rightMargin == len(text):
                    return text[leftMargin-1] == '\n'
                elif leftMargin == 0 and rightMargin == len(text):
                    return True
            while not isStandalone(leftMargin, rightMargin, text):
                leftMargin = text.find(subhead, rightMargin)
                rightMargin = leftMargin + len(subhead)
            # End duct tape
            self.textBox.SetStyle(leftMargin, rightMargin,
                                  wx.TextAttr('black', 'yellow'))

    def clearTextBox(self, *args):
        self.textBox.SetValue('')

    def updateCatInfo(self):
        cat = ''
        for i in range(0, self.articleList.GetCount()):
            item = self.articleList.GetString(i)
            if _isCat(item):
                cat = item[1:-1]
            else:
                for article in self.issue:
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
        """ Return the article in self.issue that matches the selected string
            in listbox."""
        selectedTitle = self.articleList.GetStringSelection()
        for article in self.issue:
            if article.title == selectedTitle:
                return article
        return None

    def printIssue(self, e=None):
        print 'coverImagePath:', self.issue.coverImagePath
        #print self.issue.toXML()

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
