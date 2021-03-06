from base64 import b64encode
from os import makedirs
from os.path import join, basename 
from sys import argv
import json
import requests
import os
from PIL import Image
import pyscreenshot as Imagegrab
import re
from urllib.request import urlopen
import pytesseract
from bs4 import BeautifulSoup
CLOUD_VISION_ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'
from googleapiclient.discovery import build
import pprint

api_key = "AIzaSyASDfmfsVIjyfgayCOv24Y3Hq-USDt8DUk"
cse_id = "014360726765778517958:hnpiknbfyzk"

# print(argv[1])

eliminated = False
if argv[1] == '1':
    eliminated = True    

hq = 0
ho = 0


def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']



def scores_with_options(question,options,**kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    scores = [0,0,0]
    for idx, option in enumerate(options):
        res = service.cse().list(q=question+' '+option+' wiki', cx=cse_id, **kwargs).execute()
        # print(res)
        scores[idx] = int(res['searchInformation']['totalResults'])
    print(scores)
    return scores

def normal_scores(question,options):
    results = google_search(question, api_key, cse_id, num=3)
    scores = [0,0,0]

    # print(results[0]["link"])
    
    for idx, result in enumerate(results):
        f = urlopen(result["link"])
        print(result["link"])
        myfile = f.read()
        # print (myfile)
        soup = BeautifulSoup(myfile,"lxml")
        page = soup.get_text().lower()
        # print(page)
        for n, option in enumerate(options):
                # print(n)
                # words = option.split(' ')
                # print(option.split(' '))
                # for word in words:
                occurences = page.lower().count(option.lower())
                scores[n] = occurences+scores[n]

    # for idx, result in enumerate(results):
    #     snippet = result['snippet']
    #     print(result['link'])
    #     # print(snippet)
        # for n, option in enumerate(options):
        #     # print(n)
        #     # words = option.split(' ')
        #     # print(option.split(' '))
        #     # for word in words:
        #     occurences = page.lower().count(option.lower())
        #     scores[n] = occurences+scores[n]
        print(scores)
    print(scores)
    return scores

def make_image_data_list(image_filenames):
    """
    image_filenames is a list of filename strings
    Returns a list of dicts formatted as the Vision API
        needs them to be
    """
    img_requests = []
    for imgname in image_filenames:
        with open(imgname, 'rb') as f:
            ctxt = b64encode(f.read()).decode()
            img_requests.append({
                    'image': {'content': ctxt},
                    'features': [{
                        'type': 'TEXT_DETECTION',
                        'maxResults': 1
                    }]
            })
    return img_requests

def make_image_data(image_filenames):
    """Returns the image data lists as bytes"""
    imgdict = make_image_data_list(image_filenames)
    return json.dumps({"requests": imgdict }).encode()

def request_ocr(api_key, image_filenames):
    # response = requests.post(CLOUD_VISION_ENDPOINT_URL,
    #                          data=make_image_data(image_filenames),
    #                          params={'key': api_key},
    #                          headers={'Content-Type': 'application/json'})
    for image in image_filenames:
        text
    text = pytesseract.image_to_string()
    return response

def get_text_from_response(response):
    t = response['textAnnotations'][0]
    return (t['description'])

def take_screenshot(l):
    # os.system("adb exec-out screencap -p > screen.png")
    im = Imagegrab.grab(bbox=(30, 410+hq-l, 450, 820+hq+l))
    im.save('screen.png', dpi=(600,600))

def split_screen_to_question_and_options(n,m):
    i = Image.open('screen.png')
    width, height = i.size 
    # print(l)
    question_end_y = 90+ho+n
    frame = i.crop(((0,0,width,question_end_y)))
    frame.save('question.png')

    one_start = question_end_y+18+ho
    frame = i.crop(((50,one_start,width-50,one_start+40)))
    frame.save('1.png')

    two_start = one_start +80+ ho
    frame = i.crop(((50,two_start,width-50,two_start+40)))
    frame.save('2.png')

    three_start = two_start + 80+ho
    frame = i.crop(((50,three_start,width-50,three_start + 40)))
    frame.save('3.png')
    # frame.show()


option_names = ['A','B','C']

def print_scores(scores,method):
    print(scores)
    print (method+'\n-----------------------------')
    print ("Most relevant : "+ str(option_names[scores.index(max(scores))]))
    print ("Least relevant : "+ str(option_names[scores.index(min(scores))]))


if __name__ == '__main__':
    while True:
        
        a = input("Wait for the next question and press Enter key instantly when it's displayed\n")
        
        ho = int(a)*6+6

        if eliminated:
            hq = 35
            ho=int(a)*7

        l=0
        m=0
        n=0
        if int(a)==4:
            l=30
            n=45
            m=n-20
            ho=20



        take_screenshot(l)
        split_screen_to_question_and_options(n,m)
        
        col = Image.open('question.png')
        question = pytesseract.image_to_string(col)
        
        question = re.sub('[^A-Za-z0-9\s]+', '', question)
        print(question);
        col = Image.open('1.png')
        op1 = pytesseract.image_to_string(col)
        # print(op1)

        col = Image.open('2.png')
        op2 = pytesseract.image_to_string(col)
        # print(op2)

        col = Image.open('3.png')
        op3 = pytesseract.image_to_string(col)
        # print(op3)
        
        options = [op1,op2,op3]
        for idx,option in enumerate(options):
            options[idx] = option.strip(' \t\n\r').lower()

        print(options)
        normal = normal_scores(question,options)
        # print_scores(normal,'Method 1 (Question search)')
        # withoption = scores_with_options(question,options)
        # print_scores(withoption,'Method 2 (Question and options search)')