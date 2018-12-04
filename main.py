#!/usr/bin/env python3

import os
import csv
import lxml
import requests
from time import sleep
from requests import RequestException
from multiprocessing.dummy import Pool
from bs4 import BeautifulSoup as BSoup

#The API is limited to 500 resutls, so I can't use that


BASE_URL = "https://pixabay.com"
username = "test_account_1873"
MAIN_URL = BASE_URL+"/en/photos?image_type=photo"
DEFAULT_DIRECTORY = "images/"
TIME_BETWEEN_FAILED_ATTEMPTS = 5

def download_file(url, name, directory=DEFAULT_DIRECTORY, chunk_size=1024):
        r = requests.get(url, stream=True)
        with open(directory+name+".jpg") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                                f.write(chunk)
                                f.flush( )

def make_request(url, failed_until_giveup=20):
    for attempt in range(failed_until_giveup):
        try:
            r = requests.get(url)
            return r
        except RequestException:
            print("[*] Request failed, retrying in {0} seconds".format(TIME_BETWEEN_FAILED_ATTEMPTS))
            print("Giving up in {0} attempts".format(failed_until_giveup-attempt))
            sleep(TIME_BETWEEN_FAILED_ATTEMPT)

def make_urls( ):
        #First I make 1 call to get the amount of pages that are availabe, then I
        r = make_url(MAIN_URL)
        soup = BSoup(r.text, "lxml")
        number_of_pages = soup.find_all("form", class_="add_search_params")[0].text.strip( ).strip("/").strip( )
        
        return [BASE_URL+"/en/photos"+"?&pagi="+str(i) for i in range(int(number_of_pages))]

def handle_image(url):
        r                = requests.get(url)
        soup             = BSoup(r.text, "lxml")
        cdn_640          = soup.find_all("input", type="radio")[0]["value"]
        cdn_1280         = cdn_640.replace("_640.jpg", "_1280.jpg")
        title            = soup.title.string.split("·")[0].strip( )
        author           = soup.find_all("img", class_="hover_opacity")[0]["alt"]
        details          = soup.find_all("table", id="details")
        year_created     = details[0].findChildren("td")[2].string.split( )[2]
        tags             = soup.find_all("h1")
        keywords         = " ".join([tag.string for tag in tags[0].findChildren("a") if tag.string is not None])
        category         = details[0].findChildren("a")[0].string
        
        #List goes as follows:
        #image_url, full_size_direct_download, jpg_download_link, title, author, Original publisher
        #original_creation_year,scene_information, original_location, keywords, categoy, copyright_status. 
        return [url, cdn_1280, cdn_640, title, author, "",  year_created, "", "", keywords, category, ""]

class Csv:
        def __init__(self, csv_filename="csv_file.csv"):
                self.counter = 0
                self.csvfile = open(csv_filename, "w")
                self.csv_writer = csv.writer(self.csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                self.csv_writer.writerow(["identification_number","image_url",
                                          "full_size_direct_download",
                                          "jpg_download_link","title","author",
                                          "original_publisher", "original_creation_year",
                                          "scene_information", "original_location",
                                          "keywords", "category", "copyright_status"])

        def write(self, data: list):
                self.counter+=1
                self.csv_writer.writerow(["PXB{}".format(str(self.counter).zfill(7))]+data)

        def __del__(self):
                self.csvfile.close( )

def image_urls(url):
        r    = requests.get(url)
        soup = BSoup(r.text, "lxml")
        a    = soup.find_all("div", class_="credits")
        images = a[0].findChildren("a")
        
        with Pool(10) as p:
            pm = p.imap_unordered(handle_image, [BASE_URL+image["href"] for image in images])
            pm = [i for i in pm if i]
        return [BASE_URL+image["href"] for image in images]

def main( ):
        urls = make_urls( )
        directory = str(input("Please enter the directory that you would like the images to be saved in (default: {}): ").format(DEFAULT_DIRECTORY))
        if not directory: directory=DEFAULT_DIRECTORY
        os.mkdir(directory)
        with Pool(10) as p:
                pm = p.imap_unordered(image_urls, urls)
                pm = [i for i in pm if i]

if __name__=="__main__":
        CSV = Csv( )

