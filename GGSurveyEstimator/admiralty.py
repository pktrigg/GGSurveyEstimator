########### Python 2.7 #############
import http.client, urllib, base64

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': '{subscription key}',
}

params = urllib.urlencode({
})

try:
    conn = httplib.HTTPSConnection('admiraltyapi.azure-api.net')
    conn.request("GET", "/uk_ship_routeing/v1/wms?%s" % params, "{body}", headers)
    response = conn.getresponse()
    data = response.read()
    print(data)
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################

########### Python 3.2 #############
import http.client, urllib.request, urllib.parse, urllib.error, base64

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': '{subscription key}',
}

params = urllib.parse.urlencode({
})

try:
    conn = http.client.HTTPSConnection('admiraltyapi.azure-api.net')
    conn.request("GET", "/uk_ship_routeing/v1/wms?%s" % params, "{body}", headers)
    response = conn.getresponse()
    data = response.read()
    print(data)
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################