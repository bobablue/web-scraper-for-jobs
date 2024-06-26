import os
import datetime
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'headers':{'Content-Type':'application/x-www-form-urlencoded'},

                    # 208 fields in full POST data but only these are necessary to get all data
                    'post':{'dropListSize':100,
                            'ftlinterfaceid':'requisitionListInterface',
                            'ftlcompid':'validateTimeZoneId',
                            'ftlcompclass':'InitTimeZoneAction'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(response_obj):
    jobs_text = response_obj.text.split('!|!')

    # title, url, location
    data_indices = [(i,i+6,i+7) for i in range(8, len(jobs_text)+1, 42)]

    # clean up strings before adding to dict
    exclude = ['false','Next']
    data_dict = {}
    for idx in data_indices:
        if jobs_text[idx[1]] not in exclude:
            data_dict[meta['urls']['job']+jobs_text[idx[1]]] = {'Title':scrape_funcs.decode(jobs_text[idx[0]]),
                                                                'Location':scrape_funcs.decode(jobs_text[idx[2]])}

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], data=meta['requests']['post'])

    # if num_jobs>default in dropListSize, update post data and call again with updated number
    num_jobs = int(re.compile(r'listRequisition.nbElements!\|!(\d+)').findall(response.text)[0])
    if num_jobs>meta['requests']['post']['dropListSize']:
        meta['requests']['post']['dropListSize'] = num_jobs
        response = scrape_funcs.pull('post', url=meta['urls']['page'],
                                     headers=meta['requests']['headers'], data=meta['requests']['post'])

    jobs_dict = jobs(response)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)