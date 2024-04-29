#!/usr/bin/env python

import sys
import requests
import json
from class_ids import *

def main(id):
    print("Påbörjar körning...")

    data = fetch_data(id)
    filename = get_filename(data)

    open(filename, 'w').close()
    writehandle = open(filename, 'w')

    class_ids = get_class_ids()

    groups = get_classes(data, writehandle, class_ids)
    get_competitors(data, writehandle, class_ids, groups)
    get_officials(data, writehandle)
    get_competiton(data, writehandle, class_ids)

    writehandle.close()
    
    print(f"Körning klar. Filen {filename} har skapats.")

def fetch_data(id):
    url = f"https://brukshundklubben.se/api/get_competition?id={id}"
    response = requests.get(url)
    data = json.loads(json.loads(response.text))
    return data
    
def get_filename(data):
    date = data['startDate'].split('T')[0].replace('-', '')
    name = data['name'].replace(' ', '_')
    id = data['id']
    filename = f"{date}-{id}-{name}.prov"
    return filename

def get_classes(data, writehandle, class_ids):
    groups = {}
    
    for c in data['classes']:
        n = 0
        while f'{class_ids[c["classItem"]["identifier"]]}.{n}' in groups:
            n += 1
        
        groups[f'{class_ids[c["classItem"]["identifier"]]}.{n}'] = c["id"]

        writehandle.writelines(f'[{class_ids[c["classItem"]["identifier"]]}.{n}]\n')
        
        n = 1
        for r in c['referees']:
            referee_id = r['id']
            for i, cr in enumerate(data['referees']):
                if cr['id'] == referee_id:
                    referee_nr = i + 1
                    break
            
            writehandle.writelines(f'domare{n}={referee_nr}\n')

            n += 1
        
        writehandle.writelines(f'name={c["classItem"]["name"]}\n')
        writehandle.writelines(f'sbkt={c["id"]}\n')
        writehandle.writelines('state=initialized\n')
        writehandle.writelines('\n')

    return groups
    


def get_competitors(data, writehandle, class_ids, groups):
    n = 1
    for c in data['classes']:
        class_id = class_ids[c['classItem']['identifier']]
        group = list(groups.keys())[list(groups.values()).index(c['id'])]
        competitors = fetch_startlist(c['id']) + fetch_reservelist(c['id'])

        for competitor in c['registrations']:
            try:
                height = next((p for p in competitors if p['id'] == competitor['id']), None)["height"]
            except:
                height = "0"
            
            n = get_competitor(writehandle, competitor, class_id, n, group, height)

def fetch_reservelist(class_id):
    url = f"https://brukshundklubben.se/api/get_competitionReserveList?competitionClassId={class_id}"
    response = requests.get(url)
    data = json.loads(json.loads(response.text))
    return data

def fetch_startlist(class_id):
    url = f"https://brukshundklubben.se/api/get_competitionStartList?competitionClassId={class_id}"
    response = requests.get(url)
    data = json.loads(json.loads(response.text))
    return data


def get_competitor(writehandle, competitor, class_id, index, group, height):
    try:
        if competitor['withdraw']:
            return index

        dogRegistration = competitor['dogRegistration']
        skk_data = fetch_skk(dogRegistration)
        handler_data = fetch_handler(competitor['membercareUserId'])
        isMale = int(skk_data.get("d")[0].get("Kon") == "H")

        competitor_output = f'[e{index}]\n'
        competitor_output += f'chipsnr={skk_data.get("d")[0].get("chipnr")}\n'
        competitor_output += f'epost={handler_data["email"]}\n'
        competitor_output += f'förare={handler_data["handlerName"]}\n'
        competitor_output += f'grupp={group.split(".")[1]}\n'
        competitor_output += f'hund={competitor["dogName"]}\n'
        competitor_output += f'mankhöjd={height}\n'
        competitor_output += f'hane={isMale}\n'
        competitor_output += f'klass={class_id}\n'
        competitor_output += f'klubb={competitor["club"]}\n'
        competitor_output += f'ras={competitor["breed"]}\n'
        competitor_output += f'reg={dogRegistration}\n'
        competitor_output += f'sbkt={competitor["id"]}\n'

        if competitor['startNumber'] != None and competitor['startNumber'] > 0:
            competitor_output += f'startnummer={competitor["startNumber"]}\n'
        
        competitor_output += '\n'

        print (f'Skriver ekipage {competitor["dogName"]} till fil...')

        writehandle.writelines(competitor_output)
        return index + 1
    except:
        print(f"Ett oväntat fel infräffade vid hantering av ekipage. Skippar...")
        return index


def fetch_handler(handler_id):
    try:
        url = f"https://brukshundklubben.se/api/get_registrationDetails?membercareUserId={handler_id}"
        response = requests.get(url)
        
        data = json.loads(json.loads(response.text))
    except:
        data = json.loads('{"email": "NONE", "handlerName": "NONE"}')
    return data

def fetch_skk(dogRegistration):
    try:
        payload = {
            'txtRegnr': dogRegistration,
            'txtIDnummer': '',
            'txtChipnr': '',
            'txtHundnamn': '',
            'ddlRasIn': '',
            'ddlKon': '',
            'txtLicensnr': '',
        }
            
        response = requests.post('https://hundar.skk.se/hunddata/Hund_sok.aspx/HundData', json=payload)
        data = json.loads(response.text)
    except:
        data = json.loads('{"d": [{"chipnr": "000000000000000", "Kon": "T"}]')
    
    return data

def get_officials(data, writehandle):
    writehandle.writelines('[funktionärer]\n')
    for i, r in enumerate(data['referees']):
        writehandle.writelines(f'domare{i+1}={r["name"]};;;;;;;0;0;1\n')
    
    for i, tl in enumerate(data['leaders']):
        writehandle.writelines(f'tl{i+1}={tl["name"]};;;;;;;0;0;1\n')
    
    for i, ts in enumerate(data['writers']):
        writehandle.writelines(f'ts{i+1}={ts["name"]};;;;;;;0;0;1\n')
    
    writehandle.writelines('\n')

def get_competiton(data, writehandle, class_ids):
    writehandle.writelines(f'[tävling]\n')
    writehandle.writelines(f'arrangör={data["organizers"][0]["name"]}\n')
    writehandle.writelines(f'arrangörskod=0\n')
    writehandle.writelines(f'datum={data["startDate"].split("T")[0].replace("-", "")}\n')
    writehandle.writelines(f'klasser={get_classlist(data, class_ids)}\n')
    writehandle.writelines(f'kommentar={data["name"]}\n')
    writehandle.writelines(f'sbkt={data["id"]}\n')
    
    if data['leaders'] != []:
        writehandle.writelines(f'tl=1\n')
    
    if data['writers'] != []:
        writehandle.writelines(f'ts=1\n')

    writehandle.writelines(f'version=2.0(875)\n')
    writehandle.writelines('\n')

def get_classlist(data, class_ids):
    classes = data['classes']
    classlist = ""
    
    for c in classes:
        identifier = c['classItem']['identifier']
        classlist += f"{class_ids[identifier]};"
    
    return classlist.strip(';')


if __name__ == '__main__':
    main(sys.argv[1])
