from __future__ import print_function
import os
import re
import time
import yaml
import spacy
import shutil
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import urlparse
from collections import Counter, defaultdict
from selenium.webdriver.support.select import Select

# dependencies: shutil, pandas, bs4, selenium, lxml
# global variables: keywords, categories, givenKeywords, pathToMetaData, pathToPDF, url, domains


keywords = ['sustainable development']
categories = ["Environmental Sciences", "Environmental Studies", "Green & Sustainable Science & Technology"]
givenKeywords = []

# change the options of displaying pandas dataframe
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.width', None)

# path to the directory to download meta data
pathToMetaData = os.getcwd() + os.sep + 'abstracts' + os.sep

# path to the directory to download PDFs
pathToPDF = os.getcwd() + os.sep + 'pdf' + os.sep

# path to the previous index
pathToIndex = os.getcwd() + os.sep + 'index.p'


url = "https://www.webofknowledge.com"
domains = []

# path to countries.yml (list of the synonyms of each country)
pathToCountries = os.getcwd() + os.sep + 'countries.yml'

# path to metadata.tsv
pathToMetaDataTSV = os.getcwd() + os.sep + 'metadata.tsv'

if os.path.isfile(pathToMetaDataTSV):
	df = pd.read_csv(pathToMetaDataTSV, sep='\t', header=0, names=['DOI', 'title', 'author', 'downloaded', 'address', 'author countries'])
	print(df)
else:
	df = pd.DataFrame(columns=['DOI', 'title', 'author', 'downloaded', 'address', 'author countries'])

# initiate spacy nlp
nlp = spacy.load('en', parser=False)

# load countries.yml
with open(pathToCountries, "r") as f:
	countries = yaml.load(f)


def setup(removeMetaDataDir=True, removePdfDir=False):
	"""
	:param removeMetaDataDir: If it is True, existing directory to download meta data will be removed and created again.
							If it is False, meta data will be downloaded to existing directory.
	:param removePdfDir: If it is True, existing directory to download PDFs will be removed and created again.
						If it is False, PDFs will be downloaded to existing directory.

	:return: None
	"""

	# remove meta data directory and make the same one again
	if not os.path.exists(pathToMetaData):
		os.makedirs(pathToMetaData)
	else:
		if removeMetaDataDir:
			shutil.rmtree(pathToMetaData)
			os.makedirs(pathToMetaData)

	# remove pdf directory and make the same one again
	if not os.path.exists(pathToPDF):
		os.makedirs(pathToPDF)
	else:
		if removePdfDir:
			shutil.rmtree(pathToPDF)
			os.makedirs(pathToPDF)


def searchForKeyword(browser, keyword):
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
	# numResults = int(results.text.replace(",", ""))

	# manually specify the number of meta data you want to download
	numResults = 2000
	return numResults


def downloadMetaDataHtml(browser, numResults):
	for i in range(len(df.index)+1001, numResults+1, 500):
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


def getMetaDataDataframe(chromeOptions):
	dataFrameIndex = len(df.index) + 1

	for filename in os.listdir(pathToMetaData):
		print(filename)
		if '.html' not in filename:
			continue
		soup = BeautifulSoup(open(os.getcwd() + '/abstracts/' + filename).read(), 'html5lib')
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

			if isArticleKeywordsInGivenKeywords(articleKeywords) and hasDOI(article):
				doi = article.find('td', string='DI ').next_sibling.text.strip()
				if doi in df['DOI']:
					continue
				try:
					author = re.sub(r'\n+\s+', '; ', article.find('td', string='AU ').next_sibling.text.strip())
					title = re.sub(r'\s+', ' ', article.find('td', string='TI ').next_sibling.text.strip())
					downloaded = process_doi(doi, chromeOptions)
					addresses = list(article.find('td', string='C1 ').next_sibling.stripped_strings)
					addresses = [re.sub(r'\.$', '', re.sub(r'\s+', ' ', address)) for address in addresses]
					address = '; '.join(addresses)
					authorCountries = extractAuthorCountries(addresses)
					df.loc[dataFrameIndex] = [doi, title, author, downloaded, address, authorCountries]
					dataFrameIndex += 1
					print(dataFrameIndex)
				except AttributeError:
					continue


def isArticleKeywordsInGivenKeywords(articleKeywords):
	return True


def hasAuthorKeywords(article):
	if article.find('td', string='DE ') is None:
		return False
	return True


def hasAdditionalKeywords(article):
	if article.find('td', string='ID ') is None:
		return False
	return True


def hasDOI(article):
	if article.find('td', string='DI ') is None:
		return False
	return True


def extractAuthorCountries(addresses):
	country_dict = defaultdict(lambda: 0, {})

	for address in addresses:
		switch = False
		address = re.sub(r'\bUSA\b', 'US', address)
		parsedText = nlp(address)
		gpe = [ent.text for ent in parsedText.ents if ent.label_ == 'GPE' or ent.label_ == 'ORG']

		for loc in gpe:
			for country in countries.keys():
				for syn in countries[country]:
					if re.search(syn, loc, re.U & re.I):
						country_dict[country] += 1
						switch = True
				if switch:
					break
			if switch:
				break

	return ', '.join('{}: {}'.format(country, count) for country, count in sorted(country_dict.items()))


def savefile(html):
	f = open("html.html", "w")
	f.write(html)
	f.close()


def downloadpdf(pdfurl, filename):
	try:
		pdfresponse = requests.get(pdfurl)
	except:
		print("Connection refused by the server..")
		time.sleep(5)
		pdfresponse = requests.get(pdfurl)
		print("Start downloading again...")

	file = open(pathToPDF + filename + '.pdf', 'wb')
	file.write(pdfresponse.content)
	if os.path.getsize(file.name) < 20000:
		os.remove(pathToPDF + filename + '.pdf')
		file.close()
		return False
	file.close()
	return True


def process_doi(doi, chromeOptions):
	"""
	:param doi: DOI
	:param chromeOptions: chrome option for the default download directory
	:return: Boolean
			True if pdf file is successfully downloaded.
			False if downloading failed
	"""
	# we are using the DOI to name the pdf files, however DOIs contain forward slashes which interfere with
	# path notation, so we replace slashes with underscores for the file names
	doi_underscored = doi.replace('/', '_')
	if os.path.exists(pathToPDF + doi_underscored + '.pdf'):
		return True
	browser = webdriver.Chrome(executable_path=os.getcwd() + os.sep + 'chromedriver', chrome_options=chromeOptions)
	try:
		browser.get('http://doi.org/' + doi)
	except Exception as e:
		print("Error when accessing doi url: ", e)
		browser.quit()
		return False
	currentUrl = browser.current_url
	downloaded = navigate_to_pdf(currentUrl, browser, doi_underscored)
	browser.quit()
	return downloaded


def navigate_to_pdf(currentUrl, browser, doi_underscored):
	domain = urlparse(currentUrl)[1]
	domains.append(domain)
	try:
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
			# WE HAVE SCIENCEDIRECT PDFs!!!
			return downloadpdf(pdfurl, doi_underscored)
		elif domain == 'onlinelibrary.wiley.com':
			getpdf = browser.find_element_by_xpath("//li[@class='article-support__item--pdf ']/a")  # find pdf button
			pdfurl = getpdf.get_attribute('href')  # get link from pdf button
			# go to this link (not pdf link yet, only links to a redirecting site)
			r = requests.get(pdfurl, allow_redirects=True)
			rsoup = BeautifulSoup(r.content, 'lxml')
			realpdflink = rsoup.find("iframe", {"id": "pdfDocument"})[
				'src']  # from redirected site, fish out the real pdf link
			return downloadpdf(realpdflink, doi_underscored)
			# WE HAVE WILEY ONLINE LIBRARY PDFs!!!
		elif domain == 'link.springer.com':
			pdfbutton = browser.find_element_by_xpath("//a[@title='Download this article in PDF format']")
			realpdflink = pdfbutton.get_attribute('href')
			return downloadpdf(realpdflink, doi_underscored)
			# WE HAVE SPRINGER PDFs!!!
		elif domain == 'www.mdpi.com':
			pdfbutton = browser.find_element_by_link_text("Full-Text PDF")
			realpdflink = pdfbutton.get_attribute('href')
			return downloadpdf(realpdflink, doi_underscored)
		return False
	except Exception as e:
		print('Errored on ', currentUrl, '!! The error is as follows: ', e)
		return False



def main():
	# change the default download directory to meta data directory
	chromeOptions = webdriver.ChromeOptions()
	prefs = {"download.default_directory": pathToMetaData}
	chromeOptions.add_experimental_option("prefs", prefs)

	# replace with .Firefox(), or with the browser of your choice
	browser = webdriver.Chrome(executable_path=os.getcwd() + os.sep + 'chromedriver', chrome_options=chromeOptions)
	browser.implicitly_wait(5)  # second

	setup()

	for keyword in keywords:
		numResults = searchForKeyword(browser, keyword)
		downloadMetaDataHtml(browser, numResults)

	browser.close()

	if os.path.isfile(pathToMetaData + 'savedrecs.html'):
		os.rename(pathToMetaData + 'savedrecs.html', pathToMetaData + 'savedrecs ' + '(0).html')

	# change the default download directory to PDF directory
	chromeOptions = webdriver.ChromeOptions()
	prefs = {"download.default_directory": pathToPDF}
	chromeOptions.add_experimental_option("prefs", prefs)

	getMetaDataDataframe(chromeOptions)
	df.to_csv(pathToMetaDataTSV, sep="\t")

	print(df)
	print(Counter(domains))


if __name__ == '__main__':
	try:
		main()
	except:
		df.to_csv(pathToMetaDataTSV, sep="\t")

		print(df)
		print('Interrupted: ' + str(len(df.index)) + ' records')




