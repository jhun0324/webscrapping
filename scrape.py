import os
import re
import time
import requests
import shutil
import bs4 as bs
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.select import Select
from collections import Counter

# global varibles: chromeOptions, pathToPDF, categories, download_dir


def savefile(html):
	f = open("html.html", "w")
	f.write(html)
	f.close()

def downloadpdf(pdfurl, filename):
	pdfresponse = requests.get(pdfurl)
	file = open(pathToPDF + filename + '.pdf', 'wb')
	file.write(pdfresponse.content)
	if os.path.getsize(file.name) < 20000:
		print("File size seems too small. Download may have failed for ", filename)
		return False
	file.close()
	return True

def process_doi(doi):
	doi_underscored = doi.replace('/', '_')
	chromeOptions = webdriver.ChromeOptions()
	prefs = {"download.default_directory": pathToPDF}
	chromeOptions.add_experimental_option("prefs", prefs)
	browser = webdriver.Chrome(executable_path=os.getcwd() + os.sep + 'chromedriver', chrome_options=chromeOptions)
	browser.get('http://doi.org/' + doi)
	url = browser.current_url
	downloaded = navigate_to_pdf(url, browser, doi_underscored)
	browser.close()
	return downloaded

def navigate_to_pdf(url, browser, doi_underscored):
	domain = urlparse(url)[1]
	domains.append(domain)
	if domain == 'www.sciencedirect.com':
		downloadpdfbutton = browser.find_element_by_partial_link_text("Download")
		downloadpdfbutton.click()
		getpdf = browser.find_element_by_link_text("Article")

		# cannot just grab url from html because Python requests library does not redirect correctly to the PDF
		getpdf.click()
		browser.switch_to.window(browser.window_handles[1])

		# sometimes takes a while to redirect to the actual pdf, so we wait until it does redirect
		while urlparse(browser.current_url)[1] == 'www.sciencedirect.com':
			time.sleep(1)
		pdfurl = browser.current_url
		browser.close()
		browser.switch_to.window(browser.window_handles[0])
		# WE HAVE SCIENCEDIRECT PDFS!!!
		return downloadpdf(pdfurl, doi_underscored)
	elif domain == 'onlinelibrary.wiley.com':
		getpdf = browser.find_element_by_xpath("//li[@class='article-support__item--pdf ']/a")  # find pdf button
		pdfurl = getpdf.get_attribute('href')  # get link from pdf button
		r = requests.get(pdfurl,
						 allow_redirects=True)  # go to this link (not pdf link yet, only links to a redirecting site)
		rsoup = BeautifulSoup(r.content, 'lxml')
		realpdflink = rsoup.find("iframe", {"id": "pdfDocument"})[
			'src']  # from redirected site, fish out the real pdf link
		return downloadpdf(realpdflink, doi_underscored)
		# WE HAVE WILEY ONLINE LIBRARY PDFS!!!
	elif domain == 'rd.springer.com':
		pdfbutton = browser.find_element_by_xpath("//a[@title='Download this article in PDF format']")
		realpdflink = pdfbutton.get_attribute('href')
		return downloadpdf(realpdflink, doi_underscored)
		# WE HAVE SPRINGER PDFS!!!
	elif domain == 'www.mdpi.com':
		pdfbutton = browser.find_element_by_link_text("Full-Text PDF")
		realpdflink = pdfbutton.get_attribute('href')
		return downloadpdf(realpdflink, doi_underscored)
	return False



def isKeywordInArticle(articleKeywords, keywords):
	return True

def hasAuthorKeywords(article):
	if article.find('td', string='DE ') == None:
		return False
	return True

def hasAdditionalKeywords(article):
	if article.find('td', string='ID ') == None:
		return False
	return True

def hasDOI(article):
	if article.find('td', string='DI ') == None:
		return False
	return True

def setup(metaDataDirName = '/abstracts', pdfDirName = '/pdf',
		  removeMetaDataDir = True, removePdfDir = False):

	metaDataDirPath = os.getcwd() + metaDataDirName
	pdfDirPath = os.getcwd() + pdfDirName

	# remove meta data directory and make the same one again
	if not os.path.exists(metaDataDirPath):
		os.makedirs(metaDataDirPath)
	else:
		if removeMetaDataDir:
			shutil.rmtree(metaDataDirPath)
			os.makedirs(metaDataDirPath)

	# remove pdf directory and make the same one again
	if not os.path.exists(pdfDirPath):
		os.makedirs(pdfDirPath)
	else:
		if removePdfDir:
			shutil.rmtree(pdfDirPath)
			os.makedirs(pdfDirPath)

def searchForKeyword(keyword) :
	browser.get(url)

	# go to the advanced search section
	advsearch = browser.find_element_by_xpath('//*[@title="Advanced Search"]')
	advsearch.click()

	# type in search query terms and click search
	searchbox = browser.find_element_by_id('value(input1)')
	allCategories = ' OR '.join(categories)
	query = 'TS=' + '\"' + keyword + '\"' + ' AND WC=(' + allCategories + ')'

	searchbox.send_keys(query)
	searchbutton = browser.find_element_by_class_name('searchButton')
	searchbutton.click()
	resultsbutton = browser.find_element_by_xpath('//*[@title="Click to view the results"]')
	resultsbutton.click()

	# find out how many results are found
	results = browser.find_element_by_id("hitCount.top")
	numResults = int(results.text.replace(",",""))
	numResults = 1012
	return numResults


def downloadMetaDataHtml(numResults):
	for i in range(1, numResults+1, 500):
		# choose 'Save to Other File Formats'
		saveToMenu = browser.find_element_by_id("saveToMenu")
		Select(saveToMenu).select_by_visible_text("Save to Other File Formats")
		if i != 1:
			saveToMenu = browser.find_element_by_id("saveToMenu")
			Select(saveToMenu).select_by_visible_text("Save to EndNote online")
			cancelbutton = browser.find_element_by_xpath('//*[@id="csiovldialog"]/table/tbody/tr/td[1]/table/tbody/tr[4]/td[2]/table/tbody/tr/td[3]/a')
			cancelbutton.click()
			saveToMenu = browser.find_element_by_id("saveToMenu")
			Select(saveToMenu).select_by_visible_text("Save to Other File Formats")

		# fill in the number of records
		numOfRecordRange = browser.find_element_by_id("numberOfRecordsRange")
		numOfRecordRange.click()

		markFrom = browser.find_element_by_id("markFrom")
		markFrom.send_keys(str(i))

		markTo = browser.find_element_by_id("markTo")
		if numResults > i+499:
			markTo.send_keys(str(i+499))
		else:
			markTo.send_keys(numResults)

		# choose 'Full Record' from 'Record Content' dropdown
		fieldsSelection = browser.find_element_by_id("bib_fields")
		Select(fieldsSelection).select_by_visible_text("Full Record     ")

		# choose 'HTML' from 'File Format' dropdown
		saveOptions = browser.find_element_by_id("saveOptions")
		Select(saveOptions).select_by_visible_text("HTML")

		# download the abstracts in the format of html
		sendbutton = browser.find_element_by_xpath('//*[@id="ui-id-7"]/form/div[4]/span/input')
		sendbutton.click()

		# close the window
		closebutton = browser.find_element_by_xpath('//*[@id="ui-id-7"]/form/div[2]/a')
		# closebutton = browser.find_element_by_class_name("quickoutput-cancel-action")
		closebutton.click()


def getMetaDataDataframe(download_dir):
	df = pd.DataFrame(columns = ['DOI', 'title', 'author', 'address', 'downloaded'])
	dataFrameIndex = 1

	for filename in os.listdir(download_dir):
		print(filename)
		if '.html' not in filename:
			continue
		soup = bs.BeautifulSoup(open(os.getcwd() + '/abstracts/' + filename).read(), 'html5lib')
		indicatorList = soup.findAll('table')

		numOfIndicator = len(indicatorList)

		for i in range(numOfIndicator):
			article = indicatorList[i]
			if hasAuthorKeywords(article):
				authorKeywords = re.sub(r'\s+', ' ', article.find('td', string='DE ').next_sibling.text.lower())
				authorKeywords = re.split(r';\s*', authorKeywords)
			else:
				authorKeywords = []
			if hasAdditionalKeywords(article):
				additionalKeywords = re.sub(r'\s+|-', ' ', article.find('td', string='ID ').next_sibling.text.lower())
				additionalKeywords = re.split(r';\s*', additionalKeywords)
			else:
				additionalKeywords = []
			articleKeywords = authorKeywords + additionalKeywords

			if isKeywordInArticle(articleKeywords, keywords) and hasDOI(article):
				doi = article.find('td', string='DI ').next_sibling.text.strip()
				author = re.sub(r'\n+\s+', '; ', article.find('td', string='AU ').next_sibling.text.strip())
				title = re.sub(r'\s+', ' ', article.find('td', string='TI ').next_sibling.text.strip())
				address = None
				downloaded = process_doi(doi)
				df.loc[dataFrameIndex] = [doi, title, author, address, downloaded]
				dataFrameIndex += 1
	return df


keywords = ['sustainable development']
categories = ["Environmental Sciences",
			  "Environmental Studies",
			  "Green & Sustainable Science & Technology"]

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', None)

# path to the directory to download meta data
download_dir = os.getcwd() + '/abstracts'

# path to the directory to download PDFs
pathToPDF = os.getcwd() + os.sep + 'pdf' + os.sep

# change the default directory to download files to
chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory": download_dir}
chromeOptions.add_experimental_option("prefs", prefs)

browser = webdriver.Chrome(executable_path=os.getcwd() + os.sep + 'chromedriver', chrome_options=chromeOptions) # replace with .Firefox(), or with the browser of your choice
browser.implicitly_wait(5) # second
url = "https://www.webofknowledge.com"

domains = []

setup()

for keyword in keywords:
	numResults = searchForKeyword(keyword)
	downloadMetaDataHtml(numResults)
	df = getMetaDataDataframe(download_dir)

print(df)
print(Counter(domains))






