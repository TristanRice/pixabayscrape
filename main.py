#!/usr/bin/env python3

import os
import csv
import lxml
import socket
import requests
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
TIME_BETWEEN_FAILED_ATTEMPTS = 5

def download_file(url, name, directory=DEFAULT_TIFF_DIRECTORY, chunk_size=1024, ext="tiff"):
    print("[*] Downloading file {0}".format(url))
    r = make_request(url, stream=True)
    with open("{0}/{1}.{2}".format(directory, name, ext), "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                f.flush( )

def make_request(url, failed_until_giveup=20, stream=False):
    for attempt in range(failed_until_giveup):
        try:
            r = requests.get(url, stream=stream)
            return r
        except RequestException:
            print("[*] Request failed, retrying in {0} seconds".format(TIME_BETWEEN_FAILED_ATTEMPTS))
            print("Giving up in {0} attempts".format(failed_until_giveup-attempt))
            sleep(TIME_BETWEEN_FAILED_ATTEMPTS)
        except socket.error:
        	print("err")

def make_urls( ):
    """This gets the total amount of pages that are in the websites /en/photos, and will return a list of all possible
       URLS that I can get images from."""
    r = make_request(MAIN_URL)
    soup = BSoup(r.text, "lxml")
    number_of_pages = soup.find_all("form", class_="add_search_params")[0].text.strip( ).strip("/").strip( ) #This gets the total numebr of pages
    
    return [BASE_URL+"/en/photos"+"?&pagi="+str(i) for i in range(int(number_of_pages))]

def handle_image(url):
    #This gets the image url, and gets all metadata 
    r                =   requests.get(url)
    soup             =   BSoup(r.text, "lxml")
    cdn_640          =   soup.find_all("input", type="radio")[0]["value"]
    cdn_1280         =   cdn_640.replace("_640.jpg", "_1280.jpg")
    title            =   soup.title.string.split("·")[0].strip( )
    author           =   soup.find_all("img", class_="hover_opacity")[0]["alt"]
    details          =   soup.find_all("table", id="details")
    year_created     =   details[0].findChildren("td")[2].string.split( )[2]
    tags             =   soup.find_all("h1")
    keywords         =   " ".join([tag.string for tag in tags[0].findChildren("a") if tag.string is not None])
    try:
        category         =   details[0].findChildren("a")[0].string
    except IndexError:
    	#In this case, there isn't a category, so I can't 
        category = ""

    #List goes as follows:
    #image_url, full_size_direct_download, jpg_download_link, title, author, Original publisher
    #original_creation_year,scene_information, original_location, keywords, categoy, copyright_status.
    
    list1 = [url, cdn_1280, cdn_640, title, author, "",  year_created, "", "", keywords, category, "Royalty free"]
    CSV.write(list1)
    return list1

def handle_directories( ):
    tiff_directory = input("Please enter the directory in which you would like to save the TIFF images in (default: {0}/ ): ".format(DEFAULT_TIFF_DIRECTORY))
    jpg_directory  = input("Please enter the directory in which you would like to save the JPG images in (deafult: {0}/ ):".format(DEFAULT_PREVIEW_DIRECTORY))
    if not tiff_directory: tiff_directory = DEFAULT_TIFF_DIRECTORY
    if not jpg_directory: jpg_directory = DEFAULT_PREVIEW_DIRECTORY
    if not os.path.exists(tiff_directory): os.mkdir(tiff_directory)
    if not os.path.exists(jpg_directory): os.mkdir(jpg_directory)

    return tiff_directory, jpg_directory

class Csv:
    """A CSV class to be able to write to the CSV easily
       Attributes:
           counter: this is a counter in oirder to creaet the PXB SKUs
           csvfile: The file that is opened to keep the metadata in 
           csv_writer: object of hte csv.writer class, used to write data to the CSV
           directory: directory where the images are saved
    """
    def __init__(self, csv_filename="csv_file.csv"):
        self.tiff_directory, self.jpg_directory = handle_directories( )
        self.counter = 0
        self.csvfile = open(csv_filename, "w", encoding="UTF-8")
        self.csv_writer = csv.writer(self.csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.csv_writer.writerow(["identification_number","image_url",
                                  "full_size_direct_download",
                                  "jpg_download_link","title","author",
                                  "original_publisher", "original_creation_year",
                                  "scene_information", "original_location",
                                  "keywords", "category", "copyright_status"])

    def write(self, data: list):
        self.counter+=1
        SKU = "PXB{}".format(str(self.counter).zfill(6))
        download_file(data[1],SKU,directory=self.tiff_directory)
        download_file(data[2],SKU,directory=self.jpg_directory, ext="jpg")
        self.csv_writer.writerow([SKU]+data)


def image_urls(url):
    r    = requests.get(url)
    soup = BSoup(r.text, "lxml")
    a    = soup.find_all("div", class_="credits")
    images = a[0].findChildren("a")
    try:
        with Pool(10) as p:
            pm = p.imap_unordered(handle_image, [BASE_URL+image["href"] for image in images])
            pm = [i for i in pm if i]
    except KeyboardInterrupt:
        print("Exiting program")

    return [BASE_URL+image["href"] for image in images]

def main( ):
    urls = make_urls( )
    #[os.mkdir(directory) if not os.path.exists(directory)]
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