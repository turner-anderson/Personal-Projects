import logging
import time
import getpass
from selenium import webdriver
from selenium.common.exceptions import NoSuchFrameException

cp = fr'C:\Users\{getpass.getuser()}\AppData\Local\Microsoft\WindowsApps\chromedriver.exe'

## Set up logger
logging.basicConfig(
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    )
_log = logging.getLogger(name=__name__)
_log.setLevel(logging.INFO)

def find_addr(first_name: str, last_name: str, browser: object) -> str:
    """
    Browse to the fiscal office's website, look up a given individual and scrape their information
    """
    
    ## Go to fiscal site, then search for name
    browser.get(url='https://fiscaloffice.summitoh.net/index.php/property-tax-search')
    try:
        browser.switch_to.frame(0)
    except NoSuchFrameException:
        return None, None, []
    e1 = browser.find_element_by_xpath("//input[@name='own']")
    e2 = browser.find_element_by_xpath("//input[@value='Search']")
    e1.send_keys(f'{last_name}%{first_name}%')
    e2.click()

    
    ## Scrape address
    try:
        browser.switch_to.frame(1)
    except NoSuchFrameException:
        return None, None, []
    all_data = browser.find_elements_by_xpath("//tr")
    
    r = all_data[10].text
    x = 6
    y = r.index('RENTAL REG')
    addr = r[x:y].strip()
    
    # Check if they occupy the residence
    r = all_data[15].text.strip()
    if r[-3:] == 'Yes':
        lives_here = 'Y'
    else:
        lives_here = 'N'
    
    return addr, lives_here, browser.page_source
    
def parse_addr(addr: str) -> (str, str, str):
    """
    Parse the address by parsing out the city and zip code from the address
    """
    if addr[-3:] == ', -':
        z = ''
        addr = addr[:-3]  
    elif addr[-1] == '-':
        z = addr[-6:-1]
        addr = addr[:-6]
    else:
        z = addr[-10:-5]
        addr = addr[:-10]
        
    try:
        i = addr.index(',')
        city = addr[i + 1:].strip()
        addr = addr[:i].strip()
    except ValueError:
        city = ''
    
    
    return city, z, addr

def scrape_addresses(fn: str, ln: str, browser: str, out_p: str = None) -> list:
    """
    Use the find_addr function to scrape information for a particular individual as given by firstname = fn and lastname = ln, then
    persist the entire HTML page in disk space at path specified by out_p.
    """
    addr, lives_here, full_info = find_addr(fn, ln, browser)
    if full_info:
        city, z, addr = parse_addr(addr)
        row_data = [fn, ln, lives_here, addr, city, z]
        
        # Optionally print the HTML file to out_p 
        if out_p:
            with open(f'{out_p}{fn}_{ln}.html', 'w') as f:
                f.write(full_info)
    else:
        row_data = None
        
    return row_data


if __name__ == '__main__':
    print("This function queries the Summit County Fiscal Office's website and returns an address if the person exists uniquely on their site.")
    print("Please enter a name below")
    fn = input("First Name: ")
    ln = input("Last Name: ")
    browser = webdriver.Chrome(executable_path=cp)
    row_data = scrape_addresses(fn, ln, browser)
    if row_data:
        print(f"Information from the Fiscal Office website for {fn} {ln}:")
        print(row_data)
    else:
        print(f"Either zero or multiple people named {fn} {ln} exist on the Fiscal Office's site.")