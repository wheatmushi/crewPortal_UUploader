import csv
import os
import requests
import json
import getpass
import re
from time import localtime, strftime


email_RE = '[^@]+@[^@]+\.[^@]+'
url_general = 'https://services-fv.crewplatform.aero/'

def authentication():
    login = input('\nenter your login as "firstname.lastname" (with or without domain)\n')
    password = getpass.getpass('\nenter your password\n')
    print('\nopening session...')

    if not re.match(email_RE, login):
        login = login + '@sita.aero'

    url_login = url_general + 'j_spring_security_check'
    url_admin = url_general + 'CrewServices/adminConsole/adminData'

    ssl = 'certs_rossiya.pem'

    headers = {'j_username': login, 'j_password': password}

    session = requests.Session()
    p = session.post(url_login, headers, verify=ssl)

    if 'login_error=1' in p.url:
        print('\nincorrect login or password, try again!')
        return authentication()

    session.cookies.update({'username': login})

    admin = session.get(url_admin)
    admin = json.loads(admin.content)
    key = admin['airlines'][0]['key']

    session.headers.update({'X-apiKey': key})
    print('\nsession loaded successfully')
    return {'session': session, 'login': login}


def csv_parser(csv_file):  # parse .csv file and return its data in 2D list (first list contains headers)
    csvfile = open(os.path.join('source', csv_file), 'r', encoding='utf-8')
    delimiter = csv.Sniffer().sniff(csvfile.read()).delimiter
    csvfile.seek(0)
    reader = csv.reader(csvfile, delimiter=delimiter)
    return list(reader)


def packer(userlist):
    # [ [head1,head2], [f1h1,f1h2], [f2h1,f2h2] ] -> { head1 : [f1h1,f2h1], head2 : [f1h2,f2h2] }
    # search data in table and return in dict with corresponding keys
    head = [field.casefold() for field in userlist[0]]
    data = userlist[1:]
    head_order = {field: n for n, field in enumerate(head)}
    form = {field: [] for field in head}

    for field in form.keys():
        for user in data:
            form[field].append(user[head_order[field]])

    template, user_data = ['staffid', 'last name', 'first name', 'password', 'email', 'position'], {}

    for field in form.keys():
        for name in template:
            if name in field:
                user_data[name] = form[field]
    return user_data


def get_user(nb, table):
    return {field: table[field][nb] for field in table}


def approving(handler, csvpath, user_table):
    print("\n{} users (few users displayed below as examples) from table '{}'?".format(handler, csvpath))
    head = ['staff ID','First name','Last name','Password','Email','Position']
    print('\n{0:>12}{1:>15}{2:>20}{3:>12}{4:>30}{5:>12}'.format(*head))
    for i in range(min(3, len(user_table))):
            print('{0:>12}{1:>15}{2:>20}{3:>12}{4:>30}{5:>12}'.format(*user_table[i].show()))
    h = ''
    while h not in ('y','Y','n','N'):
        print('\nY/N?')
        h = input()
    return True if h in ('Y','y') else False


def filler(s):
    return 'no' if s == '' else s


def reporting(users, csvpath, handler, login):  # create log report for user creation
    err_response = 0
    err_verify = 0
    report_list = []

    datetime = strftime("%Y-%b-%d  %H-%M-%S", localtime())
    report_path = 'USR ' + handler + ' ' + datetime + '.txt'

    for u in users:
        num = u.num
        response = filler(u.response)
        verify = filler(u.verify)
        creation = filler(u.creation_status)

        if '"success":true' not in response:
            err_response += 1
            report = 'ERROR WITH USER no.{0:>2}\n' \
                     'Source data error: {1}\n' \
                     'DB check error:    {2}\n' \
                     'Response:          {3}'.format(str(num), creation, verify, response)
            if verify != '':
                err_verify += 1
            print('\n' + report)
            report_list.append('\n' + report + '\n')

        else:
            report = 'User no.{0:>2} OK\n' \
                     'Source data error: {1}\n' \
                     'DB check error:    {2}\n' \
                     'Response:          {3}'.format(str(num), creation, verify, response)
            report_list.append('\n' + report + '\n')

    stats = 'users in table: {0:>5}\n' \
            'number of reports: {1:>2}\n' \
            '{2} errors: {3:>6}\n' \
            'checking errors: {4:>4}'.format(str(len(users)), str(len(report_list)), handler, err_response, err_verify)

    if err_response == 0:
        print("\nusers creation finished successfully\n"
              "check log in '" + report_path + "'\n")
    else:
        print("\nERROR: number of users in csv-table might differs from number of users added/deleted\n"
              "check log in '" + report_path + "'\n")

    print(stats)
    report_file = open(os.path.join('reports', report_path), 'w', encoding='utf-8')
    head = 'Source file: {0}\nLogin:       {1}\nOperation:   {2}'.format(csvpath, login, handler)
    report_file.write(head)
    report_file.write('\n\n' + stats + '\n')
    for report in report_list:
        report_file.write(report)
    report_file.close()
