#!/usr/bin/env python3

import os
import csv
import lxml
import socket
import requests
import pycountry
from time import sleep
from requests import RequestException
from multiprocessing.dummy import Pool
from bs4 import BeautifulSoup as BSoup

#The API is limited to 500 resutls, so I can't use that


BASE_URL = "https://pixabay.com"
username = "test_account_1873"
MAIN_URL = BASE_URL+"/en/photos?image_type=photo"
DEFAULT_TIFF_DIRECTORY = "tiffs"
DEFAULT_PREVIEW_DIRECTORY = "jpgs"
DEFAULT_CSV_NAME = "image_csv.csv"
TIME_BETWEEN_FAILED_ATTEMPTS = 5

"""
Because 
"""
def make_countries( ):

	return [country.name for country in pycountry.countries]

"""
a funciton to download an image. It will then save the image to a specified directory.
"""
def download_file(url, name, directory=DEFAULT_TIFF_DIRECTORY, chunk_size=1024, ext="tiff"):
    print("[*] Downloading file {0}".format(url))
    r = make_request(url, stream=True)
    with open("{0}/{1}.{2}".format(directory, name, ext), "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                f.flush( )

"""
I just use this so that if anything fails, the program won't completely break. For example, if a link is broken, 
then the program won't stop working. 
Because this program is multithreaded, this waiting for 5 seconds won't stop other downloads from going through
"""
def make_request(url, failed_until_giveup=20, stream=False):
    for attempt in range(failed_until_giveup):
        try:
            r = requests.get(url, stream=stream)
            return r
        except RequestException:
            print("[*] Request failed, retrying in {0} seconds".format(TIME_BETWEEN_FAILED_ATTEMPTS))
            print("Giving up in {0} attempts".format(failed_until_giveup-attempt))
            sleep(TIME_BETWEEN_FAILED_ATTEMPTS)

"""
This gets the total amount of pages that are in the websites /en/photos, and will return a list of all possible
URLS that I can get images from.
"""
def make_urls( ):
    r = make_request(MAIN_URL)
    soup = BSoup(r.text, "lxml")
    number_of_pages = soup.find_all("form", class_="add_search_params")[0].text.strip( ).strip("/").strip( ) #This gets the total numebr of pages
    
    return [BASE_URL+"/en/photos"+"?&pagi="+str(i) for i in range(int(number_of_pages))]

"""
This block of code takes the image URL, and scraps all metadata from it. It then writes this information to a
CSV. In the CSV.write function, it will also download the full size image, as well as a preview of the image, to
a folder that the user has chosen.
"""
def handle_image(url):
    #This gets the image url, and gets all metadata 
    countries 		 =   make_countries( )
    r                =   make_request(url)
    soup             =   BSoup(r.text, "lxml")
    cdn_640      	 =   soup.find_all("input", type="radio")[0]["value"]
    cdn_1280         =   cdn_640.replace("_640.jpg", "_1280.jpg")
    preview 		 =   cdn_640.replace("_640.jpg", "__340.jpg")
    title            =   soup.title.string.split("·")[0].strip( )
    author           =   soup.find_all("img", class_="hover_opacity")[0]["alt"]
    details          =   soup.find_all("table", id="details")
    year_created     =   details[0].findChildren("td")[2].string.split( )[2]
    tags             =   soup.find_all("h1")
    keywords         =   " ".join([tag.string for tag in tags[0].findChildren("a") if tag.string is not None])
    try:
        category     =   details[0].findChildren("a")[0].string #because the category in the details will always be a link,
    except IndexError:
    	#Some images will not have a category, so if they don't I will just put an empty string. 
    	category         =   ""
    keywordslist 	 =   keywords.split( )
    country 		 =   ''.join([word for word in keywordslist if word in countries])


    #List goes as follows:
    #image_url, full_size_direct_download, jpg_download_link, title, author,
    #original_creation_year, original_location, keywords, category, copyright_status.
    list1 = [url, cdn_1280, preview, title, author, year_created, country, keywords, category, "CC0"]
    #Since all images are CC0 copyrighted, I can just hardcode that in
    CSV.write(list1)
    return list1

"""
This is used to prompt the user to chose where they want to save the images and the CSV file. 
"""
def handle_directories( ):
    _vars = [var if var else [DEFAULT_TIFF_DIRECTORY, DEFAULT_PREVIEW_DIRECTORY, DEFAULT_CSV_NAME][i] for i, var in enumerate([
   	    input("Please enter the directory in which you would like to save the TIFF images in (default: {0}/): ".format(DEFAULT_TIFF_DIRECTORY)),
        input("Please enter the directory in which you would like to save the JPG images in (deafult: {0}/):".format(DEFAULT_PREVIEW_DIRECTORY)),
        input("Please enter the name for the csv file (including .csv extension) (default {0})".format(DEFAULT_CSV_NAME))
    ])]
    [os.mkdir(i) for i in _vars[0:2] if not os.path.exists(i)] 

    return _vars[0], _vars[1], _vars[2]

class Csv:
    """A CSV class to be able to write to the CSV easily
       Attributes:
           counter: this is a counter in oirder to create the PXB SKUs
           csvfile: The file that is opened to keep the metadata in 
           csv_writer: object of hte csv.writer class, used to write data to the CSV
           directory: directory where the images are saved
    """
    def __init__(self):
        self.tiff_directory, self.jpg_directory, csv_filename = handle_directories( )
        self.counter = 0
        self.csvfile = open(csv_filename, "w", encoding="UTF-8")
        self.csv_writer = csv.writer(self.csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.csv_writer.writerow(["identification_number","image_url",
                                  "full_size_direct_download",
                                  "jpg_download_link","title","author",
                                  "original_creation_year", "original_location",
                                  "keywords", "category", "copyright_status"])

    """
	This method will take 1 paramter, which is data. This will be the metadata that is included in the photo.
	It will also download both the preview of the image, and the fully sized image. 
    """
    def write(self, data):
        self.counter+=1
        SKU = "PXB{}".format(str(self.counter).zfill(6))
        download_file(data[1],SKU,directory=self.tiff_directory)
        download_file(data[2],SKU,directory=self.jpg_directory, ext="jpg")
        self.csv_writer.writerow([SKU]+data)

"""
This will get all the specific image URLs from a page of image URLs, it will then deal with them individually in the 
handle_image function. 
"""
def image_urls(url):
    r      = make_request(url)
    soup   = BSoup(r.text, "lxml")
    a      = soup.find_all("div", class_="credits")
    images = a[0].findChildren("a")
    try:
        with Pool(10) as p:
            pm = p.imap_unordered(handle_image, [BASE_URL+image["href"] for image in images])
            pm = [i for i in pm if i]
    except KeyboardInterrupt:
        print("Exiting program")

def main( ):
    urls = make_urls( )
    with Pool(10) as p:
        pm = p.imap_unordered(image_urls, urls)
        pm = [i for i in pm if i]

if __name__=="__main__":
    try:
        CSV = Csv( )
        main( )
    except KeyboardInterrupt:
        print("Exitting the program...")
        exit( )