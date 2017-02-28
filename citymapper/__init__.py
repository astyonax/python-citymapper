#
# Copyright 2014 Guglielmo Saggiorato
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#

"""Python library to access Citymapper transportation API"""

import requests
import warnings
import time

class citymapper(object):
    def __init__(self,key,limit=1000):
        """Citymapper class contains the methods:
            - transit
            - coverage (TODO)
            - coverage multipoints (TODO)
           exposed by the citymapper API

           Parameters
           ----------
           key : str
                API user key


           Examples
           --------
           >>> key = '124'
           >>> CM = citymapper(key)
           >>> r = CM.transit([1,1],[1,2])
           >>> print r
           {u'error_message': u'Invalid API key'}

        """

        self.key = key
        self.base_url = "https://developer.citymapper.com/"
        self.limit = 1000
        self.api_calls = 0
        # now the rate trhorlliting is implememented as a waiting time of self.rate/60 seconds
        # between calls
        self.rate = 10 # max rate per minute
        self.last_call_time = 0

    def _transit(self,origin,destination,time=None,time_type=None):
        """Configs the citymapper transit call
           This is separated by the transit method for easy testing.. (TODO: find better way)

           Parameters
           ----------
           same as self.transit

           Examples
           --------

           >>> CM = citymapper('123')
           >>> p = CM._transit([1,2],[1,3])
           >>> for k in sorted(p.keys()): print '{0:s}: {1:s}'.format(k,p[k])
           endcoord: 1,3
           node: api/1/traveltime/?
           startcoord: 1,2
           >>>

           TODO: add examples with time

           Notes
           -----

           The key: node identifies which service is being used (i.e. transit or coverage)
            and gives the service entry-point
        """

        params={}

        params['node']='api/1/traveltime/?'
        if time:
            params['time']=time
            warnings.warn('time must be in ISO-8601 format')
            if time_type in ['arrival']:
                params['time_type']=time_type
            elif time_type:
                raise Exception('time_type must be: "arrival"'
                                'https://citymapper.3scale.net/docs')
            else:
                raise Exception('time_type must be provided when a time is given')
        params['startcoord']=normalize_position(origin)
        params['endcoord']  =normalize_position(destination)
        return params

    def transit(self,origin,destination,time=None,time_type=None):
        """Retrieves the transit time from origin to destination using the citymapper transity API

            Parameters
            ----------

            Mandatory
             - origin, destination : {'lat':..,'lng':...}
                                  [lat,lng]

            Optional
             - time : string
                   ISO-8601 format for the departure time

             - time_type : 'arrival'
                   If time is not None, this is mandatory
                   arrival is the only supported value at the moment by the API

            Returns
            -------

            r : json
                Response in json format. Errors are passed up
                eg. r = {u'travel_time':42}
        """
        #------------------------------
        params = self._transit(origin,destination,time=time,time_type=time_type)
        query = self._make_url(params)
        return self._request(query).json()

    def _request(self,query):
        """Calls requests.get and throttles to query/sec (#in a brutal way)"""
        self.api_calls+=1
        if self.api_calls>= self.limit:
            raise StopIteration('citymapper max daily API calls limit reached')
        now = time.time()
        delta_T = now-self.last_call_time
        if delta_T>(60/self.rate):
            future = self.last_call_time+6
            delta_t = future-now
            try:
                import asyncio
                await asyncio.sleep(1)
            except ImportError:
                time.sleep(delta_T)
        self.last_call_time = time.time()
        return requests.get(query)

    def _make_url(self,params):
        """url encodes the query parameters

        Parameters
        ----------

        params : dict
               Dict containing the parameters of the query.
               The key: node is mandatory as it identifies which service is being used (i.e: transit or coverage)

        Examples
        --------

        >>> p = {'node':'fake/node/?','key1':'val1','key2':'val2'}
        >>> CM = citymapper('123')
        >>> url = CM._make_url(p)
        >>> print url
        https://developer.citymapper.com/fake/node/?key2=val2&key1=val1&key=123

        """
        node = params.pop('node')
        params['key']=self.key

        # join keys and values via =
        config_str=["{k}={v}".format(k=k,v=v) for k,v in params.iteritems()]
        # join configs via &
        config_str = '&'.join(config_str)

        query_str = "{base}{node}{config_str}"

        return query_str.format(base=self.base_url,
                                node=node,
                                config_str=config_str)

def islist(x):
    """Return True if x is a list
    Plain as in https://github.com/googlemaps/google-maps-services-python/blob/master/googlemaps/convert.py

    Parameters
    ----------
    x : any

    Examples
    --------

    >>> islist('abc')
    False
    >>> islist({'a':1,'b':2})
    False
    >>> islist([1,2])
    True
    >>> islist(set([1,2]))
    True
    """
    if isinstance(x,dict):
        return False
    if isinstance(x,str):
        return False
    return (not hasattr(x, "strip")
            and hasattr(x, "__getitem__")
            or  hasattr(x, "__iter__"))

def normalize_position(x):
    """converts a location object to a string suitable for the requests url
       (more or less inspired by the googlemaps python api)

       Parameters
       ----------
       x : dict
           {'lat':123,'lng':123}
       x : list of floats
           [lat,lng]

       Examples
       --------

       >>> x = {'lat':123,'lng':124}
       >>> normalize_position(x)
       '123,124'
       >>> normalize_position([123.01,124.00])
       '123.01,124'
    """
    float2str = lambda x: "{0:f}".format(x).rstrip('0').rstrip('.')

    if isinstance(x,dict):
        keys = x.keys()
        if 'lat' in keys and 'lng' in keys:
            lat = float2str(x['lat'])
            lng = float2str(x['lng'])
        else:
            raise TypeError('Position dict must contain lat and lng keys.')
    elif islist(x):
        lat = float2str(x[0])
        lng = float2str(x[1])
    else:
        raise TypeError('Unable to convert {!r} in <lat>,<long>'.format(x))

    out = "{latitude},{longitude}".format(latitude=lat,longitude=lng)
    return out
