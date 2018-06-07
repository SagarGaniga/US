# answering bot for trivia HQ and Cash Show
import json
import urllib.parse
import wikipedia
import urllib.request as urllib2
# import request
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import pyscreenshot as Imagegrab
import sys
import wx
from googleapiclient.discovery import build
import pprint
import numpy as np

my_api_key = "AIzaSyASDfmfsVIjyfgayCOv24Y3Hq-USDt8DUk"
my_cse_id = "014360726765778517958:hnpiknbfyzk"

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'


# sample questions from previous games
sample_questions = {}

# list of words to clean from the question during google search
remove_words = []

# negative words
negative_words = []


# load sample questions
def load_json():
    global remove_words, sample_questions, negative_words
    remove_words = json.loads(open("Data/settings.json").read())["remove_words"]
    negative_words = json.loads(open("Data/settings.json").read())["negative_words"]


# sample_questions = json.loads(open("Data/questions.json").read())["sample_questions"]

# take screenshot of question 
def screen_grab(to_save):
    # 31,228 485,620 co-ords of screenshot// left side of screen
    im = Imagegrab.grab(bbox=(30, 400, 450, 800))
    im.save(to_save, dpi=(600,600))

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    # pprint.pprint(res)
    return res['items']


# get OCR text //questions and options
def read_screen():
    # spinner = Halo(text='Reading screen', spinner='bouncingBar')
    # spinner.start()
    print("Reading Screen")
    screenshot_file = "Screens/to_ocr.png"
    screen_grab(screenshot_file)

    # prepare argparse
    ap = argparse.ArgumentParser(description='HQ_Bot')
    ap.add_argument("-i", "--image", required=False, default=screenshot_file, help="path to input image to be OCR'd")
    ap.add_argument("-p", "--preprocess", type=str, default="thresh", help="type of preprocessing to be done")
    args = vars(ap.parse_args())

    # load the image
    image = cv2.imread(args["image"])

    rgb = cv2.pyrDown(image)
    small = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    grad = cv2.morphologyEx(small, cv2.MORPH_GRADIENT, kernel)

    _, bw = cv2.threshold(grad, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
    connected = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
    _, contours, hierarchy = cv2.findContours(connected.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    mask = np.zeros(bw.shape, dtype=np.uint8)
    for idx in range(len(contours)):
        x, y, w, h = cv2.boundingRect(contours[idx])
        mask[y:y+h, x:x+w] = 0
        cv2.drawContours(mask, contours, idx, (255, 255, 255), -1)
        r = float(cv2.countNonZero(mask[y:y+h, x:x+w])) / (w * h)

        if r > 0.45 and w > 8 and h > 8:
            cv2.rectangle(rgb, (x, y), (x+w-1, y+h-1), (0, 255, 0), 2)

    cv2.imshow('rects', rgb)
    


    # col = Image.open(filename)
    # print(image)
    text = pytesseract.image_to_string(image)

    # spinner.succeed()
    # spinner.stop()
    return text


# get questions and options from OCR text
def parse_question():
    text = read_screen()
    lines = text.splitlines()
    question = ""
    options = list()
    flag = False

    for line in lines:
        if not flag:
            question = question + " " + line

        if '?' in line:
            flag = True
            continue

        if flag:
            if line != '':
                options.append(line)

    return question, options


# simplify question and remove which,what....etc //question is string
def simplify_ques(question):
    neg = False
    qwords = question.lower().split()
    if [i for i in qwords if i in negative_words]:
        neg = True
    cleanwords = [word for word in qwords if word.lower() not in remove_words]
    temp = ' '.join(cleanwords)
    clean_question = ""
    # remove ?
    for ch in temp:
        if ch != "?" or ch != "\"" or ch != "\'":
            clean_question = clean_question + ch

    return clean_question.lower(), neg


# get web page
def get_page(link):
    try:
        ny = wikipedia.page(link)
        # print(link)
        return ny.content
    except (urllib2.URLError, urllib2.HTTPError, ValueError) as e:
        return ''

    # # article = urllib.parse.quote(link, safe='')

    # opener = urllib2.build_opener()
    # opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this

    # resource = opener.open("http://en.wikipedia.org/wiki/" + article)
    # data = resource.read()
    # resource.close()
    # soup = BeautifulSoup(data)
    # content = soup.find('div',id="bodyContent").p
    # return content


# split the string
def split_string(source):
    splitlist = ",!-.;/?@ #"
    output = []
    atsplit = True
    for char in source:
        if char in splitlist:
            atsplit = True
        else:
            if atsplit:
                output.append(char)
                atsplit = False
            else:
                output[-1] = output[-1] + char
    return output



# answer by combining two words
def smart_answer(content, qwords):
    zipped = zip(qwords, qwords[1:])
    points = 0
    for el in zipped:
        if content.count(el[0] + " " + el[1]) != 0:
            points += 1000
    return points


# use google to get wiki page
def google_wiki(sim_ques, options, neg, simq):
    # spinner = Halo(text='Googling and searching Wikipedia', spinner='dots2')
    # spinner.start()
    print("Googling and searching Wikipedia")
    num_pages = 1
    points = list()
    content = ""
    maxo = ""
    maxp = -sys.maxsize
    words = split_string(simq)
    # page =  fetch(sim_ques)
    # content = page.lower()
    # print(content)
    for o in options:

        o = o.lower()
        original = o

        
        page = get_page(o)

        # print(page)
        temp = 0

        # print(words)
        # for word in words:
        #     temp = temp + page.count(word)
        # print(words)

        temp += smart_answer(page.lower(), words)
        if neg:
            temp *= -1
        print(temp) 
        points.append(temp)
        if temp > maxp:
            maxp = temp
            maxo = original
    # spinner.succeed()
    # spinner.stop()

    return maxo



# return points for live game // by screenshot
def get_points_live():
    neg = False
    question, options = parse_question()
    simq = ""
    points = []
    simq, neg = simplify_ques(question)
    maxo = ""
    m = 1
    if neg:
        m = -1
    print(simq)
    print(options)
    maxo = google_wiki(question, options, neg, simq)
    print(maxo)




# menu// main func
if __name__ == "__main__":
	
    # Load Json file
    load_json()
    while (1):
        keypressed = input(
            '\nPress s to screenshot live game, sampq to run against sample questions or q to quit:\n')
        if keypressed == 's':
            get_points_live()
        elif keypressed == 'sampq':
            get_points_sample()
        elif keypressed == 'q':
            break
        else:
            print( "\nUnknown input")
