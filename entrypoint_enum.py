import requests 
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import urllib3
import urllib
import argparse, json
import re
import sys

urllib3.disable_warnings()

proxies = {
   'http': 'http://127.0.0.1:8080',
   'https': 'http://127.0.0.1:8080'
}

discovered_link = []
discovered_js = []

external_discovered_link = []
external_discovered_js = []


processed_link = []

excluded_links = []

include_list = []

exclude_list = []

cookies = {}
headers = {}


def base_link_format(link):
    if (link.split(" ")[0].endswith('/') ):    
        return link[0 : len(link) - 1 ]
        
    return link

def get_link(current_link, href_str, base_url):
    
    sending_link = ""

    if ( href_str.__contains__('http://') or href_str.__contains__('https://') ):
        sending_link = href_str
    elif (href_str.startswith('/')):
        if (current_link.__contains__('https://')):
            sending_link = 'https://'+base_url + href_str
        else:
            if (current_link.__contains__('http://')):
                sending_link = 'http://'+base_url + href_str
    elif(len(href_str.strip()) == 0):
        sending_link = current_link
    else:
        if(not current_link.split(" ")[0].endswith('/')):
            sending_link = construct_link(base_link_format(current_link), href_str)
        else:
            sending_link = base_link_format(current_link) + '/' + href_str
            
    return sending_link

def construct_link(current_link, href_str):

    parsed_url = urlparse(current_link)
    path_segments = parsed_url.path.split('/')
    path_segments.pop()

    path_segments.append(href_str)

    updated_path = '/'.join(path_segments)
    updated_url = parsed_url._replace(path=updated_path)

    modified_url = urlunparse(updated_url)
    
    return modified_url
    
def resolve_link(url):
    pattern = "[\.]+\/[a-zA-Z\/\._-]*"

    relative_url = re.findall(pattern, url)

    if not relative_url:
        return url

    relative_url = relative_url[0]
    base_url = url.split(relative_url)[0]
  
    return urljoin(base_url, relative_url)

def is_get_link(link):
    # ? in link
    if "?" in link:
        return True
    
    return False


def in_scope(link):
    global include_list, exclude_list
    for inc in include_list:    
        if not re.findall(re.compile(inc), link):
            return False
    
    for exc in exclude_list:    
        if re.findall(re.compile(exc), link):
            return False

    return True

def start_process(url):
    
    global processed_link
    
    link = resolve_link(url)
    
    if not link in processed_link:
        
        print("Processing "+url)
        print()

        links = get_all_clickable_link(link)
        
        processed_link.append(link)
       
        for l in links:
            if(not l in processed_link):
                if (in_scope(link) ):
                    if not is_get_link(link):
                        start_process(l)
 

def get_all_clickable_link(link):
    global discovered_link, discovered_js, external_discovered_link, external_discovered_js, cookies, headers 
    link_list = []
    js_list = []
    
    ext_link_list = []
    ext_js_list = []
    
    return_link_list = []
   
    page = None
    try:   
        page = requests.get(link, cookies=cookies, headers=headers, verify=False)
    
    except Exception as e:
        print(e)
    
    soup = BeautifulSoup(page.text, "lxml")

    
    link_list.append(get_link(link, "", urlparse(link).netloc))
    
    for a in soup.findAll("a", attrs={"href":True}):
        if(len(a['href']) > 0):
            if a['href'][0] != '#' and 'javascript:' not in a['href'].strip() and 'mailto:' not in a['href'].strip() and 'tel:' not in a['href'].strip():
                if 'http' in a['href'].strip() or 'https' in a['href'].strip():
                    if urlparse(link).netloc.lower() in urlparse(a['href'].strip()).netloc.lower():
                        if a['href'] not in link_list:
                            link_list.append(a['href'])
                    else:
                        if a['href'] not in ext_link_list:
                            ext_link_list.append(a['href'])
                else:
                    if a['href'] not in link_list:
                        link_list.append(get_link(link, a['href'], urlparse(link).netloc))
                        
    for a in soup.findAll("form", attrs={"action":True}):
        if(len(a['action']) > 0):
            if a['action'][0] != '#' and 'javascript:' not in a['action'].strip() and 'mailto:' not in a['action'].strip() and 'tel:' not in a['action'].strip():
                if 'http' in a['action'].strip() or 'https' in a['action'].strip():
                    if urlparse(link).netloc.lower() in urlparse(a['action'].strip()).netloc.lower():
                        if a['action'] not in link_list:
                            link_list.append(a['action'])
                    else:
                        if a['action'] not in ext_link_list:
                            ext_link_list.append(a['action'])
                else:
                    if a['action'] not in link_list:
                        link_list.append(get_link(link, a['action'], urlparse(link).netloc))
    
    for a in soup.findAll("iframe", attrs={"src":True}):
        if(len(a['src']) > 0):
            if a['src'][0] != '#' and 'javascript:' not in a['src'].strip() and 'mailto:' not in a['src'].strip() and 'tel:' not in a['src'].strip():
                if 'http' in a['src'].strip() or 'https' in a['src'].strip():
                    if urlparse(link).netloc.lower() in urlparse(a['src'].strip()).netloc.lower():
                        if a['src'] not in link_list:
                            link_list.append(a['src'])
                    else:
                        if a['src'] not in ext_link_list:
                            ext_link_list.append(a['src'])
                else:
                    if a['src'] not in link_list:
                        link_list.append(get_link(link, a['src'], urlparse(link).netloc))
                        
    for a in soup.findAll("script", attrs={"src":True}):
        if(len(a['src']) > 0):
            if a['src'][0] != '#' and 'javascript:' not in a['src'].strip() and 'mailto:' not in a['src'].strip() and 'tel:' not in a['src'].strip():
                if 'http' in a['src'].strip() or 'https' in a['src'].strip():
                    if urlparse(link).netloc.lower() in urlparse(a['src'].strip()).netloc.lower():
                        if a['src'] not in js_list:
                            js_list.append(a['src'])
                    else:
                        if a['src'] not in ext_link_list:
                            ext_js_list.append(a['src'])
                else:
                    if a['src'] not in js_list:
                        js_list.append(get_link(link, a['src'], urlparse(link).netloc))
                                            
    
    for href_item in link_list:
        if href_item not in discovered_link:
            return_link_list.append(href_item)
            discovered_link.append(href_item)
            
    for href_item in js_list:
        if href_item not in discovered_js:
            discovered_js.append(href_item)
            
    for href_item in ext_link_list:
        if href_item not in external_discovered_link:
            external_discovered_link.append(href_item)
            
    for href_item in ext_js_list:
        if href_item not in external_discovered_js:
            external_discovered_js.append(href_item)
            
    return return_link_list     
    


def main():

    parser = argparse.ArgumentParser(description="""entrypoint_enum.py
       
    Ex: python3 entrypoint_enum.py -l http://192.168.43.16/DVWA2/ -c '{"PHPSESSID": "ockufsp8jup8j1qc5u13o1kq1f", "security": "low"}' -H  '{"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Connection": "close", "Upgrade-Insecure-Requests": "1"}' -e http://192.168.43.16/DVWA2/logout.php """)

    parser.add_argument('-l', '--link', type=str, help='Link URL')
    parser.add_argument('-e', '--exclude', nargs='+', type=str, help='Regex of excluded links separated by space')
    parser.add_argument('-i', '--include', nargs='+', type=str, help='Regex of included links separated by space: this will be used as whitelist')
    parser.add_argument('-c', '--cookie', type=str, help='Cookie dictionary')
    parser.add_argument('-H', '--header', type=str, help='Headers dictionary')
    
    args = parser.parse_args()

    if not args.link:
        parser.print_help() 
        sys.exit(1)  


    if args.cookie:
        # Parse the cookie argument as a dictionary
        try:
            cookies = json.loads(args.cookie)
        except json.JSONDecodeError:
            print("Invalid JSON format for the cookie argument")
            return
    else:
        cookies =  {}

    if args.header:
        # Parse the header argument as a dictionary
        try:
            headers = json.loads(args.header)
        except json.JSONDecodeError:
            print("Invalid JSON format for the header argument")
            return
    else:
        headers =  {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Connection": "close", "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1"}

    
    if args.exclude:
        exclude_list = args.exclude
    else:
        exclude_list = []

    if args.include:
        include_list = args.include
    else:
        include_list = []

    global processed_link, discovered_js
    
    link = args.link
    links = get_all_clickable_link(link)
    
    processed_link.append(link)
    
    for l in links:
        link = resolve_link(l)
        if (in_scope(link) ):
            if not is_get_link(link):
                start_process(link)
                
    print("===Discovered links===")
    for d in discovered_link:
        print(d)
    print()
        
    print("===Discovered js===")   
    for d in discovered_js:
        print(d)
    print()
        
    print("===External discovered link===")  
    for d in external_discovered_link:
        print(d) 
    print()
    
    print("===External discovered js===")  
    for d in external_discovered_js:
        print(d) 
    
if __name__ == '__main__':
    main()