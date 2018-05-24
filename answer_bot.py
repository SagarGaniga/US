# answering bot for trivia HQ and Cash Show
import json
import urllib.parse
import wikipedia
import urllib.request as urllib2
# import request
from bs4 import BeautifulSoup
from google import google
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import pyscreenshot as Imagegrab
import sys
import wx
from halo import Halo
from googleapiclient.discovery import build
import pprint
import numpy as np

my_api_key = "AIzaSyASDfmfsVIjyfgayCOv24Y3Hq-USDt8DUk"
my_cse_id = "014360726765778517958:hnpiknbfyzk"

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'


# for terminal colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# sample questions from previous games
sample_questions = {}

# list of words to clean from the question during google search
remove_words = []

# negative words
negative_words = []


# GUI interface
def gui_interface():
    app = wx.App()
    frame = wx.Frame(None, -1, 'win.py')
    # frame.SetDimensions(0, 0, 1200, 1200)
    frame.Show()
    app.MainLoop()
    return None


# load sample questions
def load_json():
    global remove_words, sample_questions, negative_words
    remove_words = json.loads(open("Data/settings.json").read())["remove_words"]
    negative_words = json.loads(open("Data/settings.json").read())["negative_words"]


# sample_questions = json.loads(open("Data/questions.json").read())["sample_questions"]

# take screenshot of question 
def screen_grab(to_save):
    # 31,228 485,620 co-ords of screenshot// left side of screen
    im = Imagegrab.grab(bbox=(650, 385, 1250, 1000))
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

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    img = cv2.bitwise_not(gray) 

    if args["preprocess"] == "thresh":
        gray = cv2.threshold(img, 60, 120,
                             cv2.THRESH_OTSU)[1]


    # filename = "Screens/{}.png".format(os.getpid())
    # cv2.imwrite(filename, gray)

    col = Image.fromarray(gray)

    # col = Image.open(filename)
    # col.show()
    area = (0, 0, 80, 400)
    cropped_img = col.crop(area)
    # cropped_img.show()
    col.paste(cropped_img, (44, 140, 124, 540))
    col.paste(cropped_img, (450, 140, 530, 540))
    # col.show()

    text = pytesseract.image_to_string(col)

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


# normalize points // get rid of common appearances // "quote" wiki option + ques
def normalize():
    return None


# take screen shot of screen every 2 seconds and check for question
def check_screen():
    return None


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


# return points for sample_questions
def get_points_sample():
    simq = ""
    x = 0
    for key in sample_questions:
        x = x + 1
        points = []
        simq, neg = simplify_ques(key)
        options = sample_questions[key]
        simq = simq.lower()
        maxo = ""
        points, maxo = google_wiki(simq, options, neg)
        print("\n" + str(x) + ". " + bcolors.UNDERLINE + key + bcolors.ENDC + "\n")
        for point, option in zip(points, options):
            if maxo == option.lower():
                option = bcolors.OKGREEN + option + bcolors.ENDC
            print(option + " { points: " + bcolors.BOLD + str(point) + bcolors.ENDC + " }\n")


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


# print("\n" + bcolors.UNDERLINE + question + bcolors.ENDC + "\n")
# for point, option in zip(points, options):
# 	if maxo == option.lower():
# 		option=bcolors.OKGREEN+option+bcolors.ENDC
# 	print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }\n")


# menu// main func
if __name__ == "__main__":
	
    # Load Json file
    load_json()
    while (1):
        keypressed = input(
            bcolors.WARNING + '\nPress s to screenshot live game, sampq to run against sample questions or q to quit:\n' + bcolors.ENDC)
        if keypressed == 's':
            get_points_live()
        elif keypressed == 'sampq':
            get_points_sample()
        elif keypressed == 'q':
            break
        else:
            print(bcolors.FAIL + "\nUnknown input" + bcolors.ENDC)
