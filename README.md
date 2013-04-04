Huozi
=======
Huozi is a package of automated document manipulators, tailored for efficient production of electronic digest-type weekly magazines which requires little fancy. Huozi grew out of my experiences of editing and producing of 1510 Weekly, which is why for the moment, Huozi is customized for 1510 Weekly production, and Chinese-oriented.
The package is under development and far from decent usability.
In Chinese, Huozi means 'movable type', 'lively words', or 'animated words'.

## Tool Simple
Tool simple is the GUI. 

## AEP
AEP, or Automated E-Digest Preprocessor, includes these tools:
+ Issue Class and Article Class, corresponding to an issue of a magazine and an article in it;
+ Text cleaner that removes redundant spaces, blank lines, and unify punctuation marks;
+ Html analyser that extract its main text and guess title, author, and where the sub-headlines lies; and
+ Grabber that handles .

## The Bride
The Bride is the Microsoft Word document formatter.
The naming has nothing to do with Kill Bill.

## Requirments
+ Python 2.7 (not tested on other versions)
+ lxml, BeautifulSoup 3
+ PIL
For auto-detection of charset:
+ chardet
For doc export:
+ MS Windows XP or 7; Vista should probably work but not tested.
+ MS Word 2007 or 2010; Version 2013 and 2003 could work as well.
+ win32com

## Software Structure
For a closer look at the structure of the package, see [package structure](https://docs.google.com/drawings/d/1a7UuFqxJZ2w612ZCunHIQBt-jXBpSWyJm_HNQ4I4vuE/edit?usp=sharing).


## Author
My name is Andy Shu. I am a Hong Kong-based journalist and volunteer with a non-profit organization  [Co-China forum](https://cochina.org). I picked up programming in January 2013. So please expect nothing better than chaotic design, horrible mistakes, and spaghetti code style.
