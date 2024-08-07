import os
import datetime
from bs4 import BeautifulSoup
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':25,

        'requests':{'url':{'startrow':0, 'locationsearch':'singapore'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('tr', class_='data-row')
    data_dict = {}
    for i in data:
        job = i.find('a', class_='jobTitle-link')
        data_dict[meta['urls']['job'] + job['href']] = {'Title':job.text,
                                                        'Location':i.find('span', class_='jobLocation').text.strip()}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = bs_obj.find('span', class_='paginationLabel').text
    num_jobs = int(re.search(r'of (\d+)', num_jobs).group(1))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['url'],
                                           page_range=range(1, pages+1),
                                           page_param='startrow',
                                           multiplier=pagesize)

    responses = scrape_funcs.concurrent_pull('get', url=meta['urls']['page'], params=page_info)

    for v in responses.values():
        jobs_dict.update(jobs(BeautifulSoup(v.content, 'html.parser')))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)