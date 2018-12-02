#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup as BSoup
import lxml

BASE_URL = "https://pixabay.com/en/photos/"

def make_urls( ):
	r = requests.get(BASE_URL)
	soup = BSoup(r.text, "lxml")
	number_of_pages = soup.find_all("form", class_="add_search_params")[0].text.strip( ).strip("/").strip( )
	return [BASE_URL+"?&pagi="+str(i) for i in range(int(number_of_pages))]

def main( ):
	urls = make_urls( )
	print(urls)
	for url in ["https://pixabay.com/en/photos/"]:
		y = requests.get(url)
		soup = BSoup(y.text, "lxml")
		a = soup.find_all("div", class_="credits")
		images = a[0].findChildren("a")
		print(len(images))
		return [image["href"] for image in images]

if __name__=="__main__":
	print(main( ))