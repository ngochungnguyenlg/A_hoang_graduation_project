import pickle
import datetime
from pyexpat import model
import time
import logging as log
import threading as td

import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions

import pandas as pd
import numpy as np
from fake_useragent import UserAgent
import re
# file_raw = pd.read_excel("./20211110.Final.Data.xlsx")
# header = file_raw.columns[4:]


def gettime():
    cur_time = str(datetime.datetime.now())
    cur_time = cur_time.replace(':', '.')
    return cur_time


def create_chrome():
    try:

        s = Service(ChromeDriverManager().install())
        ua = UserAgent()

        userAgent = ua.random
        chrome_op = webdriver.ChromeOptions()

        browser_locale = 'en'

        chrome_op.add_argument(f'user-agent={userAgent}')
        chrome_op.add_argument("--lang=en-GB")
        prefs = {
            "translate_whitelists": {"your native language": "en"},
            "translate": {"enabled": "True"}
        }
        chrome_op.add_experimental_option("prefs", prefs)
        # chrome_op.add_argument("user-agent=Iphone 11")
        # str_epoxy_1 = random.randrange(255)
        # str_epoxy_2 = random.randrange(100)
        # strepoxy_input='–proxy-server=209.127.191.'+str(str_epoxy_1)+':'+str(str_epoxy_2)

        # chrome_op.add_argument(strepoxy_input)

        # executable_path_c="C:\Program Files\Google\Chrome\Application\chrome.exe"
        executable_path_c = ".\chromedriver"
        createDriverChrome = webdriver.Chrome(
            chrome_options=chrome_op, service=s, executable_path=executable_path_c)
        createDriverChrome.minimize_window()
        # createDriverChrome.get('https://www.google.com')

        return createDriverChrome
    except:
        return -1


def create_firefox():
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)


def doMainJob(key_search, sleep=0):
    chrome = create_chrome()
    if(chrome == -1):
        print("cannot get chrome instance")
        return -1
    else:
        print("successfully create chrome object, the process is starting ...")
    chrome.get('https://www.google.com/search?q='+key_search)
    if sleep:
        random_sleep = np.random.uniform(2, 6)
        print(random_sleep)
        time.sleep(random_sleep)
    search = chrome.find_element_by_name('q')
    # search.send_keys(key_search)
    # search.send_keys(Keys.RETURN)
    # page_text = chrome.find_element_by_xpath("/html/body").text
    page_text = chrome.find_element_by_tag_name("body").text
    if sleep:
        random_sleep = np.random.uniform(5, 15)
        time.sleep(random_sleep)
    chrome.close()
    return page_text


def text_page_processing(text):
    text = text.replace('\n', ' ')

    # bỏ các kí tự đặc biệt và dấu xuống dòng
    text_nonalphanumeric = re.sub("[^0-9a-zA-Z]+", " ", text)
    text_nonASCII = re.sub("[\x00-\x2F\x3A-\x40\x5B-\x60\x7B-\x7F]+",
                           " ", text_nonalphanumeric)  # decode unicode symbols
    return text
# include thread


def logStart(processName):
    log.basicConfig(filename='./log/'+processName+'.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=log.DEBUG)


class Process_:
    def __init__(self, MAX_THREAD, processName, model_dict):
        self.MAX_THREAD = MAX_THREAD
        self.tickets = [0]*MAX_THREAD
        self.choosing = [0]*MAX_THREAD
        self.processName = processName
        self.model_dict = model_dict

    def call_model(self, model_name):  # Load models
        try:
            print('starting load ....' + model_name)
            loaded_model = pickle.load(open(model_name, 'rb'))
            print('loading success...' + model_name)
        except:
            return -1
        return loaded_model

    def run_with_out_multi_threading(self, key):

        text = doMainJob(key)

        if(text == -1):
            exit()
        elif (text.find('About this page') != -1) and (text.find('IP address') != -1) and (text.find('Time: 2021-') != -1):
            log.info(': thread '+str(1) +
                     ' inform that the google bot block crawling, thread ' + str(1) + ' is exitting ...')
            # add dong log moi thong bao viec google block va thoat khoi chuong trinh
            print(': thread '+str(1) +
                  ' inform that the google bot block crawling, thread ' + str(1) + ' is exitting ...')
            exit()  # thoat khoi chuong trinh
        return text

# apply backery algorithm in python.

    def lock(self, thread_num):
        self.choosing[thread_num] = True
        max_ticket = 0
        for i in range(self.MAX_THREAD):
            ticket = self.tickets[i]
            if ticket > max_ticket:
                max_ticket = ticket
        self.tickets[thread_num] = max_ticket+1
        self.choosing[thread_num] = False
        for i in range(self.MAX_THREAD):
            while(self.choosing[i]):
                pass
            while(self.tickets[i] != 0 and (self.tickets[i] < self.tickets[thread_num] or (self.tickets[i] == self.tickets[thread_num] and i < thread_num))):
                pass

    def unlock(self, thread_num):
        self.tickets[thread_num] = 0

    def write_result(self, df, row, col, infor):  # ghi kết quả
        # row, col are numberic
        df.iloc[row, col] = infor

    def underThread_func(self, key, i, j, thread_num, df, model):
        header = list(df.columns)
        print('-------------------------- header', header[j])
        log.info(': thread '+str(thread_num) +
                 ' execute the process with key ' + key + ' is starting ...')
        text = doMainJob(key, sleep=1)
        if(text == -1):
            exit()
        elif (text.find('About this page') != -1) and (text.find('IP address') != -1) and (text.find('Time: 2021-') != -1):
            log.info(': thread '+str(thread_num) +
                     ' inform that the google bot block crawling, thread ' + str(thread_num) + ' is exitting ...')
            # add dong log moi thong bao viec google block va thoat khoi chuong trinh
            exit()
        text = text_page_processing(text)
        result = model.predict([text])
        self.lock(thread_num)

        idx_push_result = df.columns.to_list().index(header[j]+"_output")
        idx_push_text = df.columns.to_list().index(header[j])

        print('---------------------------------------------------------------------------------------')
        print("input int to row ", i, " and columns ",
              idx_push_result, 'header name: ', header[j])
        print("orignal value:=", df.iloc[i, idx_push_result],
              " the value fill in cell ", i, " ", j, " is: ", str(text[0:10]), "...")
        print('---------------------------------------------------------------------------------------')
        log.info(
            ':---------------------------------------------------------------------------------------')
        log.info(': thread '+str(thread_num) +
                 ' write information in to row: ' + str(i))
        log.info(': thread '+str(thread_num) +
                 ' write information in to col: ' + str(idx_push_result))
        log.info(': thread '+str(thread_num)+' change information from: ' +
                 str(df.iloc[i, idx_push_result]) + ' to ' + str(text[0:10])+' ... header name' + header[j])
        df.iloc[i, idx_push_result] = result

        # ghi thong tin du doan
        self.write_result(df, i, idx_push_result, result[0])
        self.write_result(df, i, idx_push_text, text)  # ghi thong tin cua text

        time.sleep(0.1)
        log.info(': thread '+str(thread_num) +
                 ' fill in file successfully, thread out "__joined"')
        log.info(
            ':---------------------------------------------------------------------------------------')

        self.unlock(thread_num)

    def running_fuc(self, df, name, original_clm):
        logStart(self.processName)
        header = original_clm
        manufactor_pname = df.iloc[:, 1:3]
        real_clm = list(df.columns)
        for i in range(len(df)):
            for j in range(0, len(header), self.MAX_THREAD):
                try:
                    thread_list = []
                    count = 0
                    step_jump = self.MAX_THREAD
                    if(j+self.MAX_THREAD > len(header)):
                        step_jump = len(header)-j
                    for k in range(j, j+step_jump, 1):
                        key = str(manufactor_pname.iloc[i, 0]) + ' '+str(manufactor_pname.iloc[i, 1])\
                            + str(header[k].replace(header[k][0:2], '')
                                  )  # key search bao gồm: Manufacture + Product name + tên ecolabel

                        real_col = real_clm.index(header[k])
                        try:
                            print('k---------------------------', k, step_jump,
                                  j, j+step_jump, self.model_dict[header[k]])
                            model = self.call_model(
                                './model/'+self.model_dict[header[k]])
                        except:
                            # some time cannot find the header[k] because header[k] don't have in the dictionary
                            # if we don't ignore, the process will ignore the rest
                            log.info(
                                header[k] + ' fail load model, cannot tray the dict')
                            continue
                        if model == -1:
                            log.info(header[k] + ' fail load model')
                            # ignore the case cannot load model, because if we don't ignore, the process will ignore the rest
                            continue
                        td_ = td.Thread(target=self.underThread_func,
                                        args=(key, i, real_col, count, df, model))

                        td_.start()
                        thread_list.append(td_)
                        count += 1

                    for k in range(len(thread_list)):
                        if(type(thread_list[k]) != 'NoneType'):
                            thread_list[k].join()
                            log.info(':'+'thread '+str(k) + ' joined')
                    thread_list.clear()

                except TypeError as error:
                    log.info("joined--> error" + str(error))
                except Exception as error:
                    log.info("joined--> error" + str(type(error).__name__))
                except:
                    log.info("joined--> error cannot capture at row" + str(i))
            df.to_excel("./output/tem_output"+name+".xlsx", index=None)
