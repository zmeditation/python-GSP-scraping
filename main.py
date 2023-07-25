import requests
from bs4 import BeautifulSoup
import re
import mysql.connector
import csv
import math
import random
import os

mydb = mysql.connector.connect(
    host="127.0.0.1",
    port=3305,
    user="root",
    passwd="",
    database="scrape"
)
mycursor = mydb.cursor()
state_list = {}
state_abbr_list = {}
with open('states.csv', 'r') as f:
    reader = csv.reader(f, delimiter=',')
    state_arr = [row[1] for row in reader]
    state_arr.pop(0)

with open('states.csv', 'r') as f:
    red = csv.DictReader(f)
    for d in red:
        state_list.setdefault(d['key'], d['status'])

with open('states.csv', 'r') as f:
    red = csv.DictReader(f)
    for d in red:
        state_abbr_list.setdefault(d['status'], d['key'])

phone_reg = re.compile(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})')
email_reg = re.compile(r"([\w.+-]+@[\w-]+\.[\w.-]+)")

prefix = ["Dr.", "Dr", "Mr", "Mr.", "Mrs.", "Mrs", "Ms", "Ms."]

s = requests.Session()

with open('proxy.txt') as f:
    proxy_list = [line.rstrip('\n') for line in f]


def main():
    try:
        for state in state_arr:
            proxy = random.choices(proxy_list)[0]
            table_name = "scrap_" + str(state).replace(" ", "_")
            create_tb = f"""CREATE TABLE IF NOT EXISTS `{table_name}`  (
                  `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
                  `organization_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `nonprofit_address` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `country` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `state` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `primary_full_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `primary_first_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `primary_last_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `primary_email` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `primary_phone` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `full_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `first_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `last_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `email` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `phone` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `website` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `EIN` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `ruling_year` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
                  `domain_scraped` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
                  `specific_url_scraped` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
                  PRIMARY KEY (`id`) USING BTREE
                ) ENGINE = InnoDB AUTO_INCREMENT = 101 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;"""

            mycursor.execute(create_tb)
            proxies = {"http": proxy, "https": proxy}

            HEADER = {
                "accept": "application/json, */*;q=0.8",
                "accept-encoding": "gzip, deflate",
                "accept-language": "en-US,en;q=0.9",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/92.0.4515.131 Safari/537.36",
                "x-requested-with": "XMLHttpRequest",
                "origin": "https://www.guidestar.org",
                "connection": "keep-alive"
            }
            form_data = {
                "EmailAddress": "jin.bey220@proton.me",
                "Password": "tinyTIM@2020",
                "ReturnUrl": "https://www.guidestar.org",
                "IsUpdaterUserTransfer": "False",
                "UpdateInviteId": "",
                "X-Requested-With": "XMLHttpRequest"
            }
            event_url = "https://www.guidestar.org/Account/LoginToMainsite?Length=7"
            r = s.post(event_url, headers=HEADER, data=form_data, proxies=proxies, verify=False)

            if r.status_code == 200:
                # get first page
                form_data = {
                    "CurrentPage": 1,
                    "SearchType": "org",
                    "State": state,
                    "PeopleZipRadius": "Zip Only",
                    "PeopleRevenueRangeLow": "$0",
                    "PeopleRevenueRangeHigh": "max",
                    "PeopleAssetsRangeLow": "$0",
                    "PeopleAssetsRangeHigh": "max",
                    "PCSSubjectPeople": "",
                }
                event_url = "https://www.guidestar.org/search/SubmitSearch"
                response = s.post(
                    event_url, headers=HEADER, data=form_data, proxies=proxies, verify=False
                )
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    organList = response.json()
                    organs = organList["Hits"]
                    total_hits = organList["TotalHits"]
                    if total_hits < 10000:
                        hit_range = math.ceil(total_hits / 25)
                        for organ in organs:
                            record = []
                            event_url = "https://www.guidestar.org/profile/" + organ["Ein"]
                            response = s.get(
                                event_url, headers=HEADER, proxies=proxies, verify=False
                            )
                            try:
                                if response.status_code == 200:
                                    record.append(organ["OrgName"])
                                    content = response.text
                                    soup = BeautifulSoup(content, 'html.parser')
                                    summary_content = soup.find("div", {"id": "summary"})
                                    main_addr_elem = summary_content.findAll("section", {"class": "report-section"})
                                    for addr_elem in main_addr_elem:
                                        main_header = addr_elem.find("p", {"class": "report-section-header"})
                                        if main_header is not None:
                                            if "Main address" in main_header.text:
                                                main_addr = addr_elem.findAll("p", {"class": "report-section-text"})
                                                addr = main_addr[0].text + main_addr[1].text
                                                # for main_add in main_addr:
                                                #     addr += main_add.text
                                                record.append(addr)
                                                break
                                    if len(record) == 1:
                                        record.append(None)
                                    record.append("UNITED STATES OF AMERICA")
                                    record.append(state_list[organ["State"]])
                                    contact_modal = soup.find("div", {"id": "contactModal"})
                                    all_elements = contact_modal.findAll("p")
                                    order = 0
                                    primary_elements = []
                                    second_elements = []
                                    primary_content = ""
                                    second_content = ""
                                    for elment in all_elements:
                                        if elment.has_attr('class'):
                                            if elment['class'][0] == 'report-section-header':
                                                if "Contact" == elment.text:
                                                    order = 1
                                                    continue
                                                elif "Fundraising Contact" in elment.text:
                                                    order = 2
                                                    continue
                                                else:
                                                    order = 3
                                                    continue
                                        if order == 1:
                                            primary_elements.append(elment)
                                            primary_content += elment.text
                                        elif order == 2:
                                            second_elements.append(elment)
                                            second_content += elment.text
                                    # primary contact
                                    if organ["ContactName"] is not None:
                                        record.append(organ["ContactName"])
                                        contact_names = organ["ContactName"].split()
                                        if len(contact_names) > 1:
                                            if contact_names[0] in prefix:
                                                record.append(contact_names[1])
                                            else:
                                                record.append(contact_names[0])
                                            record.append(contact_names[-1])
                                        else:
                                            record.append(None)
                                            record.append(None)
                                        record.append(organ["ContactEmail"])
                                        results = phone_reg.findall(primary_content)
                                        if len(results) == 0:
                                            record.append(None)
                                        else:
                                            record.append(
                                                "+1" + results[0].replace("(", " ").replace(")", "").replace("-", " "))
                                    else:
                                        record.append(None)
                                        record.append(None)
                                        record.append(None)
                                        record.append(None)
                                        record.append(None)

                                    # second contact
                                    if len(second_elements) != 0:
                                        if second_elements[0].text.strip() == "":
                                            record.append(second_elements[1].text.strip())
                                            contact_names = second_elements[1].text.split()
                                        else:
                                            record.append(second_elements[0].text.strip())
                                            contact_names = second_elements[0].text.split()
                                        if len(contact_names) > 1:
                                            if contact_names[0] in prefix:
                                                record.append(contact_names[1])
                                            else:
                                                record.append(contact_names[0])
                                            record.append(contact_names[-1])
                                        else:
                                            record.append(None)
                                            record.append(None)
                                        results = email_reg.findall(second_content)
                                        if len(results) == 0:
                                            record.append(None)
                                        else:
                                            record.append(results[0])
                                        results = phone_reg.findall(second_content)
                                        if len(results) == 0:
                                            record.append(None)
                                        else:
                                            record.append(
                                                "+1" + results[0].replace("(", " ").replace(")", "").replace("-", " "))
                                    else:
                                        record.append(None)
                                        record.append(None)
                                        record.append(None)
                                        record.append(None)
                                        record.append(None)
                                    website_elem = soup.find("a", {"class": "hide-print-url"}, href=True)
                                    if website_elem is None:
                                        record.append(None)
                                    else:
                                        record.append(website_elem["href"])
                                    ein = re.sub('[^0-9a-zA-Z]+', '', organ["Ein"])
                                    record.append(ein)
                                    ruling_elm = summary_content.findAll("section", {"class": "report-section"})
                                    for rule_elm in ruling_elm:
                                        rule_header = rule_elm.find("p", {"class": "report-section-header"})
                                        if rule_header is not None:
                                            if "Ruling year" in rule_header.text:
                                                ruling = rule_elm.find("p", {"class": "report-section-text"})
                                                record.append(ruling.text)
                                                break
                                    if len(record) == 16:
                                        record.append(None)
                                    record.append('{"https://www.guidestar.org"}')
                                    record.append('{"https://www.guidestar.org/profile/' + organ["Ein"] + '"}')
                                    sql = f"INSERT IGNORE into {table_name}(organization_name, nonprofit_address, country, state, primary_full_name, primary_first_name, primary_last_name, primary_email, primary_phone, full_name, first_name, last_name, email, phone, website, EIN, ruling_year, domain_scraped, specific_url_scraped) VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s)"
                                    val = (record)
                                    mycursor.execute(sql, val)
                                    mydb.commit()
                                else:
                                    pass
                            except Exception as e:
                                print(e)
                                pass

                        if hit_range > 1:
                            for page in range(2, hit_range + 1):
                                form_data = {
                                    "CurrentPage": page,
                                    "SearchType": "org",
                                    "State": state,
                                    "PeopleZipRadius": "Zip Only",
                                    "PeopleRevenueRangeLow": "$0",
                                    "PeopleRevenueRangeHigh": "max",
                                    "PeopleAssetsRangeLow": "$0",
                                    "PeopleAssetsRangeHigh": "max",
                                    "PCSSubjectPeople": "",
                                }
                                event_url = "https://www.guidestar.org/search/SubmitSearch"
                                response = s.post(
                                    event_url, headers=HEADER, data=form_data, proxies=proxies, verify=False
                                )
                                if response.status_code == 200:
                                    response.encoding = 'utf-8'
                                    organList = response.json()
                                    organs = organList["Hits"]
                                    for organ in organs:
                                        record = []
                                        event_url = "https://www.guidestar.org/profile/" + organ["Ein"]
                                        response = s.get(
                                            event_url, headers=HEADER, proxies=proxies, verify=False
                                        )
                                        try:
                                            if response.status_code == 200:
                                                record.append(organ["OrgName"])
                                                content = response.text
                                                soup = BeautifulSoup(content, 'html.parser')
                                                summary_content = soup.find("div", {"id": "summary"})
                                                main_addr_elem = summary_content.findAll("section",
                                                                                         {"class": "report-section"})
                                                for addr_elem in main_addr_elem:
                                                    main_header = addr_elem.find("p", {"class": "report-section-header"})
                                                    if main_header is not None:
                                                        if "Main address" in main_header.text:
                                                            main_addr = addr_elem.findAll("p",
                                                                                          {"class": "report-section-text"})
                                                            addr = main_addr[0].text + main_addr[1].text
                                                            # for main_add in main_addr:
                                                            #     addr += main_add.text
                                                            record.append(addr)
                                                            break
                                                if len(record) == 1:
                                                    record.append(None)
                                                record.append("UNITED STATES OF AMERICA")
                                                record.append(state_list[organ["State"]])
                                                contact_modal = soup.find("div", {"id": "contactModal"})
                                                all_elements = contact_modal.findAll("p")
                                                order = 0
                                                primary_elements = []
                                                second_elements = []
                                                primary_content = ""
                                                second_content = ""
                                                for elment in all_elements:
                                                    if elment.has_attr('class'):
                                                        if elment['class'][0] == 'report-section-header':
                                                            if "Contact" == elment.text:
                                                                order = 1
                                                                continue
                                                            elif "Fundraising Contact" in elment.text:
                                                                order = 2
                                                                continue
                                                            else:
                                                                order = 3
                                                                continue
                                                    if order == 1:
                                                        primary_elements.append(elment)
                                                        primary_content += elment.text
                                                    elif order == 2:
                                                        second_elements.append(elment)
                                                        second_content += elment.text
                                                # primary contact
                                                if organ["ContactName"] is not None:
                                                    record.append(organ["ContactName"])
                                                    contact_names = organ["ContactName"].split()
                                                    if len(contact_names) > 1:
                                                        if contact_names[0] in prefix:
                                                            record.append(contact_names[1])
                                                        else:
                                                            record.append(contact_names[0])
                                                        record.append(contact_names[-1])
                                                    else:
                                                        record.append(None)
                                                        record.append(None)
                                                    record.append(organ["ContactEmail"])
                                                    results = phone_reg.findall(primary_content)
                                                    if len(results) == 0:
                                                        record.append(None)
                                                    else:
                                                        record.append(
                                                            "+1" + results[0].replace("(", " ").replace(")", "").replace(
                                                                "-", " "))
                                                else:
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)

                                                # second contact
                                                if len(second_elements) != 0:
                                                    if second_elements[0].text.strip() == "":
                                                        record.append(second_elements[1].text.strip())
                                                        contact_names = second_elements[1].text.split()
                                                    else:
                                                        record.append(second_elements[0].text.strip())
                                                        contact_names = second_elements[0].text.split()
                                                    if len(contact_names) > 1:
                                                        if contact_names[0] in prefix:
                                                            record.append(contact_names[1])
                                                        else:
                                                            record.append(contact_names[0])
                                                        record.append(contact_names[-1])
                                                    else:
                                                        record.append(None)
                                                        record.append(None)
                                                    results = email_reg.findall(second_content)
                                                    if len(results) == 0:
                                                        record.append(None)
                                                    else:
                                                        record.append(results[0])
                                                    results = phone_reg.findall(second_content)
                                                    if len(results) == 0:
                                                        record.append(None)
                                                    else:
                                                        record.append(
                                                            "+1" + results[0].replace("(", " ").replace(")", "").replace(
                                                                "-", " "))
                                                else:
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                website_elem = soup.find("a", {"class": "hide-print-url"}, href=True)
                                                if website_elem is None:
                                                    record.append(None)
                                                else:
                                                    record.append(website_elem["href"])
                                                ein = re.sub('[^0-9a-zA-Z]+', '', organ["Ein"])
                                                record.append(ein)
                                                ruling_elm = summary_content.findAll("section", {"class": "report-section"})
                                                for rule_elm in ruling_elm:
                                                    rule_header = rule_elm.find("p", {"class": "report-section-header"})
                                                    if rule_header is not None:
                                                        if "Ruling year" in rule_header.text:
                                                            ruling = rule_elm.find("p", {"class": "report-section-text"})
                                                            record.append(ruling.text)
                                                            break
                                                if len(record) == 16:
                                                    record.append(None)
                                                record.append('{"https://www.guidestar.org"}')
                                                record.append('{"https://www.guidestar.org/profile/' + organ["Ein"] + '"}')
                                                sql = f"INSERT IGNORE into {table_name}(organization_name, nonprofit_address, country, state, primary_full_name, primary_first_name, primary_last_name, primary_email, primary_phone, full_name, first_name, last_name, email, phone, website, EIN, ruling_year, domain_scraped, specific_url_scraped) VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s)"
                                                val = (record)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                            else:
                                                pass
                                        except Exception as e:
                                            print(e)
                                            pass
                    else:
                        state_abbr = state_abbr_list[state]
                        file_path = f"./section/{state_abbr}.txt"
                        if os.path.isfile(file_path):
                            with open(file_path) as fp:
                                city_list = fp.readlines()
                            for city in city_list:
                                form_data = {
                                    "CurrentPage": 1,
                                    "SearchType": "org",
                                    "State": state,
                                    "PeopleZipRadius": "Zip Only",
                                    "PeopleRevenueRangeLow": "$0",
                                    "PeopleRevenueRangeHigh": "max",
                                    "PeopleAssetsRangeLow": "$0",
                                    "PeopleAssetsRangeHigh": "max",
                                    "PCSSubjectPeople": "",
                                    "CityNav": city,
                                    "SelectedCityNav[]": city
                                }
                                event_url = "https://www.guidestar.org/search/SubmitSearch"
                                response = s.post(
                                    event_url, headers=HEADER, data=form_data, proxies=proxies, verify=False
                                )
                                if response.status_code == 200:
                                    response.encoding = 'utf-8'
                                    organList = response.json()
                                    organs = organList["Hits"]
                                    total_hits = organList["TotalHits"]
                                    hit_range = math.ceil(total_hits / 25)
                                    for organ in organs:
                                        record = []
                                        event_url = "https://www.guidestar.org/profile/" + organ["Ein"]
                                        response = s.get(
                                            event_url, headers=HEADER, proxies=proxies, verify=False
                                        )
                                        try:
                                            if response.status_code == 200:
                                                record.append(organ["OrgName"])
                                                content = response.text
                                                soup = BeautifulSoup(content, 'html.parser')
                                                summary_content = soup.find("div", {"id": "summary"})
                                                main_addr_elem = summary_content.findAll("section",
                                                                                         {"class": "report-section"})
                                                for addr_elem in main_addr_elem:
                                                    main_header = addr_elem.find("p", {"class": "report-section-header"})
                                                    if main_header is not None:
                                                        if "Main address" in main_header.text:
                                                            main_addr = addr_elem.findAll("p",
                                                                                          {"class": "report-section-text"})
                                                            addr = main_addr[0].text + main_addr[1].text
                                                            # for main_add in main_addr:
                                                            #     addr += main_add.text
                                                            record.append(addr)
                                                            break
                                                if len(record) == 1:
                                                    record.append(None)
                                                record.append("UNITED STATES OF AMERICA")
                                                record.append(state_list[organ["State"]])
                                                contact_modal = soup.find("div", {"id": "contactModal"})
                                                all_elements = contact_modal.findAll("p")
                                                order = 0
                                                primary_elements = []
                                                second_elements = []
                                                primary_content = ""
                                                second_content = ""
                                                for elment in all_elements:
                                                    if elment.has_attr('class'):
                                                        if elment['class'][0] == 'report-section-header':
                                                            if "Contact" == elment.text:
                                                                order = 1
                                                                continue
                                                            elif "Fundraising Contact" in elment.text:
                                                                order = 2
                                                                continue
                                                            else:
                                                                order = 3
                                                                continue
                                                    if order == 1:
                                                        primary_elements.append(elment)
                                                        primary_content += elment.text
                                                    elif order == 2:
                                                        second_elements.append(elment)
                                                        second_content += elment.text
                                                # primary contact
                                                if organ["ContactName"] is not None:
                                                    record.append(organ["ContactName"])
                                                    contact_names = organ["ContactName"].split()
                                                    if len(contact_names) > 1:
                                                        if contact_names[0] in prefix:
                                                            record.append(contact_names[1])
                                                        else:
                                                            record.append(contact_names[0])
                                                        record.append(contact_names[-1])
                                                    else:
                                                        record.append(None)
                                                        record.append(None)
                                                    record.append(organ["ContactEmail"])
                                                    results = phone_reg.findall(primary_content)
                                                    if len(results) == 0:
                                                        record.append(None)
                                                    else:
                                                        record.append(
                                                            "+1" + results[0].replace("(", " ").replace(")", "").replace(
                                                                "-", " "))
                                                else:
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)

                                                # second contact
                                                if len(second_elements) != 0:
                                                    if second_elements[0].text.strip() == "":
                                                        record.append(second_elements[1].text.strip())
                                                        contact_names = second_elements[1].text.split()
                                                    else:
                                                        record.append(second_elements[0].text.strip())
                                                        contact_names = second_elements[0].text.split()
                                                    if len(contact_names) > 1:
                                                        if contact_names[0] in prefix:
                                                            record.append(contact_names[1])
                                                        else:
                                                            record.append(contact_names[0])
                                                        record.append(contact_names[-1])
                                                    else:
                                                        record.append(None)
                                                        record.append(None)
                                                    results = email_reg.findall(second_content)
                                                    if len(results) == 0:
                                                        record.append(None)
                                                    else:
                                                        record.append(results[0])
                                                    results = phone_reg.findall(second_content)
                                                    if len(results) == 0:
                                                        record.append(None)
                                                    else:
                                                        record.append(
                                                            "+1" + results[0].replace("(", " ").replace(")", "").replace(
                                                                "-", " "))
                                                else:
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                    record.append(None)
                                                website_elem = soup.find("a", {"class": "hide-print-url"}, href=True)
                                                if website_elem is None:
                                                    record.append(None)
                                                else:
                                                    record.append(website_elem["href"])
                                                ein = re.sub('[^0-9a-zA-Z]+', '', organ["Ein"])
                                                record.append(ein)
                                                ruling_elm = summary_content.findAll("section", {"class": "report-section"})
                                                for rule_elm in ruling_elm:
                                                    rule_header = rule_elm.find("p", {"class": "report-section-header"})
                                                    if rule_header is not None:
                                                        if "Ruling year" in rule_header.text:
                                                            ruling = rule_elm.find("p", {"class": "report-section-text"})
                                                            record.append(ruling.text)
                                                            break
                                                if len(record) == 16:
                                                    record.append(None)
                                                record.append('{"https://www.guidestar.org"}')
                                                record.append('{"https://www.guidestar.org/profile/' + organ["Ein"] + '"}')
                                                sql = f"INSERT IGNORE into {table_name}(organization_name, nonprofit_address, country, state, primary_full_name, primary_first_name, primary_last_name, primary_email, primary_phone, full_name, first_name, last_name, email, phone, website, EIN, ruling_year, domain_scraped, specific_url_scraped) VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s)"
                                                val = (record)
                                                mycursor.execute(sql, val)
                                                mydb.commit()
                                            else:
                                                pass
                                        except Exception as e:
                                            print(e)
                                            pass

                                    if hit_range > 1:
                                        for page in range(2, hit_range + 1):
                                            form_data = {
                                                "CurrentPage": page,
                                                "SearchType": "org",
                                                "State": state,
                                                "PeopleZipRadius": "Zip Only",
                                                "PeopleRevenueRangeLow": "$0",
                                                "PeopleRevenueRangeHigh": "max",
                                                "PeopleAssetsRangeLow": "$0",
                                                "PeopleAssetsRangeHigh": "max",
                                                "PCSSubjectPeople": "",
                                                "CityNav": city,
                                                "SelectedCityNav[]": city
                                            }
                                            event_url = "https://www.guidestar.org/search/SubmitSearch"
                                            response = s.post(
                                                event_url, headers=HEADER, data=form_data, proxies=proxies, verify=False
                                            )
                                            if response.status_code == 200:
                                                response.encoding = 'utf-8'
                                                organList = response.json()
                                                organs = organList["Hits"]
                                                for organ in organs:
                                                    record = []
                                                    event_url = "https://www.guidestar.org/profile/" + organ["Ein"]
                                                    response = s.get(
                                                        event_url, headers=HEADER, proxies=proxies, verify=False
                                                    )
                                                    try:
                                                        if response.status_code == 200:
                                                            record.append(organ["OrgName"])
                                                            content = response.text
                                                            soup = BeautifulSoup(content, 'html.parser')
                                                            summary_content = soup.find("div", {"id": "summary"})
                                                            main_addr_elem = summary_content.findAll("section", {
                                                                "class": "report-section"})
                                                            for addr_elem in main_addr_elem:
                                                                main_header = addr_elem.find("p", {
                                                                    "class": "report-section-header"})
                                                                if main_header is not None:
                                                                    if "Main address" in main_header.text:
                                                                        main_addr = addr_elem.findAll("p", {
                                                                            "class": "report-section-text"})
                                                                        addr = main_addr[0].text + main_addr[1].text
                                                                        # for main_add in main_addr:
                                                                        #     addr += main_add.text
                                                                        record.append(addr)
                                                                        break
                                                            if len(record) == 1:
                                                                record.append(None)
                                                            record.append("UNITED STATES OF AMERICA")
                                                            record.append(state_list[organ["State"]])
                                                            contact_modal = soup.find("div", {"id": "contactModal"})
                                                            all_elements = contact_modal.findAll("p")
                                                            order = 0
                                                            primary_elements = []
                                                            second_elements = []
                                                            primary_content = ""
                                                            second_content = ""
                                                            for elment in all_elements:
                                                                if elment.has_attr('class'):
                                                                    if elment['class'][0] == 'report-section-header':
                                                                        if "Contact" == elment.text:
                                                                            order = 1
                                                                            continue
                                                                        elif "Fundraising Contact" in elment.text:
                                                                            order = 2
                                                                            continue
                                                                        else:
                                                                            order = 3
                                                                            continue
                                                                if order == 1:
                                                                    primary_elements.append(elment)
                                                                    primary_content += elment.text
                                                                elif order == 2:
                                                                    second_elements.append(elment)
                                                                    second_content += elment.text
                                                            # primary contact
                                                            if organ["ContactName"] is not None:
                                                                record.append(organ["ContactName"])
                                                                contact_names = organ["ContactName"].split()
                                                                if len(contact_names) > 1:
                                                                    if contact_names[0] in prefix:
                                                                        record.append(contact_names[1])
                                                                    else:
                                                                        record.append(contact_names[0])
                                                                    record.append(contact_names[-1])
                                                                else:
                                                                    record.append(None)
                                                                    record.append(None)
                                                                record.append(organ["ContactEmail"])
                                                                results = phone_reg.findall(primary_content)
                                                                if len(results) == 0:
                                                                    record.append(None)
                                                                else:
                                                                    record.append(
                                                                        "+1" + results[0].replace("(", " ").replace(")",
                                                                                                                    "").replace(
                                                                            "-", " "))
                                                            else:
                                                                record.append(None)
                                                                record.append(None)
                                                                record.append(None)
                                                                record.append(None)
                                                                record.append(None)

                                                            # second contact
                                                            if len(second_elements) != 0:
                                                                if second_elements[0].text.strip() == "":
                                                                    record.append(second_elements[1].text.strip())
                                                                    contact_names = second_elements[1].text.split()
                                                                else:
                                                                    record.append(second_elements[0].text.strip())
                                                                    contact_names = second_elements[0].text.split()
                                                                if len(contact_names) > 1:
                                                                    if contact_names[0] in prefix:
                                                                        record.append(contact_names[1])
                                                                    else:
                                                                        record.append(contact_names[0])
                                                                    record.append(contact_names[-1])
                                                                else:
                                                                    record.append(None)
                                                                    record.append(None)
                                                                results = email_reg.findall(second_content)
                                                                if len(results) == 0:
                                                                    record.append(None)
                                                                else:
                                                                    record.append(results[0])
                                                                results = phone_reg.findall(second_content)
                                                                if len(results) == 0:
                                                                    record.append(None)
                                                                else:
                                                                    record.append(
                                                                        "+1" + results[0].replace("(", " ").replace(")",
                                                                                                                    "").replace(
                                                                            "-", " "))
                                                            else:
                                                                record.append(None)
                                                                record.append(None)
                                                                record.append(None)
                                                                record.append(None)
                                                                record.append(None)
                                                            website_elem = soup.find("a", {"class": "hide-print-url"},
                                                                                     href=True)
                                                            if website_elem is None:
                                                                record.append(None)
                                                            else:
                                                                record.append(website_elem["href"])
                                                            ein = re.sub('[^0-9a-zA-Z]+', '', organ["Ein"])
                                                            record.append(ein)
                                                            ruling_elm = summary_content.findAll("section", {
                                                                "class": "report-section"})
                                                            for rule_elm in ruling_elm:
                                                                rule_header = rule_elm.find("p", {
                                                                    "class": "report-section-header"})
                                                                if rule_header is not None:
                                                                    if "Ruling year" in rule_header.text:
                                                                        ruling = rule_elm.find("p", {
                                                                            "class": "report-section-text"})
                                                                        record.append(ruling.text)
                                                                        break
                                                            if len(record) == 16:
                                                                record.append(None)
                                                            record.append('{"https://www.guidestar.org"}')
                                                            record.append('{"https://www.guidestar.org/profile/' + organ[
                                                                "Ein"] + '"}')
                                                            sql = f"INSERT IGNORE into {table_name}(organization_name, nonprofit_address, country, state, primary_full_name, primary_first_name, primary_last_name, primary_email, primary_phone, full_name, first_name, last_name, email, phone, website, EIN, ruling_year, domain_scraped, specific_url_scraped) VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s)"
                                                            val = (record)
                                                            mycursor.execute(sql, val)
                                                            mydb.commit()
                                                        else:
                                                            pass
                                                    except Exception as e:
                                                        print(e)
                                                        pass
                        else:
                            print(f"doesn't exist file : {state}.txt")
            else:
                print("Login is failed")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
