# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import logging
import json
import urllib
from operator import itemgetter

# [START urlfetch-import]
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
# [END urlfetch-import]
import webapp2
import time
regions = """ { "regions":
              [{"region": "Africa", "mapcode": "002", "countries":["Cameroon", "Central African Republic", "Chad", "Congo", "Democratic Republic of the Congo", "Equatorial Guinea", "Gabon", "Burundi", "Djibouti", "Eritrea", "Ethiopia", "Kenya",
                "Rwanda", "Somalia", "South Sudan", "Sudan", "Tanzania", "Uganda", "Angola", "Botswana", "Lesotho", "Malawi", "Mozambique", "Namibia", "South Africa", "Swaziland", "Zambia", "Zimbabwe", "Benin",
                "Burkina Faso", "Cape Verde", "Cote d'Ivoire", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Liberia", "Mali", "Mauritania", "Niger", "Nigeria",
                "Senegal", "Sierra Leone", "Togo", "Algeria", "Egypt", "Libya", "Morocco", "Tunisia", "Comoros", "Madagascar", "Mauritius", "Reunion","Western Sahara"] },
{"region": "Asia", "mapcode": "142", "countries":["Kazakhstan", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Uzbekistan", "Russia", "Borneo", "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Mekong Valley", "Myanmar", "Philippines",
"Singapore", "Thailand", "Timor-Leste", "Vietnam", "Bangladesh", "Bhutan", "India", "Afghanistan", "Bahrain", "Iran", "Iraq", "Israel", "Jordan", "Kuwait", "Lebanon", "Oman", "Qatar", "Saudi Arabia",
"Syria", "Turkey", "United Arab Emirates", "Yemen", "Nepal", "Pakistan", "Sri Lanka", "China", "Hong Kong", "Macau", "Tibet", "Japan", "Democratic People's Republic of Korea", "Republic of Korea",
"Mongolia", "Taiwan", "Armenia", "Azerbaijan", "Georgia (Republic)"] },
{"region": "Caribbean Region", "mapcode": "029", "countries":["Antigua and Barbuda", "Bahamas", "Barbados", "British Virgin Islands", "Cuba", "Dominica", "Dominican Republic", "Grenada", "Guadeloupe", "Haiti", "Jamaica", "Martinique",
"Netherlands Antilles", "Puerto Rico", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Trinidad and Tobago", "United States Virgin Islands", "Turks and Caicos", "Anguilla", "Cayman Islands", "Montserrat", "Saint Martin", "Sint Maarten" ] },
{"region": "Central America", "mapcode": "013", "countries":["Belize", "Costa Rica", "El Salvador", "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama"] },
{"region": "Europe", "mapcode": "150", "countries":["Andorra", "Austria", "Belgium", "Albania", "Estonia", "Latvia", "Lithuania", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Czech Republic", "Hungary", "Kosovo", "Macedonia (Republic)",
"Moldova", "Montenegro", "Poland", "Republic of Belarus", "Romania", "Serbia", "Slovakia", "Slovenia", "Ukraine", "France",
  "Germany", "Gibraltar", "Great Britain", "Channel Islands", "Guernsey", "England ", "Northern Ireland", "Scotland", "Wales",
  "Greece", "Ireland", "Italy", "Liechtenstein", "Luxembourg", "Cyprus", "Malta", "Sicily", "Monaco", "Netherlands", "Portugal", "San Marino", "Denmark",
  "Greenland", "Finland", "Iceland", "Norway", "Sweden", "Spain", "Switzerland", "Vatican City", "Faroe Islands", "Russia"] },
{"region": "North America", "mapcode": "021", "countries":["Canada", "Greenland", "United States", "Bermuda"] },
{"region": "Oceania", "mapcode": "009", "countries":["Australia", "Fiji", "New Caledonia", "Papua New Guinea", "Vanuatu", "Guam", "Palau", "New Zealand", "Hawaii", "Pitcairn Island", "American Samoa", "Independent State of Samoa", "Tonga", "Solomon Islands"] },
{"region": "South America", "mapcode": "005", "countries":["Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador", "French Guiana", "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela", "Falkland Islands"]}]
} """

urlstem = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&usehistory=y&retmode=json&retmax=0&email=ed_sperr%40hotmail.com&tool=medmap&term="
searches = []
localtime = time.asctime( time.localtime(time.time()) )


def search(name):
    for region in searches[0]['regions']:
        if region['region'] == name:
            return region

class myJson(ndb.Model):
    applicationName = ndb.StringProperty()
    json = ndb.TextProperty()

def searchStringer(area):
    if area == "Macedonia (Republic)":
        searchString = '"Macedonia (Republic)"[mesh]'
    elif area == "Georgia (Republic)":
        searchString = '"Georgia (Republic)"[mesh]'
    elif area == "Anguilla":
        searchString = 'Anguilla AND Caribbean'
    elif area == "Turks and Caicos":
        searchString = 'Turks and Caicos[tiab]'
    elif area == "Turkey":
        searchString = '("Turkey"[mesh] OR Turkey[tiab]) NOT (Avian OR Poultry)'
    elif area == "Guinea":
        searchString = '"Guinea"[mesh]'
    else:
        searchString = '("' + area + '"[mesh] OR ' + area + '[tiab])';
    return searchString;

def locationConvert(area):
    if area == "Macedonia (Republic)":
        locationString = 'Macedonia'
    elif area == "Georgia (Republic)":
        locationString = 'Georgia'
    elif area == "Democratic People's Republic of Korea":
        locationString = 'North Korea'
    elif area == "Republic of Korea":
        locationString = 'South Korea'
    elif area == "Turks and Caicos":
        locationString = 'Turks and Caicos Islands'
    else:
        locationString = area
    return locationString;


class BuildMapCount(webapp2.RequestHandler):

    def get(self):
        searchstr = "all[sb]+AND+(Africa+OR+Asia+OR+Caribbean+Region+OR+Central+America+OR+Europe+OR+North+America+OR+Oceania+OR+South+America+OR+Geographic+Locations[mesh])"
        url = urlstem + searchstr
        try:
            validate_certificate = 'true'
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                data = json.loads(result.content)
                count = data['esearchresult']['count']
                baseline = { "timestamp": localtime, "count": count, "regions": [] }
                searches.append(baseline)

            else:
                self.response.status_code = result.status_code
        except urlfetch.Error:
            logging.exception('Caught exception fetching url')

        regiondata = json.loads(regions)
        for x in regiondata['regions']:
            region = x['region']
            #self.response.write( region )
            self.fetchRegionCount(region)

        jsonText = json.dumps(searches[0])

        self.response.write(jsonText)

        gotJson = myJson.query(myJson.applicationName=='medmap').fetch()
        if len(gotJson) > 0:
            baseline = gotJson[0]
            baseline.json = jsonText
            baseline.put()
        else:
            baselinejson = myJson(applicationName='medmap', json=jsonText)
            baselinejson.put()


    def fetchRegionCount(self, region):
        # [START urlfetch-rpc]
        rpc = urlfetch.create_rpc()
        regionstr = urllib.quote_plus(region)
        searchterm = "(" + regionstr + "[mesh]+OR+" + regionstr + "[tiab])"
        url = urlstem + searchterm
        urlfetch.make_fetch_call(rpc, url)

        try:
            validate_certificate = 'true'
            result = rpc.get_result()
            if result.status_code == 200:
                data = json.loads(result.content)
                count = int(data['esearchresult']['count'])
                proportion = count / float(searches[0]['count'])
                regioncount = {
                    "region": region,
                    "count": count,
                    "proportion": proportion,
                    "countries": []
                }
                searches[0]['regions'].append(regioncount)
                self.fetchCountryCount(region)
            else:
                self.response.status_int = result.status_code
                self.response.write('URL returned status code {}'.format(
                    result.status_code))
        except urlfetch.DownloadError:
            self.response.status_int = 500
            self.response.write('Error fetching URL')

    def fetchCountryCount(self, region):
        myregion = search(region)
        regiondata = json.loads(regions)
        totalcount = float(searches[0]['count'])
        for x in regiondata['regions']:
            if x['region'] == region:
                countries = x['countries']
        for country in countries:
            validate_certificate = 'true'
            rpc = urlfetch.create_rpc()
            searchterm = urllib.quote_plus(searchStringer(country))
            url = urlstem + searchterm
            urlfetch.make_fetch_call(rpc, url)

            try:
                result = rpc.get_result()
                if result.status_code == 200:
                    data = json.loads(result.content)
                    count = int(data['esearchresult']['count'])
                    proportion = count / totalcount
                    countrycount = {
                        "country": locationConvert(country),
                        "count": count,
                        "proportion": proportion
                    }
                    myregion['countries'].append(countrycount)
                    myregion['countries'] = sorted(myregion['countries'], key=itemgetter('country'))
                else:
                    self.response.status_int = result.status_code
                    self.response.write('URL returned status code {}'.format(
                        result.status_code))
            except urlfetch.DownloadError:
                self.response.status_int = 500
                self.response.write('Error fetching URL')

class MainMap(webapp2.RequestHandler):
    """ Demonstrates an asynchronous HTTP query with a callback using
    urlfetch"""

    def get(self):
        self.response.headers = { "Content-Type": "application/json; charset=UTF-8",
         "Access-Control-Allow-Origin": "*" }
        latestJson = myJson.query(myJson.applicationName=='medmap').get()
        self.response.write(latestJson.json)

app = webapp2.WSGIApplication([
    ('/mapcounts', MainMap),
    ('/buildmapcounts', BuildMapCount),
], debug=True)
