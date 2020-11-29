import os
from bs4 import BeautifulSoup
import re
from utilities import FileContentGetter
import pandas as pd
from langdetect import detect



def book_scraping(html_source): # this takes the html content and returns a list with the useful info

    soup = BeautifulSoup(html_source, features='lxml') # instantiate a BeautifulSoup object for HTML parsing

    bookTitle = soup.find_all('h1', id='bookTitle')[0].contents[0].strip() # get the book title

    # if bookSeries is not present, then set it to the empty string
    try:
        bookSeries = soup.find_all('h2', id='bookSeries')[0].contents[1].contents[0].strip()[1:-1]
    except:
        bookSeries = ''

    # if bookAuthors is not present, then set it to the empty string
    try:
        bookAuthors = soup.find_all('span', itemprop='name')[0].contents[0].strip()
    except:
        bookAuthors = ''
    
    # the plot of the book is essential; if something goes wrong with the plot, raise an error
    try:
        descr = soup.find_all('div', id='description')[0].contents # get the plot
        descr_fil= list(filter(lambda s: s!='\n', descr)) # clean it from newline chars
        if len(descr_fil) == 1:
            Plot = ''.join(descr_fil[0].contents[0]) # join the filtered plot into a string
        else:
            descr_fil = descr_fil[1:-1]
            x = [j for i in descr_fil for j in i.contents if (isinstance(j, str)==True)]
            Plot = ''.join(x) # join the filtered plot into a string
        if detect(Plot) != 'en':
            raise Exception # if the plot is not in english, raise an error
    except:
        raise # pass the error to the caller function

    # if NumberofPages is not present, then set it to the empty string
    try:
        NumberofPages = soup.find_all('span', itemprop='numberOfPages')[0].contents[0].split()[0]
    except:
        NumberofPages = ''
    
    # if ratingValue is not present, then set it to the empty string
    try:
        ratingValue = soup.find_all('span', itemprop='ratingValue')[0].contents[0].strip()
    except:
        ratingValue = ''
    
    # if rating_reviews is not present, then set it to the empty string
    try:
        ratings_reviews = soup.find_all('a', href='#other_reviews')
        for i in ratings_reviews:
            if i.find_all('meta',itemprop='ratingCount'):
                ratingCount = i.contents[2].split()[0]
            if i.find_all('meta',itemprop='reviewCount'):
                reviewCount = i.contents[2].split()[0]
    except:
        ratings_reviews = ''

    # if Published is not present, then set it to the empty string
    try:        
        pub = soup.find_all('div', class_='row')[1].contents[0].split()[1:4]
        Published = ' '.join(pub) # join the list of publishers
    except:
        Published = ''
    
    # if Character is not present, then set it to the empty string
    try:
        char = soup.find_all('a', href=re.compile('characters')) # find the regular expression(re) 'characters' within the attribute href 
        if len(char) == 0:
            Characters = '' # no characters in char
        else:
            Characters = ', '.join([i.contents[0] for i in char])
    except:
        Characters = '' # something went wrong with char
    
    # if Setting is not present, then set it to the empty string
    try:
        sett = soup.find_all('a', href=re.compile('places')) # find the regular expression(re) 'places' within the attribute href 
        if len(sett) == 0:
            Setting = ''
        else:
            Setting = ', '.join([i.contents[0] for i in sett])
    except:
        Setting = '' # something went wrong with Setting
    
    # get the URL to the page
    Url = soup.find_all('link', rel='canonical')[0].get('href')

    return [bookTitle, bookSeries, bookAuthors, ratingValue, ratingCount, reviewCount, Plot, NumberofPages, Published, Characters, Setting, Url]


# for i in range(1, 301):
#     new_dir = f'./data/tsv/{i}' 
#     if not os.path.isdir(new_dir):
#         os.mkdir(new_dir)


content_getter = FileContentGetter('./data/html/*/*.html')
fields = ['bookTitle', 'bookSeries', 'bookAuthors', 'ratingValue', 'ratingCount', 'reviewCount',\
            'Plot', 'NumberofPages', 'Published', 'Characters', 'Setting', 'Url']
while True:
    html_content, dir_num, file_num = content_getter.get(file_ext='html')

    if html_content is None:
        break
    
    # something went wrong during the book scraping:
    #   * missing plot
    #   * plot not in english
    #   * something else
    try:
        book_info = book_scraping(html_content)
    except:
        with open('./log/log_tsv.txt', 'a') as log:
            log.write(f'html/{dir_num}/article_{file_num}.html\n') # trace the errors
        continue # continue the while loop from the top
    book_info = [field.replace('\n', ' ') for field in book_info] # clean the book fields from newline chars; this prevents errors in file .tsv writing
    data = dict.fromkeys(fields) # create a dictionary, using 'fields' as keys, to pass to a pandas.DataFrame object
    for field, info in zip(fields, book_info):
        data[field] = [info] # fill the dictionary
    book_info_df = pd.DataFrame(data) # new DataFrame containing the book information

    # print the DataFrame out into a .tsv file
    # keep the  structure and nomenclature of the original HTML file
    book_info_df.to_csv('./data/tsv/' + dir_num + '/article_' + file_num + '.tsv', sep='\t', index=False) 

