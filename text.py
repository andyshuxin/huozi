# -*- coding: utf-8 -*-

# Suffix explained:
# T == Title
# Q == Question
# H == Helpstring / Hint

txtMainFrame = {
        'AddArticlesT':  "Add Articles",
        'AddArticlesQ':  "URLs to the articles (one each line):",
        'AddArticleT':   "Add Article",
        'AddCategoryT':  "Add Category",
        'AddCategoryQ':  "Name of the category:",
        'MdfTitleT':     "Article Title",
        'MdfCategoryT':  "Category",
        'MdfCategoryQ':  "Name of the category:",
        'PortraitT':     "Select Portrait File for the Author.",
        'SaveIssueT':    "Save issue",
        'ConfirmNewT':   "Confirm creating new issue",
        'ConfirmNewQ':   "All unsaved progress would be lost. Confirm?",
        'DelArticle':    "Delete ",
        'OverwriteHif':  "Overwrite ",
        'configIssueH':  "Configure the issue",
        'getDocH':       "Produce doc file",
        'quitH':         "Quit",
        'AboutH':        "About",
        'issueNoH':       "Issue no.",
        'articleNo':     "Total number of articles: ",
        'ratioH':        "Threshold:",
        'btnAutoRet':    "&Auto Retrieve",
        }

txtIssueConfig = {
        'issueNumT':     "Issue Number",
        'issueNumQ':     "What's the number of issue?",
        'grandTitleT':   "General Title",
        'grandTitleQ':   "What's the general title of the issue?",
        'ediRemarkT':    "Editor's Remarks",
        'ediRemarkQ':    "What are the editor's remarks?",
        }

txtAddOneArticleFrame = {
        'URL':           "Set the URL to the article",
        'MainTextH':     "Preview of the main text(please avoid editing here):",
        'TeaserTextH':   "Digest of the article:",
        }

txtAddMultipleArticleFrame = {}

txtErrorMessage = {
        'graberror':     "Something is wrong grabbing ",
        'graberrorCap':  "Grabber Error",
        'duplicate':     "Already added the article: ",
        'duplicateCap':  "Duplicate article",
        #'emptyContent':  "The webpage has too little textual content.",
        }

txt = {}
for dic in (txtIssueConfig,
            txtMainFrame,
            txtAddOneArticleFrame,
            txtAddMultipleArticleFrame,
            txtErrorMessage,):
    txt.update(dic)
