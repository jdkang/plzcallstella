#!/bin/env python3

import datetime
import pathlib
import shutil
import requests
import json
import xlsxwriter
from bs4 import BeautifulSoup
from sty import fg, bg, ef, rs
import re

from pprint import pprint

MAX_PARTICIPANTS_TO_PROCESS = -1
FILE_TS = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
SCRIPT_DIR = pathlib.Path(__file__).parent
OUTPUT_DIR = pathlib.Path.joinpath(SCRIPT_DIR, f"output/{FILE_TS}")
OUTPUT_RECORDINGS_DIR = pathlib.Path.joinpath(OUTPUT_DIR, 'recordings')
OUTPUT_TRANSCRIPTIONS_DIR = pathlib.Path.joinpath(OUTPUT_DIR, 'transcriptions')
OUTPUT_JSON_DIR = pathlib.Path.joinpath(OUTPUT_DIR, 'json')
BASE_URL = 'http://accent.gmu.edu'

def download_details(participant: dict):
    file_id_fmt = '{:010}'
    file_id = file_id_fmt.format(participant['id'])
    print(f"  {fg.green}partcipant id:{participant['id']} key:{participant['key']}")

    # recording
    for audio_url in participant['details']['audio_files']:
        audio_ext = audio_url.split('/')[-1].split('.')[-1]
        audio_filename = f"{file_id}.{audio_ext}"
        audio_file = pathlib.Path.joinpath(OUTPUT_RECORDINGS_DIR, audio_filename)
        print(f"  {fg.grey}[audio] {fg.green}src: {fg.yellow}{audio_url}{fg.rs}")
        print(f"  {fg.grey}[audio] {fg.green}dest: {fg.yellow}{audio_file}{fg.rs}")
        with requests.get(audio_url, stream=True) as req:
            with open(audio_file, 'wb') as audio_f:
                shutil.copyfileobj(req.raw, audio_f)

    # transcription
    for ipa_url in participant['details']['ipa_transcripts']:
        ipa_ext = ipa_url.split('/')[-1].split('.')[-1]
        ipa_filename = f"{file_id}.{ipa_ext}"
        ipa_file = pathlib.Path.joinpath(OUTPUT_TRANSCRIPTIONS_DIR, ipa_filename)
        print(f"  {fg.grey}[ipa] {fg.green}src: {fg.yellow}{ipa_url}{fg.rs}")
        print(f"  {fg.grey}[ipa] {fg.green}dest {fg.yellow}{ipa_file}{fg.rs}")
        with requests.get(ipa_url, stream=True) as req:
            with open(ipa_file, 'wb') as ipa_f:
                shutil.copyfileobj(req.raw, ipa_f)

    # json
    json_filename = f"{file_id}.json"
    json_file = pathlib.Path.joinpath(OUTPUT_JSON_DIR, json_filename)
    print(f"  {fg.grey}[json] {fg.green}saving {fg.yellow}{json_file}{fg.rs}")
    json_str = json.dumps(participant)
    json_file.write_text(json_str)

def get_lang_participants(lan: str):
    ret = []
    url = f"{BASE_URL}/browse_language.php?function=find&language={str.lower(lan)}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    profile_id_regex = re.compile(r'speakerid=(\d+)($|&)')
    for c in soup.find_all('div',attrs={ 'class':'content' }):
        for p in c.find_all('p'):
            if match := profile_id_regex.search(p.a['href']):
                id = match.group(1)
                desc = p.get_text()
                desc_parts = str.split(desc, ',')

                sex = 'unknown'
                city = 'unknown'
                country = 'unknown'
                if len(desc_parts) > 1:
                    sex = str.strip(desc_parts[1])
                if len(desc_parts) > 2:
                    city = str.strip(desc_parts[2])
                if len(desc_parts) > 3:
                    country = str.strip(desc_parts[3])

                participant = {
                    'id':int(id),
                    'key':str.strip(desc_parts[0]),
                    'language':lan,
                    'sex':sex,
                    'city':city,
                    'country':country,
                    'link':BASE_URL + '/' + p.a['href'],
                    'details':{}
                }
                ret.append(participant)
    return ret
            

def get_participant_details(id: int):
    ret = {
        'audio_files': [],
        'ipa_transcripts': []
    }
    url = f"{BASE_URL}/browse_language.php?function=detail&speakerid={id}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    # audio files
    for audio in soup.find_all('audio'):
        for source in audio.find_all('source'):
            ret['audio_files'].append(f"{BASE_URL}{source['src']}")

    # transcript
    for transcript in soup.find_all('div', attrs={ 'id':"transcript" }):
        for img in transcript.find_all('img', attrs={ 'alt':'ipa transcript' }):
            ret['ipa_transcripts'].append(f"{BASE_URL}{img['src']}")

    return ret

def get_language_list():
    ret = []
    url = f"{BASE_URL}/browse_language.php"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')

    for lang_list in soup.find_all('ul',attrs={ 'class':'languagelist' }):
        for li in lang_list.find_all('li'):
            lang_item = {
                'language':li.a.get_text(),
                'link':f"{BASE_URL}/{li.a['href']}"
            }
            ret.append(lang_item)
    return ret

def main():
    # Ensure output dirs
    OUTPUT_RECORDINGS_DIR.mkdir(parents=True,exist_ok=True)
    OUTPUT_TRANSCRIPTIONS_DIR.mkdir(parents=True,exist_ok=True)
    OUTPUT_JSON_DIR.mkdir(parents=True,exist_ok=True)
    
    # create .xlsx manifest
    participants_workbook_file = pathlib.Path.joinpath(OUTPUT_DIR, 'participants.xlsx')
    participants_manifest_workbook = xlsxwriter.Workbook(participants_workbook_file)
    bold = participants_manifest_workbook.add_format({'bold': True})
    participants_worksheet = participants_manifest_workbook.add_worksheet('participants')
    participants_worksheet.write(0, 0, 'id', bold)
    participants_worksheet.write(0, 1, 'key', bold)
    participants_worksheet.write(0, 2, 'language', bold)
    participants_worksheet.write(0, 3, 'sex', bold)
    participants_worksheet.write(0, 4, 'city', bold)
    participants_worksheet.write(0, 5, 'country', bold)
    participants_worksheet.write(0, 6, 'link', bold)

    # get all languages
    language_list = get_language_list()
    print(f"{fg.cyan}language count: {fg.yellow}{len(language_list)}{fg.rs}")

    # get each language particiapnts
    total_partcipants = 0
    try:
        for lan in language_list:
            print(f"{fg.cyan}fetching language {fg.yellow}{lan['language']}{fg.rs}")
            participants = get_lang_participants(lan['language'])
            for count, participant in enumerate(participants):
                total_partcipants += 1

                # get and append detaILS
                details = get_participant_details(participant['id'])
                participant['details'].update(details)
                
                # print progress
                print(f"{fg.green}[{lan['language']}:{count+1}/{len(participants)}] {fg.da_yellow}{participant['key']} {fg.yellow}{participant['id']} {fg.rs}")

                # write spreadsheet entry
                row = total_partcipants
                print(f"  {fg.grey}[xlsx] {fg.cyan}writing row {fg.yellow}{row}{fg.rs}")
                participants_worksheet.write(row, 0, participant['id'])
                participants_worksheet.write(row, 1, participant['key'])
                participants_worksheet.write(row, 2, participant['language'])
                participants_worksheet.write(row, 3, participant['sex'])
                participants_worksheet.write(row, 4, participant['city'])
                participants_worksheet.write(row, 5, participant['country'])
                participants_worksheet.write(row, 6, participant['link'])

                #pprint(participant)

                # download details files
                download_details(participant)

                if MAX_PARTICIPANTS_TO_PROCESS > 0 and total_partcipants >= MAX_PARTICIPANTS_TO_PROCESS:
                    break
            if MAX_PARTICIPANTS_TO_PROCESS > 0 and total_partcipants >= MAX_PARTICIPANTS_TO_PROCESS:
                break
    finally:
        participants_manifest_workbook.close()

if __name__ == '__main__':
    main()