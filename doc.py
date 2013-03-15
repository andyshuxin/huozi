#!python
#coding=utf-8

#Copyright (C) 2013 Shu Xin

from urllib import urlopen
from aep import Article, Issue
from aep import grab, parseHtml, cleanText
import codecs

try:
    import win32com.client as win32
except:
    pass

## Constants
FONT = u'宋体'


def createDoc(issue):
    word = win32.gencache.EnsureDispatch('Word.Application')
    doc = word.Documents.Add()
    #doc = word.Documents.Open('C:\\Dropbox\\aep\\template.doc')
    word.Visible = False

    ##### Set up styles #####

    # Normal Text 
    font = doc.Styles(win32.constants.wdStyleNormal).Font
    font.Size = 11
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleNormal).ParagraphFormat
    paraF.LineSpacing = 1.5 * font.Size
    paraF.CharacterUnitFirstLineIndent = 2   # Heading 1
    font = doc.Styles(win32.constants.wdStyleHeading1).Font
    font.Bold = True
    font.Size = 24
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleHeading1).ParagraphFormat
    paraF.Alignment = win32.constants.wdAlignParagraphLeft
    paraF.CharacterUnitFirstLineIndent = 0

    # Heading 2
    font = doc.Styles(win32.constants.wdStyleHeading2).Font
    font.Bold = True
    font.Size = 18
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleHeading2).ParagraphFormat
    paraF.Alignment = win32.constants.wdAlignParagraphCenter
    paraF.CharacterUnitFirstLineIndent = 0

    # Subheads
    font = doc.Styles(win32.constants.wdStyleHeading3).Font
    font.Bold = True
    font.Italic = False
    font.Size = 11
    font.Name = FONT
    paraF = doc.Styles(win32.constants.wdStyleHeading3).ParagraphFormat
    paraF.Alignment = win32.constants.wdAlignParagraphCenter
    paraF.LineSpacing = 2 * font.Size
    paraF.CharacterUnitFirstLineIndent = 0

    # Foot notes
    font = doc.Styles(win32.constants.wdStyleQuote).Font
    font.Bold = True
    font.Size = 10
    font.Name = FONT

    ##### Add contents #####

    ## Add Header
    C = win32.constants.wdHeaderFooterPrimary
    hdr = u'一五一十周刊第' + issue.issueNum + u'期' + \
          u'： ' + issue.grandTitle
    word.ActiveDocument.Sections(1).Headers(C).Range.Text = hdr

    rng = doc.Range(0, 0)

    ## Add Cover page
    rng.InsertAfter(u'【封面圖片】\r\n')
    rng.Collapse( win32.constants.wdCollapseEnd )
    rng.InsertBreak( win32.constants.wdPageBreak )

    ## Add Editor's Remark
    rng.InsertAfter(u'【编者的话】\r\n')
    rng.InsertAfter(issue.ediRemark)
    rng.Collapse( win32.constants.wdCollapseEnd )
    rng.InsertBreak( win32.constants.wdPageBreak )

    ## Add Contents Page
    rng.InsertAfter(u'目录\r\n')
    rng.Collapse( win32.constants.wdCollapseEnd )
    tocPos = rng.End
    rng.InsertBreak( win32.constants.wdPageBreak )

    word.Visible = False
    #rng.Collapse( win32.constants.wdCollapseEnd )
    #articleStart = rng.End

    ## Add articles
    rng.Collapse( win32.constants.wdCollapseEnd )
    category = ''
    for article in issue.articleList:

        # Category
        if article.category != category:
            category = article.category
            rng.InsertAfter(u'【' + category + u'】' + '\r\n')
            rng.Style = win32.constants.wdStyleHeading1
            rng.Collapse( win32.constants.wdCollapseEnd )

        # Title
        rng.InsertAfter(article.author + u'：' + article.title + '\r\n')
        rng.Style = win32.constants.wdStyleHeading2
        rng.Collapse( win32.constants.wdCollapseEnd )

        # Main text
        for line in article.text.split('\n'):
            rng.Collapse( win32.constants.wdCollapseEnd )
            rng.InsertAfter(line+'\r\n')
            if line in article.subheadLines:
                rng.Style = win32.constants.wdStyleHeading3

        rng.Collapse( win32.constants.wdCollapseEnd )
        rng.InsertBreak( win32.constants.wdPageBreak )

    ## About infomation
    ## TODO

    #Add TOC
    doc.TablesOfContents.Add(doc.Range(tocPos, tocPos), True, 1, 2)
    #doc.TablesOfContents(1).Update()

    #Unify font, just in case
    rng = doc.Range()
    rng.Font.Name = FONT

    #doc.Close(False)
    #word.Application.Quit()

def _test():
    issue = Issue()
    issue.issueNum = '666'
    issue.grandTitle = u'测试刊'

    article1 = Article()
    url = 'http://my1510.cn/article.php?id=94381'
    html = grab(url)
    parsed = parseHtml(html)
    article1.text = cleanText(parsed[0])
    article1.title = parsed[1]['title']
    article1.author = parsed[1]['author']
    article1.subheadLines = parsed[1]['sub']

    #print article1.subheadLines

    issue.addArticle(article1)
    createDoc(issue)

if __name__ == '__main__':
    _test()
