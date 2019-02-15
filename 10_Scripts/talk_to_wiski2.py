import urllib.request, urllib.parse, urllib.error
from xml.etree import cElementTree
import os
import re
import pandas as pd
import numpy as np
from datetime import datetime

# import Support.awrams_log
# logger = Support.awrams_log.get_module_logger('talk_to_wiski2')

today = datetime.now()
P = pd.date_range('1900-01-01',today,freq='D')

WISKI_URL = 'http://www.bom.gov.au/waterdata/'  ### SOS external web services
# KIWIS_URL = 'http://wiski-04:8080/KiWIS/KiWIS?service=kisters&type=queryServices&'  ### KIWIS internal web services

WISKI_CODES = {
               "Water Course Discharge": {"DMQaQc.Merged.DailyMean.09HR": "Pat4_C_B_1_DailyMean09"},
               "Water Course Level":     {"DMQaQc.Merged.DailyMean.24HR": "Pat3_C_B_1_DailyMean"},
               # "Storage Level":          {"DMQaQc.Merged.DailyMean.24HR": "Pat7_C_B_1_DailyMean"},
               # "Storage Volume":         {"DMQaQc.Merged.DailyMean.24HR": "Pat6_C_B_1_DailyMean"},
               "Storage Level":          {"DMQaQc.Merged.DailyMean.24HR": "Pat7_PR02_AHD_1_DailyMean"},
               "Storage Volume":         {"DMQaQc.Merged.DailyMean.24HR": "Pat6_PR02_AV_1_DailyMean"},
               }

DEV_MODE = True #False

class StationNotFoundException(Exception):
    def __str__(self):
        return "StationNotFoundException: %s" % self.args

class ParameterNotFoundException(Exception):
    def __str__(self):
        return "ParameterNotFoundException: %s" % self.args

class ParameterEmptyException(Exception):
    def __str__(self):
        return "ParameterEmptyException: %s" % self.args

class FlowUnitsNotCumecException(Exception):
    def __str__(self):
        return "FlowUnitsNotCumecException: %s" % self.args

def date_from_string(s):
    m = re.match("(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}.\d{3})(?P<utc>.\d{2}:\d{2})",s)
    return datetime(int(m.group("year")),int(m.group("month")),int(m.group("day")))

def s(u):
    '''
    strip url prefix from tags
    :param u:
    :return:
    '''
    reg = re.compile('{.*}(.+)')
    return reg.search(u).group(1)

def xml_from_url(req):
    resp = urllib.request.urlopen(req).read()
    x = cElementTree.fromstring(resp.read())
    return x

def replace_spaces(s):
    return s.replace(" ","%20")

def get_station_list(obs_type='Water Course Level'):
    '''
    Getfeatureofinterest request
    :return:
    '''

    foi = replace_spaces(obs_type)
    req = WISKI_URL+'services?service=SOS&version=2.0&request=Getfeatureofinterest&observedproperty=http://bom.gov.au/waterdata/services/parameters/'+foi
    print('req', req)
    print(parse_xml(xml_from_url(req),tag_type='featureMember',class_type=XOb))
    return parse_xml(xml_from_url(req),tag_type='featureMember',class_type=XOb)

def find_id_in_station_list(sid,xobs):
    matching = []
    for xob in xobs:

        stn = re.search('.*/(.+)$',xob.identifier.text).group(1)
        # stn = re.search('.*/([a-zA-Z]?)$',xob.identifier.text).group(1)

        if re.match(sid+'([a-zA-Z]?)|(\.\d+)$', stn):
            # print(sid,stn)
            matching.append(stn)

    return matching

def find_ob_in_station_list(sid,xobs):
    matching = []
    for xob in xobs:

        stn = re.search('.*/(.+)$',xob.identifier.text).group(1)
        # stn = re.search('.*/([a-zA-Z]?)$',xob.identifier.text).group(1)

        # if re.search(sid,stn):
        if re.match(sid+'([a-zA-Z]?)$', stn):
            # print(sid,stn)
            matching.append(xob)

    return matching

def get_availability_for_site(rid):
    print("GET DATA AVAILABILITY")

    req = WISKI_URL+'services?service=SOS&version=2.0&request=GetDataAvailability&featureofinterest=http://bom.gov.au/waterdata/services/stations/'+rid
    print(req)
    resp = urllib.request.urlopen(req)
    # js = json.load(reader(resp))
    print("GET DATA AVAILABILITY responded")
    xml = cElementTree.fromstring(resp.read())
    print("GET DATA AVAILABILITY xml")
    return xml

class XOb:
    '''
    digest wiski-2 xml Getobservation request
    '''

    def _builder(self,o):
        '''
        traverse nodes
        :param o:
        :return:
        '''

        if len(o) == 0:  # element has no children

            self.__dict__[s(o.tag)] = self.__class__()
            if hasattr(o,'text') and o.text is not None:
                self.__dict__[s(o.tag)].text = o.text

        else:  #  digest child nodes

            if s(o.tag) == 'point':  #  this is the data
                # if not hasattr(self,"_digest_data"):
                #     self._digest_data = digest_data
                digest_data(self,o)

            else: # this is meta
                self.__dict__[s(o.tag)] = self.__class__()
                # print("meta",o.tag,len(o))
                for e in o:
                    self.__dict__[s(o.tag)]._builder(e)

        if hasattr(o,'attrib'):  # add attributes to node

            for k,v in o.attrib.items():
                # print(o.tag,k,v)
                try:
                    ku = s(k)
                except AttributeError:
                    ku = k
                # self.__dict__[s(o.tag)].attr.__dict__[ku] = v
                self.__dict__[s(o.tag)].__dict__[ku] = v

def digest_data(self,o):
    '''
    digest data
    :param o:
    :return:
    '''
    if not hasattr(self,'qual'):
        self.qual = []
        self.idx = []
        self.val = []

    self.qual.append('-999')  # if no quality code present then set to None
    for d in o[0]:
        dtag = s(d.tag)
        if dtag == 'value':
            self.val.append(d.text)
        elif dtag == 'time':
            self.idx.append(d.text)
        elif dtag == 'metadata':
            for n in d[0]:
                ntag = s(n.tag)
                if ntag == 'qualifier':
                    for k,val in n.attrib.items():
                        if s(k) == 'title':
                            self.qual[-1] = val

class Caol:
    '''
    holds the digested xml object from a GetDataAvailability request
    and a dict of all timeseries names with valid data
    '''
    def __init__(self,xos):
        self.xos = xos
        self.chn_list = {}

        self._init()

    def _init(self):
        for xo in self.xos:
            if not hasattr(xo.phenomenonTime,'nilReason'):
                if xo.observedProperty.title not in self.chn_list:
                    self.chn_list[xo.observedProperty.title] = {}
                self.chn_list[xo.observedProperty.title][xo.procedure.title] = xo
            else:
                print(xo.procedure.title,"has no data")
        pass

def parse_data_availability(xml):
    xos = []

    for e in xml:
        tag = s(e.tag)

        if tag == 'dataAvailabilityMember':  # ignore all the other muck
            # print(tag)
            xo = XOb()
            xos.append(xo)

            for o in e:
                # print(o.tag)
                xo._builder(o)

    print("number of datasets found:",len(xos))

    c = Caol(xos)
    return c

class Islay:
    '''
    holds the digested xml object from a Getobservation request
    and a shortcut to the data node
    '''
    def __init__(self,xo):
        self.xo = xo
        self.observed_property = xo.observedProperty.title
        self._do = self.xo.result.MeasurementTimeseries

        if self.observed_property == 'Water Course Discharge' and \
          not xo.result.MeasurementTimeseries.defaultPointMetadata.DefaultTVPMeasurementMetadata.uom.code == 'cumec':
            raise FlowUnitsNotCumecException(xo.featureOfInterest.href)

    def get_dataframe(self):
        try:
            default_qual = int(self.xo.result.MeasurementTimeseries.defaultPointMetadata.DefaultTVPMeasurementMetadata.qualifier.title)
        except AttributeError:
            default_qual = -999

        try:
            data = np.array(self._do.val).astype(float)
            data_qual = np.array(self._do.qual).astype(int)
        except AttributeError:
            raise ParameterEmptyException(self.observed_property)

        data_qual[data_qual == -999] = default_qual

        return pd.DataFrame({'values':data,'qualifier':data_qual},
                            index=[date_from_string(t) for t in self._do.idx])

def parse_xml(xml,tag_type='observationData',class_type=XOb):
    global wo

    xos = []
    xo = None

    for e in xml:
        tag = s(e.tag)
        if tag == tag_type:  # ignore all the other muck
            # print(tag)
            xo = class_type()
            xos.append(xo)

            for o in e[0]:
                # print("\t",o.tag)
                xo._builder(o)

    # logger.info("%s id: %s number of observation datasets returned: %d",xo.observedProperty.title,xo.result.MeasurementTimeseries.id,len(xos))
    print("number of xml elements returned: %d" % len(xos))

    if xo is None:
        raise StationNotFoundException()

    if tag_type == 'featureMember':
        return xos

    else:
        wo = [Islay(xo) for xo in xos]
        return wo

def get_timeseries(foi_href,prop_href,proc_href,period):

    _prop_href = prop_href.replace(" ","%20")
    if period is None:
        tf = P[0].to_pydatetime().strftime("%Y-%m-%d") + '/' + P[-1].to_pydatetime().strftime("%Y-%m-%d")
    else:
        tf = period[0].to_pydatetime().strftime("%Y-%m-%d") + '/' + period[-1].to_datetime().strftime("%Y-%m-%d")

    req = WISKI_URL+'services?service=SOS&version=2.0&request=Getobservation&'+\
                    'featureofinterest='+foi_href+'&' +\
                    'observedproperty='+_prop_href+'&' +\
                    'procedure='+proc_href+'&' +\
                    'temporalfilter=phenomenonTime,'+tf

    if DEV_MODE:
        print(req)

    x = xml_from_url(req)

    if len(x) == 0:
        raise ParameterNotFoundException(os.path.basename(prop_href))

    return parse_xml(x)

def get_data_ob(rid,obs_type="Water Course Discharge",procedure=None,period=None,get_availability=False):
    '''

    :param rid:
    :param obs_type:
    :param procedure: "DMQaQc.Merged.DailyMean.09HR"
    :param period:
    :param get_availability:
    :return:
    '''

    if procedure is None:
        ### assuming there is only one procedure per obs type in WISKI_CODES
        procedure = WISKI_CODES[obs_type][list(WISKI_CODES[obs_type].keys())[0]]

    if get_availability:
        caol = parse_data_availability(get_availability_for_site(rid))
        a = caol.chn_list[obs_type][procedure]

        foi_href = a.featureOfInterest.href
        prop_href = a.observedProperty.href
        proc_href = a.procedure.href

    else:
        foi_href = "http://bom.gov.au/waterdata/services/stations/"+rid
        prop_href = "http://bom.gov.au/waterdata/services/parameters/"+obs_type
        proc_href = "http://bom.gov.au/waterdata/services/tstypes/"+procedure

    # print("QUERY",foi_href,prop_href,proc_href)

    return get_timeseries(foi_href,prop_href,proc_href,period)

def get_data(rid,obs_type="Water Course Discharge",procedure=None,period=None,get_availability=False):
    '''

    :param rid:
    :param obs_type:
    :param procedure: "DMQaQc.Merged.DailyMean.09HR"
    :param period:
    :param get_availability:
    :return:
    '''

    ### possible to get multiple return sites from wiski for one station id,
    ### strategy: take site with latest data and infill with other(s)
    obs = get_data_ob(rid,obs_type,procedure,period,get_availability)

    latest = datetime(1900,1,1)
    df = pd.DataFrame(columns=['values','qualifier'])

    for i,ob in enumerate(obs):

        _df = ob.get_dataframe()
        last = _df['values'].notnull().index[-1]

        df = df.reindex(df.index.union(_df.index))

        if last > latest:
            idx = _df.index[_df['values'].notnull()]
            df.loc[idx,'values'] = _df.loc[idx,'values']
            # df.loc[_df['values'].notnull(),'values'] = _df.loc[_df['values'].notnull(),'values']
            df.loc[idx,'qualifier'] = _df.loc[idx,'qualifier']
            latest = last

        else:
            df['values'].fillna(_df['values'])

        if len(obs) > 1:
            df[['values.'+str(i),'qualifier.'+str(i)]] = _df.loc[:,['values','qualifier']]

    return df

def merge_data_from_stations(stations,obs_type):
    stations.sort(reverse=True)  ### use latest infilled with older, assuming 229246C is later than 229246B
    d = {}

    for stn in stations:
        print("retrieving station: %s" % stn)
        try:
            d[stn] = get_data(stn,obs_type=obs_type)
        except (ParameterNotFoundException,ParameterEmptyException) as e:
            print("%s %s" % (stn,str(e)))
            # print(stn,e)

    df = pd.DataFrame(index=P)

    stns_used = []

    for stn in stations:
        if stn in d:
            stns_used.append(stn)

            for k in 'values','qualifier':

                for col in [c for c in d[stn].columns if c.startswith(k)]:
                    new_col = col.replace(k,k+'.'+stn)
                    df.loc[:,new_col] = d[stn].loc[:,col]

            if 'merged' not in df.columns:
                df['merged'] = df.loc[:,'values.'+stn]
                df['qc'] = df.loc[:,'qualifier.'+stn]
            else:
                isnull = df['merged'].isnull()
                df.loc[:,'merged'] = df['merged'].fillna(df['values.'+stn])
                df.loc[isnull,'qc'] = df['qualifier.'+stn]

    if len(df.columns) == 0:
        raise ParameterNotFoundException("no data found for: %s %s" % (obs_type,stations))

    return df

def interactive_get_data():
    x = cElementTree.fromstring(open('test/services.xml','r').read())
    return parse_xml(x)

def interactive_availability(rid=None,source=None):
    # x = cElementTree.fromstring(open('test/available.xml','r').read())
    if source is not None:
        x = cElementTree.fromstring(open(source,'r').read())

    elif rid is not None:
        x = get_availability_for_site(rid)

    else:
        print("specify either rid or source")
        return

    return parse_data_availability(x)

def _get_data_for_sites():
    sites = [
             '142801A',
             # '142108A',
             # '143036A',
             # '143305A',
             # '143111A',
             # '143234A',
             # '143235A',
             # '143228A',
             # '143049A',
             # '143047A',
             # '143048A',
             # '145021A',
             # '146033A',
             # '146034A',
             # 'sp-o10109',
             # 'sp-o10138',
             # 'sp-o10298',
             # 'sp-o10334',
             # 'sp-o10350',
             # 'sp-o10438',
             # 'sp-o10606',
             # 'sp-o10814',
             # 'sp-o10926',
             # 'sp-o10930',
             # 'sp-o11430',
             # 'sp-o11454',
             # 'sp-o11534',
             # 'sp-o11590'
             ]

    for s in sites:
        print(s)
        df = get_data(s,obs_type="Storage Level",procedure="Pat7_C_B_1_DailyMean")
        df.to_csv("./test/Storage_Level_"+s+".csv")
        df = get_data(s,obs_type="Storage Volume",procedure="Pat6_C_B_1_DailyMean")
        df.to_csv("./test/Storage_Volume_"+s+".csv")

def sj():
    import json
    import re
    import codecs
    reader = codecs.getreader("utf-8")

    resp = urllib.request.urlopen('http://wiski-04:8080/KiWIS/KiWIS?service=kisters&type=queryServices&request=getStationList&datasource=0&format=objson&station_name=*&returnfields=station_no,station_id,station_name,catchment_no,catchment_id,catchment_name,site_no,site_id,site_name,parametertype_id,parametertype_name,stationparameter_name,object_type,station_longname,custom_attributes')
    # resp = urllib.request.urlopen('http://ccfvp-wiskiap04:8080/KiWIS/KiWIS?service=kisters&type=queryServices&request=getSiteList&datasource=0&format=objson&returnfields=site_no,site_id,site_name,site_type_name,site_type_shortname,parametertype_id,parametertype_name,stationparameter_name,site_georefsystem,custom_attributes')
    j = json.load(reader(resp))
    # j = json.load(open('stations.json','r'))
    c = 0
    for d in j:
        if d['station_no'].startswith('228'):
            print(d)
            print()
        # if d['site_id'].startswith('22'):
        #     print(d['site_id'])
        # if d['parametertype_name'] == "Storage Level":
        #     print(c,d['station_longname'])
        #     c +=1
            #
            # for k,v in d.items():
            #     if k == 'station_no' or k == 'station_id' or k == 'station_name' or k == 'site_no' or k == 'site_id' or k == 'site_name':
                # if k == 'station_id' and v.startswith('228'): #or k == 'station_id':
                #     print(k, v)

            # print()
                #
                # if k.endswith('name'): # and "TARAGO" in k:
                #     if re.search('228224A',v):
                #         print(d)

if __name__ == '__main__':
    # # x = get_chn_list_for_site('410713')
    # # d = parse_get_data_availability(x)
    # #
    # # get_timeseries('410713','Water Course Discharge','DMQaQc.Merged.DailyMean.09HR',p,d)
    #
    #
    # x = cElementTree.fromstring(open('test/services.xml','r').read())
    # parse_xml(x,"Water.Course.Discharge")


    # x = cElementTree.fromstring(open('test/services.xml','r').read())
    # parse_xml(x,"Water.Course.Discharge")
    # sj()
    pass
