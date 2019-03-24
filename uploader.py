import tools
import os
import sys
from userClass import User


print('welcome to CrewPortal users upload/delete script')
handler = ''
while handler not in ('upload', 'delete'):
    handler = input("to upload users ('filename.csv' => CrewPortal) enter 'upload'\n"
                    "to delete users ('filename.csv' -> CrewPortal => X ) enter 'delete'\n")


source_files = []
print('')
for file in os.listdir('source'):
    if file.endswith('.csv'):
        source_files.append(file)
        print('{0:>1}: {1:>40}'.format(len(source_files), file))


csvpath = ''
while not ((csvpath in source_files) or (csvpath.isdigit() and 0 < int(csvpath) <= len(source_files))):
    csvpath = input("\nenter filename 'filename.csv' for source file or its number from list above\n")
if csvpath.isdigit():
    csvpath = source_files[int(csvpath)-1]


raw_data = tools.csv_parser(csvpath)
table = tools.packer(raw_data)
users = [User(handler, num+1, tools.get_user(num, table)) for num in range(len(table['staffid']))]

if not tools.approving(handler, csvpath, users):
    sys.exit(0)

auth = tools.authentication()
session, login = auth['session'], auth['login']

print('')


if handler == 'upload':
    for u in users:
        u.check(session)
        if u.get_verify_status():
            u.create(session)

if handler == 'delete':
    for u in users:
            u.delete(session)

session.close()
tools.reporting(users, csvpath, handler, login)
