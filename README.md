# webscrapping
webscrapper for igg project

The program is defaulted to use the search term "sustainable development" under categories Environmental Sciences, Environmental Studies, Green & Sustainable Science & Technology on the [Web of Science](https://webofknowledge.com/) search platform. We will add more capabilities in the future to allow different search terms.

**Things to install**:

BeautifulSoup
```
pip install bs4
```

selenium
```
pip install selenium
```

Chromedriver

Download the [Chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads). In order to use the selenium webdriver, we have to download drivers for the browswer we will use. We chose Chrome for this program. After downloading, **place the Chromedriver module in the same folder as scrape.py**. 


Finally, you may run the file.
```
python scrape.py
```
