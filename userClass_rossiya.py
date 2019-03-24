import re
import requests
import json

email_RE = '[^@]+@[^@]+\.[^@]+'
email_RE_tmp = 'fv_+[^@]+@tempmail.net'


class User:  # creation/deletion user methods and checking data routine while __init__

    creation_status = ''
    response = ''
    verify = ''

    def __init__(self, handler, user_num, data):
        self.num = user_num
        self.data = data

        for field in ['staffid', 'first name', 'last name']:
            if field not in self.data.keys() or data[field] == '':
                self.data[field] = ''
                self.creation_status += '  /no ' + field + ' in table'

        if 'position' not in self.data.keys():
            self.data['position'] = 'CC'
        if not self.data['staffid'].isdigit():
            self.creation_status += '  /incorrect staffid'
        #  if not re.match(email_RE, self.data['email']):
        #    self.creation_status += '  /incorrect email'

        self.data['email'] = 'fv_' + self.data['staffid'] + '@tempmail.net'
        self.data['password'] = 'fv#' + self.data['staffid']

        #if ('password' not in self.data.keys()) or (self.data['password'].casefold() in ('su', '')):
        #    self.data['password'] = 'su'

        #self.data['first name'] = self.data['first name'].split(' ')[0].capitalize()
        #self.data['last name'] = self.data['last name'].split(' ')[0].capitalize()

        name = self.data['last name'].split()
        self.data['last name'] = name[0]
        self.data['first name'] = ' '.join(name[1:])

        if handler == 'delete' and 'staffid' not in self.response:
            self.creation_status = ''

    def show(self):
            return (self.data['staffid'], self.data['first name'], self.data['last name'],
                    self.data['password'], self.data['email'], self.data['position'])

    def get_post_data(self):
        jstr = '{{"staffId":"{staffid}","username":"{email}","position":"{position}","phone":"","password":"{password}",' \
               '"firstName":"{first name}","lastName":"{last name}","email":"{email}","enabled":true}}'
        return jstr.format(**self.data)

    def get_verify_status(self):
        return True if self.verify == '' else False

    def is_equal(self, user_inf):
        if (self.data['staffid'] != user_inf['staffId'] or
            self.data['email'] != user_inf['email'] or
            self.data['first name'] != user_inf['firstName'] or
            self.data['last name'] != user_inf['lastName']):
            return False
        elif (user_inf['mustChangePassword'] == 'true' or
            user_inf['enabled'] == 'true' or
            user_inf['credentialsNonExpired'] == 'true' or
            user_inf['accountNonLocked'] == 'true' or
            user_inf['accountNonExpired'] == 'true'):
            return False
        else:
            return True

    def check(self, session):
        url_check = 'https://services-fv.crewplatform.aero/CrewServices/crewManager/v1/SU/'
        try:
            check_by_email = session.get(url_check + self.data['email'])
            check_by_stfid = session.get(url_check + self.data['staffid'])
            resp_email = json.loads(check_by_email.content)
            resp_stfid = json.loads(check_by_stfid.content)
        except requests.exceptions.RequestException as exception:
            resp_check = exception
            self.response = self.verify = str(resp_check)
            return 0

        if resp_email['numberOfUsers'] > 0 and resp_email['airlineUsers'][0]['username'] == self.data['email']:
            self.verify += ' /user already exist with this email'
            email_data = resp_email['airlineUsers'][0]
            if not self.is_equal(email_data):
                resp_user = '  [staff ID: {staffId}, email: {email}, first name: {firstName}, last name: {lastName},' \
                            ' enabled: {enabled}]  '.format(**email_data)
                self.verify += ' but with different data:' + resp_user
            else:
                self.verify += ' and same data'
        if resp_stfid['numberOfUsers'] > 0 and resp_stfid['airlineUsers'][0]['staffId'] == self.data['staffid']:
            self.verify += ' /user already exist with this ID'
            stfid_data = resp_stfid['airlineUsers'][0]
            if not self.is_equal(stfid_data):
                resp_user = '  [staff ID: {staffId}, email: {email}, first name: {firstName}, last name: {lastName},' \
                            ' enabled: {enabled}]  '.format(**stfid_data)
                self.verify += ' but with different data:' + resp_user
            else:
                self.verify += ' and same data'

    def create(self, session):
        url_upl = 'https://services-fv.crewplatform.aero/CrewServices/crewManager/user/SU'
        print('creating user No.{}'.format(self.num))
        if self.creation_status == '':
            try:
                p = session.post(url_upl, self.get_post_data().encode('utf-8'))
                resp = p.content
            except requests.exceptions.RequestException as exception:
                resp = exception
            if type(resp) == bytes:
                self.response = resp.decode('utf-8')
            else:
                self.response = str(resp)

    def delete(self, session):
        url = 'https://services-fv.crewplatform.aero/CrewServices/crewManager/delete/SU/'
        print('deleting user No.{}'.format(self.num))
        if self.creation_status == '':
            url_del = url + str(self.data['staffid'])
            try:
                p = session.get(url_del)
                resp = p.content
            except requests.exceptions.RequestException as exception:
                resp = exception
            if type(resp) == bytes:
                self.response = resp.decode('utf-8')
            else:
                self.response = str(resp)

    def delete_tmp(self, session):
        url = 'https://services-fv.crewplatform.aero/CrewServices/crewManager/delete/SU/'
        url_check = 'https://services-fv.crewplatform.aero/CrewServices/crewManager/v1/SU/'

        print('{:>4} deleting staffid {:>6}'.format(self.num, self.data['staffid']))
        check_by_stfid = session.get(url_check + self.data['staffid'])
        resp_stfid = json.loads(check_by_stfid.content)
        resp_stfid = [u for u in resp_stfid['airlineUsers'] if self.data['staffid'] == u['staffId'] and re.match(email_RE_tmp, u['username'])]

        if resp_stfid:
            url_del = url + str(self.data['staffid'])
            try:
                p = session.get(url_del)
                resp = p.content
                print('{:>4} deleting staffid {:>6}  OK'.format(self.num, self.data['staffid']))
            except requests.exceptions.RequestException as exception:
                resp = exception
            if type(resp) == bytes:
                self.response = resp.decode('utf-8')
            else:
                self.response = str(resp)
