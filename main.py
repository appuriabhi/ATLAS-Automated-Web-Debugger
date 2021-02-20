# main.py
# ToDo (next release)
# handle duplicate requests
# handle urls with query string appended

# Initial Setup 
start_page = 'https://abhinavpuri.com/'
# not setting page scan limit will throw error
limit = 5
# use below list to exclude specific diretory/pages
exclude_list = ['mailto:','javascript:','#','account','result']
# Setup complete

import asyncio
from pyppeteer import launch, launcher
from pyppeteer.network_manager import Request, Response
import urllib.parse
import csv
import time
import os
import pyppdf.patch_pyppeteer
import requests
from bs4 import BeautifulSoup
import zipfile

# Check script execution time
start_time = time.time()

# from Crawler
master_hrefs = []
#base domain can come from input or api call parameters
base_domain = start_page.replace('http://','').replace('https://','').replace('www.','')
base_domain = base_domain.split('/')[0]

# set up input for user to add paths, directories to exclude from crawling
# exclude list will work as string match only

# This will return True/False checking hrefs - True means add it to _indexer else (False) exclude
def _excludeCheck(_h):
    _h = _h.lower()
    _ret = True # setting true as default value
    for _i in exclude_list:
        _i = _i.lower()
        if _h.find(_i) == -1:
            # not in exclude list (add it)
            _ret = True
        else:
            # let us excoude this href
            _ret = False
            return _ret
    return _ret  


if (start_page[len(start_page)-1] == "/"):
    pass
else:
    start_page = str(start_page) + '/'

_obj = {}
_obj['page_url'] = start_page
_obj['crawlStatus'] = 'pending'
    
master_hrefs.append(_obj)
def get_protocol(url):        
    if ('https:' in url):
        p = 'https://'
    elif ('http:' in url):
        p = 'http://'
    else:
        p = 'http://'
    return p

def make_folder(base_domain):
    _dir = base_domain
    _time = time.asctime().replace(':','-').replace(' ','_').lower()
    _path = os.getcwd() + str('/'+_dir+'_'+_time)
    os.mkdir(_path)
    _file_info = {}
    _file_info['complete_path'] = _path
    _file_info['folder_name'] = str(_dir+'_'+_time)
    return _file_info

# Create new folder for this run
file_info = make_folder(base_domain)

def create_csv(file_name,li_to_add,headers):
    access_to_file = file_info['folder_name']+'/'+file_name

    if (os.path.exists(access_to_file)) == True:
        #don't set header
        with open(access_to_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(li_to_add)
    else:
        #write headers
        with open(access_to_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerow(li_to_add)

def _cookieWriter(file_name,li_to_add):
    headers = ['Page URL','Page Title','Status Code','Cookie Name','Cookie Value','Domain','Path','Expiry','Size','httpOnly','Secure','Session'] 
    access_to_file = file_info['folder_name']+'/'+file_name

    if (os.path.exists(access_to_file)) == True:
        #don't set header
        with open(access_to_file, 'a', newline='') as file:
            writer = csv.writer(file)
            for _c in li_to_add:
                _arr = []
                _arr.append(current_page_details.get('url',''))
                _arr.append(current_page_details.get('title',''))
                _arr.append(current_page_details.get('statusCode','200'))
                _arr.extend(list(_c.values()))                    
                writer.writerow(_arr)
    else:
        #write headers
        with open(access_to_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for _c in li_to_add:
                _arr = []
                _arr.append(current_page_details.get('url',''))
                _arr.append(current_page_details.get('title',''))
                _arr.append(current_page_details.get('statusCode','200'))
                _arr.extend(list(_c.values()))                 
                writer.writerow(_arr)


def _indexer(_arr,current_domain):
    protocol = get_protocol(current_domain)
    current_domain = current_domain.replace('http://','').replace('https://','').replace('www.','')
    current_domain = current_domain.split('/')[0]
    if (len(_arr) > 0):
        for val in _arr:
            try:           
                _href = (val.attrs['href'])
                if ((base_domain in _href) and (_href not in str(master_hrefs)) and (_excludeCheck(_href))):
                    _obj = {}
                    _obj['page_url'] = urllib.parse.unquote(_href)
                    _obj['crawlStatus'] = 'pending'
                    master_hrefs.append(_obj) 
                elif (_href[0] == '/' and (str(protocol) + (current_domain + _href).replace('//','/') not in str(master_hrefs)) and (_excludeCheck(_href))):
                    _obj = {}
                    _obj['page_url'] = urllib.parse.unquote(str(protocol) + (current_domain + _href).replace('//','/')) 
                    _obj['crawlStatus'] = 'pending'
                    master_hrefs.append(_obj)
            except:
                pass
                          
def _crawler(url):
    try:
        r = requests.get(url)
        statusCode = r.status_code
        
        if (statusCode == (200 or 400)):
            content = r.content
            soup = BeautifulSoup(content, 'lxml')
            #allScriptsList = soup.find_all('script')
            allAnchorTags = soup.find_all('a')
            pageTitle = soup.find('title')
            pageTitle = pageTitle.string
            #indexer function will be called here on allAnchorTags
            _indexer(allAnchorTags,str(url))
            #format file
            global current_page_details
            current_page_details = {}
            current_page_details['url'] = url
            current_page_details['statusCode'] = statusCode
            current_page_details['title'] = pageTitle
            print(current_page_details)
    except Exception as ex:
        print(ex) 
        print('Unexpected error occured\nPlease retart program')
        quit()   

# Create zip file for data extracted
def _zipFile(file_name):
    file_name = str(file_name)
    zf = zipfile.ZipFile(str(file_name)+".zip", "w")
    for dirname, subdirs, files in os.walk(file_name):
        zf.write(dirname)
        for filename in files:
            zf.write(os.path.join(dirname, filename))
    zf.close()

# end --------------------------
async def intercept_request(req:Request):
    '''
    if (req.resourceType == 'image') and (req.url.endswith('.png') or req.url.endswith('.jpg')):
        await req.abort()
    else:
        await req.continue_()
    '''   
    await req.continue_()


async def intercept_response(res:Response):
    status = res.status
    url = res.url
    _req = res.request
    _reqURL = _req.url
    _reqMethod = _req.method

    # Get Adobe Analytics Calls
    # Custom link calls: not included
    if ('b/ss' in url) and (status == 200) and 'pe=lnk_' not in url:
        aa_header_arr = ['Page URL','Page Title','Status Code','Method','Tracking Server','Report Suite','Version','Size','Request URL']
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))
        _arr.append(_reqMethod)
        if (_reqMethod == 'GET'):
            aa_payload = urllib.parse.unquote(res.url)
        elif (_reqMethod == 'POST'):
            aa_payload = urllib.parse.unquote(_req.postData)
        
        trimmed_aa_payload = aa_payload.replace('https://','').replace('http://','')
        trimmed_aa_payload = trimmed_aa_payload.split('/')
        _arr.append(trimmed_aa_payload[0])
        _arr.append(trimmed_aa_payload[3])
        _arr.append(trimmed_aa_payload[5])
        _arr.append(len(aa_payload))
        #print(aa_payload)
        _arr.append(aa_payload)
        # write to file
        create_csv('adobe_analytics.csv',_arr,aa_header_arr)

    # Get Google Analytics Calls
    if ('google-analytics.com/' in _reqURL) and (status == 200) and ('/collect' in _reqURL):
        ga_header_arr = ['Page URL','Page Title','Status Code', 'Method','Tracking Code','Event','Language','Size','Request URL']
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))

        if (_reqMethod == 'GET'):
            ga_payload = (urllib.parse.unquote(res.url))
        elif (_reqMethod == 'POST'):
            ga_payload = (urllib.parse.unquote(_reqURL))

        trimmed_ga_payload = ga_payload.replace('https://','').replace('http://','')
        trimmed_ga_payload = trimmed_ga_payload.split('&')
        _arr.append(_reqMethod)
        _ix = [i for i, s in enumerate(trimmed_ga_payload) if 'tid=UA-' in s]
        if (len(_ix)) > 0:
            _arr.append(trimmed_ga_payload[_ix[0]].replace('tid=',''))
        else:
            _arr.append('Not Found')
        if ('t=pageview' in ga_payload):
            _arr.append('pageview')
        else:
            _arr.append('Not Found')
        _arr.append(len(ga_payload))
        _arr.append(ga_payload)
        # write to file
        create_csv('google_analytics.csv',_arr,ga_header_arr)    

    # Check doubleclick floodlight Tags
    if ('fls.doubleclick.net/activity' in _reqURL) and status == 200:
        fls_header_arr = ['Page URL','Page Title','Status Code','Method','src','type','cat','ord','Size','Request URL']
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))
        _arr.append(_reqMethod)
        floodlight_payload = urllib.parse.unquote(_reqURL)
        floodlight_payload_split = floodlight_payload.split(';')
        _arr.append(floodlight_payload_split[2].split('=')[1])
        _arr.append(floodlight_payload_split[3].split('=')[1])
        _arr.append(floodlight_payload_split[4].split('=')[1])
        _arr.append(floodlight_payload_split[5].split('=')[1])
        _arr.append(len(floodlight_payload))
        _arr.append(floodlight_payload)
        # write to file
        create_csv('floodlight_tags.csv',_arr,fls_header_arr)


    # Check Adobe Target
    if ('tt.omtrdc.net' in _reqURL) and status == 200:
        target_header_arr = ['Page URL','Page Title','Status Code','Method','Tracking Server','Version','Size','Request URL','postData']
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))
        _arr.append(_reqMethod)
        _arr.append(_reqURL.replace('https://','').replace('http://','').split('/')[0])
        if (_reqMethod == 'GET'):           
            tt_payload = urllib.parse.unquote(res.url)
            tt_payload = tt_payload.lower()
            if 'version' in tt_payload:
                str1 = tt_payload.split('version=')[1]
                str2 = str1.split('&')[0]
                _arr.append(str2)
            else:
                _arr.append('')
            _arr.append(len(tt_payload))
            _arr.append(tt_payload)
            _arr.append('GET Request')

        elif (_reqMethod == 'POST'):
            _arr.append(_reqURL.split('version=')[1])
            _arr.append(len(_reqURL))
            _arr.append(_reqURL)
            _arr.append(_req.postData)
            tt_payload = urllib.parse.unquote(_req.postData)
        # write to file
        create_csv('adobe_target.csv',_arr,target_header_arr)

    # Facebook Pixels Fired
    if ('www.facebook.com/tr/' in _reqURL) and (status == 200) and (_reqMethod == 'GET'):
        fb_header_arr = ['Page URL','Page Title','Status Code','Method','Event','Size','Request URL']
        fb_payload = urllib.parse.unquote(_reqURL)
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))
        _arr.append(_reqMethod)
        if ('&ev=' in fb_payload):
            str1 = fb_payload.split('&ev=')[1]
            str2 = str1.split('&')[0]
            _arr.append(str2)
        else:
            _arr.append('')
        _arr.append(len(fb_payload))
        _arr.append(fb_payload)
        # write to file
        create_csv('facebook_pixels.csv',_arr,fb_header_arr)


    # Check GTM Container
    if (('googletagmanager.com/gtm.js?id=' in _reqURL) and (status == 200)):
        gtm_payload = urllib.parse.unquote(_reqURL)
        gtm_header_arr = ['Page URL','Page Title','Status Code','Method','GTM Container','Size','Request URL']
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))
        _arr.append(_reqMethod)
        _arr.append(_reqURL.split('?id=')[1])
        _arr.append(len(gtm_payload))
        _arr.append(gtm_payload)
        # write to file
        create_csv('google_tag_manager.csv',_arr,gtm_header_arr)

    # Check DTM/Launch Header Code
    if ('assets.adobedtm.com' in _reqURL) and (status == 200) and ('libraryCode' not in _reqURL) and (('launch' or 'satelliteLib') in _reqURL):
        launch_payload = (urllib.parse.unquote(_reqURL))
        launch_header_arr = ['Page URL','Page Title','Status Code','Method','DTM/Launch','Size','Request URL']
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))
        _arr.append(_reqMethod)
        if ('satelliteLib' in _reqURL):
            _arr.append('Adobe DTM Header')
        else:
            _arr.append('Adobe Launch Header')
        _arr.append(len(launch_payload))
        _arr.append(launch_payload)
        # write to file
        create_csv('adobe-dtm-launch.csv',_arr,launch_header_arr)

    # Check Decibel Code
    if ('cdn.decibelinsight.net/' in _reqURL) and (status == 200) and (_reqMethod == 'GET') and ('/di.js' in _reqURL):
        decibel_payload = (urllib.parse.unquote(_reqURL))
        decibel_header_arr = ['Page URL','Page Title','Status Code','Method','accountNumber','da_websiteId','Size','Request URL']
        _arr = []
        _arr.append(current_page_details.get('url',''))
        _arr.append(current_page_details.get('title',''))
        _arr.append(current_page_details.get('statusCode',status))
        _arr.append(_reqMethod)
        trimmed_decibel_payload = decibel_payload.replace('https://','').replace('http://','').split('/')
        _arr.append(trimmed_decibel_payload[2])
        _arr.append(trimmed_decibel_payload[3])
        _arr.append(len(decibel_payload))
        _arr.append(decibel_payload)
        # write to file
        create_csv('decibel_insight.csv',_arr,decibel_header_arr)
    pass

async def main(pageURL):
    print('..main..')

    try:
        # Browser startup parameters
        start_parm = {
            # Close the headless browser The default is to start headless
            "headless": True,
            "ignorehttpserrrors":True,
            "dumpio":True
        }

        #browser = await launch({'headless':True,"userAgent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36','autoClose':True,'args':['--no-sandbox']})
        browser = await launch(**start_parm)
        # Create a page object, page operations are performed on the object
        page = await browser.newPage()

        # JS is true by default
        #await page.setJavaScriptEnabled(enabled=True)
            
        await page.setRequestInterception(True)

        page.on('request', intercept_request)
        page.on('response', intercept_response)
        await page.goto(pageURL, {'timeout':25000})
        _cookies = await page.cookies()
        _cookieWriter('cookies.csv',_cookies)
        cur_dist = 0
        height = await page.evaluate("() => document.body.scrollHeight")
        while True:
            if cur_dist < height:
                await page.evaluate("window.scrollBy(0, 500);")
                await asyncio.sleep(0.2)
                cur_dist += 500
            else:
                break
        await browser.close()
    except Exception as e:
        print(e)
        print('timeout:25000ms exceded > headless browser closed')
        pass

for _index, _val in enumerate(master_hrefs):
    if (_val['crawlStatus'] == 'pending' and _index < int(limit)):
        print('---------------------')
        print('Urls Found: ', len(master_hrefs))
        print('---------------------\n')
        _crawler(_val['page_url'])
        asyncio.get_event_loop().run_until_complete(main(_val['page_url']))
        _val['crawlStatus'] = 'done'
    else:
        print('quit')
        end_time = time.time()
        time_taken = str(end_time - start_time)
        print(f'Program Compelete\nExecution Time: {time_taken} seconds for {_index} Web Pages.')
        
        #create zip file
        _zipFile(file_info.get('folder_name'))
        quit()